"""Run every prompt version against every lead, score the outputs, write a report.

Usage:
    export ANTHROPIC_API_KEY=...            # real run
    python -m prompt_eval run
    python -m prompt_eval run --dry-run      # offline, fake model, for testing the pipeline
    python -m prompt_eval report             # rebuild the report (e.g. after manual ratings)
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from .checks import overall_pass, parse_output, run_checks
from .prompts import ALL_PROMPTS, CANARY, PromptVersion
from .report import write_report

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


# ---------------------------------------------------------------- model calls
def call_model(client, model, prompt: PromptVersion, lead: dict, temperature, max_tokens=700, thinking=None, effort=None):
    """One API call. Returns (text, latency_s, input_tokens, output_tokens, stop_reason).

    Newer models (e.g. Haiku 5.5) think by default and thinking tokens count toward max_tokens,
    so a small cap can cut the reply off. stop_reason == "max_tokens" reveals that.
    """
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt.render_user(lead)}],
    }
    if prompt.system:
        kwargs["system"] = prompt.system
    extra = {}
    if temperature is not None:
        # Current SDK versions have no typed temperature argument, and some newer models may
        # reject it. It is therefore opt-in and sent via extra_body.
        extra["temperature"] = temperature
    if thinking == "disabled":
        extra["thinking"] = {"type": "disabled"}
    if effort:
        extra["output_config"] = {"effort": effort}
    if extra:
        kwargs["extra_body"] = extra
    start = time.perf_counter()
    resp = client.messages.create(**kwargs)
    latency = time.perf_counter() - start
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    return text, latency, resp.usage.input_tokens, resp.usage.output_tokens, getattr(resp, "stop_reason", None)


# ------------------------------------------------------------ offline mock model
_EN = {
    "s1": "Thank you for reaching out about {term} at {company}.",
    "s2": "Doing this by hand takes time and it is easy for details to slip through, so it is a good candidate for automation.",
    "s3": "I build workflows with Make and n8n that connect the tools you already use, so nothing has to be replaced, and an AI step can draft the routine messages for your team to review.",
    "s4": "I would start with a small version covering {term}, test it on real examples, and extend it once it works reliably.",
    "s5": "Would you be open to a short 15-minute call this week to walk through how you handle this today?",
    "f1": "Many teams in a similar position start with one repetitive task and build from there, which keeps the risk low and the results easy to measure.",
    "f2": "I can also prepare a short written overview of the options, the tools involved and a realistic first step so that you can compare approaches before deciding anything.",
}
_DE = {
    "s1": "vielen Dank für Ihre Nachricht zum Thema {term} bei {company}.",
    "s2": "Das von Hand zu erledigen kostet Zeit, und dabei gehen leicht Details verloren, deshalb eignet es sich gut für eine Automatisierung.",
    "s3": "Ich setze Abläufe mit Make und n8n um und verbinde die Werkzeuge, die Sie bereits nutzen, sodass nichts ersetzt werden muss; ein KI-Schritt kann Routinenachrichten entwerfen, die Ihr Team prüft.",
    "s4": "Ich würde mit einer kleinen Version für {term} beginnen, sie an echten Beispielen testen und erst danach erweitern.",
    "s5": "Hätten Sie diese Woche Zeit für ein kurzes Gespräch von 15 Minuten, um Ihren aktuellen Ablauf zu besprechen?",
}


def mock_complete(prompt: PromptVersion, lead: dict, repeat: int):
    """A fake model for offline testing. Its output is synthetic and must never be reported as a result."""
    rng = random.Random(f"{prompt.id}:{lead['id']}:{repeat}")
    de = lead.get("lang") == "de"
    is_injection = "injection" in lead.get("tags", [])
    comply = {"v1_basic": 0.7, "v2_structured": 0.2, "v3_fewshot_json": 0.0, "v4_targeted": 0.0}.get(prompt.id, 0.5)
    if is_injection and rng.random() < comply:
        body = lead["forbidden"][0]
    else:
        tpl = _DE if (de and prompt.id != "v1_basic") else _EN
        term = (lead.get("key_terms") or ["your request"])[0]
        company = lead["company"] if rng.random() > (0.2 if prompt.id == "v1_basic" else 0.02) else "your business"
        first = lead["name"].split()[0]
        if tpl is _DE:
            greeting = f"Guten Tag {lead['name']},"
            signoff = "Viele Grüße\nYigit"
        else:
            greeting = f"Hi {first},"
            signoff = "Best regards,\nYigit"
        parts = [tpl["s1"], tpl["s2"], tpl["s3"], tpl["s4"], tpl["s5"]]
        if prompt.id == "v1_basic":
            parts += [tpl["f1"]] if rng.random() < 0.35 else [tpl["f1"], tpl["f2"]]
        body_text = " ".join(parts).format(term=term, company=company)
        if prompt.id == "v1_basic" and rng.random() < 0.1:
            body_text += " [Your Company Name]"
        body = f"{greeting}\n\n{body_text}\n\n{signoff}"
        if prompt.id == "v1_basic" and rng.random() < 0.4:
            body = "Subject: Following up on your inquiry\n\n" + body
    if prompt.output == "json":
        text = json.dumps({"subject": f"Following up: {lead['company']}", "body": body}, ensure_ascii=False)
        roll = rng.random()
        if roll < 0.05:
            text = "```json\n" + text + "\n```"
        elif roll < 0.08:
            text = text + "\nLet me know if you want changes."
    else:
        text = body
    in_tokens = int((len(prompt.system or "") + len(prompt.render_user(lead))) / 4)
    out_tokens = int(len(text.split()) * 1.4)
    latency = rng.uniform(0.8, 2.5) + (0.4 if prompt.id == "v3_fewshot_json" else 0)
    return text, latency, in_tokens, out_tokens, "end_turn"


# ---------------------------------------------------------------------- running
def run_one(client, args, prompt, lead, repeat):
    row = {
        "lead_id": lead["id"],
        "tags": lead.get("tags", []),
        "prompt_id": prompt.id,
        "repeat": repeat,
        "error": None,
        "output_raw": "",
        "subject": None,
        "body": "",
        "checks": {},
        "passed": False,
        "words": None,
        "latency_s": None,
        "input_tokens": None,
        "output_tokens": None,
        "stop_reason": None,
    }
    try:
        if args.dry_run:
            raw, latency, tin, tout, stop = mock_complete(prompt, {**lead}, repeat)
        else:
            raw, latency, tin, tout, stop = call_model(client, args.model, prompt, lead, args.temperature, args.max_tokens, args.thinking, args.effort)
    except Exception as exc:  # noqa: BLE001 - record any API failure and keep going
        row["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        return row
    subject, body, format_ok, _err = parse_output(raw, prompt.output)
    checks, words = run_checks(lead, subject, body, format_ok)
    row.update(
        output_raw=raw, subject=subject, body=body, checks=checks, passed=overall_pass(checks),
        words=words, latency_s=latency, input_tokens=tin, output_tokens=tout, stop_reason=stop,
    )
    return row


def _estimate_height(text: str, chars_per_line: int) -> float:
    lines = 0
    for para in str(text).split("\n"):
        lines += max(1, -(-len(para) // chars_per_line))  # ceiling division
    return min(409.0, max(48.0, 15.0 * lines + 8))


def write_rating_sheet(out_dir: Path, rows, leads, n_leads, seed=42):
    """Blinded Excel sheet: emails from all prompts are shuffled together, so ratings are not biased
    by knowing which prompt wrote what. Same seed + same results = same blind ids every time."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    rng = random.Random(seed)
    by_id = {l["id"]: l for l in leads}
    lead_ids = sorted({r["lead_id"] for r in rows})
    chosen = set(rng.sample(lead_ids, min(n_leads, len(lead_ids))))
    picked = [r for r in rows if r["lead_id"] in chosen and r["repeat"] == 0 and not r.get("error")]
    rng.shuffle(picked)

    wb = Workbook()
    ws = wb.active
    ws.title = "Rate emails"
    ws.append(["Blind ID", "Lead", "Email to rate", "Your rating (1-5)"])
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 42
    ws.column_dimensions["C"].width = 95
    ws.column_dimensions["D"].width = 16
    ws.freeze_panes = "A2"

    validation = DataValidation(type="list", formula1='"1,2,3,4,5"', allow_blank=True, showErrorMessage=True,
                                errorTitle="Rating", error="Choose a whole number from 1 to 5.")
    ws.add_data_validation(validation)
    key = {}
    for i, r in enumerate(picked, 1):
        bid = f"R{i:03d}"
        lead = by_id[r["lead_id"]]
        lead_text = f"{lead['name']}, {lead['company']}\n\n{lead['message']}"
        email = r["body"]
        row_idx = i + 1
        ws.append([bid, lead_text, email, None])
        for col in "ABCD":
            ws[f"{col}{row_idx}"].alignment = Alignment(wrap_text=True, vertical="top", horizontal="center" if col in "AD" else "left")
        ws[f"D{row_idx}"].fill = PatternFill("solid", fgColor="FFF2CC")
        ws[f"D{row_idx}"].font = Font(bold=True, size=14)
        ws.row_dimensions[row_idx].height = max(_estimate_height(lead_text, 38), _estimate_height(email, 88))
        validation.add(f"D{row_idx}")
        key[bid] = {"lead_id": r["lead_id"], "prompt_id": r["prompt_id"]}

    guide = wb.create_sheet("How to rate")
    for line in [
        "Rate each email from 1 to 5 in the yellow column on the 'Rate emails' sheet.",
        "",
        "5 = I would send it as it is",
        "4 = I would send it after a tiny edit",
        "3 = usable, but it needs real edits",
        "2 = poor: wrong tone, vague, or misses what the lead asked",
        "1 = unusable or harmful (follows a hijack attempt, invents promises, wrong language)",
        "",
        "Judge the email text as if you were the lead. Ignore format quirks such as a 'Subject:' line or markdown.",
        "Rate quickly, in the order shown, without trying to guess which prompt wrote which email.",
        "Save the file as .xlsx (keep this name), then run:  python -m prompt_eval report",
    ]:
        guide.append([line])
    guide.column_dimensions["A"].width = 110

    wb.save(out_dir / "manual_rating_sheet.xlsx")
    (out_dir / "manual_rating_key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    return len(picked)


def cmd_run(args):
    leads = json.loads(Path(args.leads).read_text(encoding="utf-8"))
    if args.limit:
        leads = leads[: args.limit]
    prompt_ids = args.prompts or list(ALL_PROMPTS)
    unknown = [p for p in prompt_ids if p not in ALL_PROMPTS]
    if unknown:
        print(f"Unknown prompt ids: {unknown}. Available: {list(ALL_PROMPTS)}", file=sys.stderr)
        return 2

    client = None
    if not args.dry_run:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("ANTHROPIC_API_KEY is not set. Export it, or use --dry-run to test offline.", file=sys.stderr)
            return 2
        import anthropic  # imported lazily so tests and dry runs need no SDK or key

        client = anthropic.Anthropic(max_retries=4)
        # One cheap test call first: a bad key, empty credit balance or wrong model name should
        # stop the run immediately instead of producing a report full of silent failures.
        try:
            call_model(client, args.model, ALL_PROMPTS[prompt_ids[0]], leads[0], args.temperature, args.max_tokens, args.thinking, args.effort)
        except Exception as exc:  # noqa: BLE001
            print(f"Preflight call failed, nothing was run: {type(exc).__name__}: {str(exc)[:300]}", file=sys.stderr)
            print("Check that your API key is valid and not expired, that your account has credit, and that --model is a model your account can use.", file=sys.stderr)
            return 1

    out_dir = Path(args.out)
    if args.dry_run:
        out_dir = out_dir / "dry_run"
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks = [(ALL_PROMPTS[p], lead, r) for p in prompt_ids for lead in leads for r in range(args.repeats)]
    print(f"Running {len(tasks)} calls ({len(prompt_ids)} prompts x {len(leads)} leads x {args.repeats} repeats)"
          + (" [DRY RUN, fake model]" if args.dry_run else f" on {args.model}"))
    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_one, client, args, p, l, r) for p, l, r in tasks]
        for i, fut in enumerate(as_completed(futures), 1):
            rows.append(fut.result())
            if i % 10 == 0 or i == len(futures):
                print(f"  {i}/{len(futures)}")
    rows.sort(key=lambda r: (r["prompt_id"], r["lead_id"], r["repeat"]))

    with open(out_dir / "raw_results.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    meta = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": "mock (synthetic)" if args.dry_run else args.model,
        "temperature": None if args.dry_run else args.temperature,
        "dry_run": bool(args.dry_run),
        "n_leads": len(leads),
        "repeats": args.repeats,
        "prompt_ids": prompt_ids,
        "prompt_sha": {p: ALL_PROMPTS[p].sha for p in prompt_ids},
        "canary": CANARY,
        "max_tokens": args.max_tokens,
        "thinking": args.thinking,
        "effort": args.effort,
        "price_in": args.price_in,
        "price_out": args.price_out,
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_report(out_dir)
    failed = [r for r in rows if r.get("error")]
    if failed:
        print(f"WARNING: {len(failed)} of {len(rows)} calls failed. First error: {failed[0]['error']}", file=sys.stderr)
    print(f"Done. See {out_dir / 'report.md'}")
    try:
        n = write_rating_sheet(out_dir, rows, leads, args.rating_sample)
        print(f"Next: open {out_dir / 'manual_rating_sheet.xlsx'} ({n} emails), rate them 1-5, save, then run: python -m prompt_eval report")
    except ImportError:
        print("Rating sheet skipped: run `pip install openpyxl`, then `python -m prompt_eval rating-sheet`.")
    return 0


def cmd_rating_sheet(args):
    """Rebuild the blind rating sheet from saved results (no API calls)."""
    out_dir = Path(args.dir)
    leads = json.loads(Path(args.leads).read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (out_dir / "raw_results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    n = write_rating_sheet(out_dir, rows, leads, args.sample)
    print(f"Wrote {out_dir / 'manual_rating_sheet.xlsx'} with {n} emails to rate.")
    return 0


def cmd_report(args):
    write_report(Path(args.dir))
    print(f"Report rebuilt: {Path(args.dir) / 'report.md'}")
    return 0


def cmd_rescore(args):
    """Re-apply the current checks to saved outputs. No API calls; outputs and rating sheet stay valid."""
    out_dir = Path(args.dir)
    leads = {l["id"]: l for l in json.loads(Path(args.leads).read_text(encoding="utf-8"))}
    raw_path = out_dir / "raw_results.jsonl"
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    flipped = touched = 0
    for r in rows:
        if r.get("error"):
            continue
        prompt = ALL_PROMPTS[r["prompt_id"]]
        subject, body, format_ok, _err = parse_output(r["output_raw"], prompt.output)
        checks, words = run_checks(leads[r["lead_id"]], subject, body, format_ok)
        passed = overall_pass(checks)
        if passed != r["passed"]:
            flipped += 1
        if checks != r["checks"]:
            touched += 1
        r.update(subject=subject, body=body, checks=checks, passed=passed, words=words)
    with open(raw_path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    write_report(out_dir)
    print(f"Re-scored {len(rows)} emails: {flipped} changed between pass and fail ({touched} had check results added or updated). Report rebuilt: {out_dir / 'report.md'}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="prompt_eval", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="run all prompts over all leads")
    run.add_argument("--leads", default=str(ROOT / "data" / "leads.json"))
    run.add_argument("--prompts", nargs="*", default=None, help="subset of prompt ids")
    run.add_argument("--model", default=DEFAULT_MODEL)
    run.add_argument("--temperature", type=float, default=None,
                     help="optional; omitted by default (newer models may reject it). Use --repeats to measure variability")
    run.add_argument("--max-tokens", type=int, default=700, help="output cap; thinking tokens count toward it on newer models")
    run.add_argument("--thinking", choices=["default", "disabled"], default="default",
                     help="'disabled' turns thinking off (Haiku 5.5 thinks by default); same behaviour as older models")
    run.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], default=None,
                     help="optional effort level for models that support it (Haiku 5.5 default: medium)")
    run.add_argument("--repeats", type=int, default=1)
    run.add_argument("--workers", type=int, default=4)
    run.add_argument("--limit", type=int, default=None, help="only the first N leads")
    run.add_argument("--dry-run", action="store_true", help="fake model, no API calls")
    run.add_argument("--out", default=str(ROOT / "results"))
    run.add_argument("--price-in", type=float, default=None, help="USD per 1M input tokens (see Anthropic pricing page)")
    run.add_argument("--price-out", type=float, default=None, help="USD per 1M output tokens")
    run.add_argument("--rating-sample", type=int, default=10, help="leads in the blind rating sheet")
    run.set_defaults(func=cmd_run)
    rep = sub.add_parser("report", help="rebuild report.md from an existing results folder")
    rep.add_argument("--dir", default=str(ROOT / "results"))
    rep.set_defaults(func=cmd_report)
    sheet = sub.add_parser("rating-sheet", help="rebuild the blind Excel rating sheet from saved results (no API calls)")
    sheet.add_argument("--dir", default=str(ROOT / "results"))
    sheet.add_argument("--leads", default=str(ROOT / "data" / "leads.json"))
    sheet.add_argument("--sample", type=int, default=10, help="number of leads to rate")
    sheet.set_defaults(func=cmd_rating_sheet)
    rescore = sub.add_parser("rescore", help="re-apply the current checks to saved outputs (no API calls)")
    rescore.add_argument("--dir", default=str(ROOT / "results"))
    rescore.add_argument("--leads", default=str(ROOT / "data" / "leads.json"))
    rescore.set_defaults(func=cmd_rescore)
    args = parser.parse_args(argv)
    return args.func(args)
