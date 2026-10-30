import csv
import json

from openpyxl import load_workbook

from prompt_eval.harness import main
from prompt_eval.prompts import ALL_PROMPTS

N = len(ALL_PROMPTS)


def _dry_run(tmp_path, *extra):
    assert main(["run", "--dry-run", "--out", str(tmp_path), *extra]) == 0
    return tmp_path / "dry_run"


def test_dry_run_writes_all_outputs_and_flags_itself(tmp_path):
    out = _dry_run(tmp_path, "--limit", "8", "--rating-sample", "3")
    for name in ("raw_results.jsonl", "meta.json", "report.md", "manual_rating_sheet.xlsx", "manual_rating_key.json"):
        assert (out / name).exists(), name
    assert "DRY RUN" in (out / "report.md").read_text(encoding="utf-8")
    rows = [json.loads(l) for l in (out / "raw_results.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 8 * N
    assert json.loads((out / "meta.json").read_text(encoding="utf-8"))["dry_run"] is True


def test_small_run_with_the_default_sample_size_does_not_crash(tmp_path):
    out = _dry_run(tmp_path, "--limit", "4")  # fewer leads than the default sample of 10
    ws = load_workbook(out / "manual_rating_sheet.xlsx").worksheets[0]
    assert ws.max_row == 1 + 4 * N


def test_rating_sheet_is_readable_and_blind(tmp_path):
    out = _dry_run(tmp_path, "--limit", "6", "--rating-sample", "2")
    wb = load_workbook(out / "manual_rating_sheet.xlsx")
    assert wb.sheetnames == ["Rate emails", "How to rate"]
    ws = wb["Rate emails"]
    assert [c.value for c in ws[1]] == ["Blind ID", "Lead", "Email to rate", "Your rating (1-5)"]
    assert ws.max_row == 1 + 2 * N
    assert ws.freeze_panes == "A2"
    for r in range(2, ws.max_row + 1):
        assert ws.cell(r, 3).alignment.wrap_text and ws.row_dimensions[r].height >= 48
        assert ws.cell(r, 3).value and "v1_basic" not in str(ws.cell(r, 3).value)  # nothing reveals the prompt
    ids = [ws.cell(r, 1).value for r in range(2, ws.max_row + 1)]
    assert ids == sorted(ids)


def test_manual_ratings_are_joined_back_to_prompts(tmp_path):
    out = _dry_run(tmp_path, "--limit", "6", "--rating-sample", "2")
    sheet = out / "manual_rating_sheet.xlsx"
    wb = load_workbook(sheet)
    ws = wb["Rate emails"]
    for r in range(2, ws.max_row + 1):
        ws.cell(r, 4).value = 4
    ws.cell(2, 4).value = 9  # out of range, must be ignored
    wb.save(sheet)
    assert main(["report", "--dir", str(out)]) == 0
    report = (out / "report.md").read_text(encoding="utf-8")
    assert "Manual ratings" in report and "4.00" in report


def test_old_semicolon_csv_ratings_still_work(tmp_path):
    out = _dry_run(tmp_path, "--limit", "6", "--rating-sample", "2")
    key = json.loads((out / "manual_rating_key.json").read_text(encoding="utf-8"))
    (out / "manual_rating_sheet.xlsx").unlink()
    with open(out / "manual_rating_sheet.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["blind_id", "lead_name", "lead_company", "lead_message", "email", "rating"])
        for bid in key:
            w.writerow([bid, "x", "y", "z", "line one\nline two", "3,0"])
    main(["report", "--dir", str(out)])
    assert "Manual ratings" in (out / "report.md").read_text(encoding="utf-8")


def test_rating_sheet_command_rebuilds_the_same_blind_ids(tmp_path):
    out = _dry_run(tmp_path, "--limit", "10", "--rating-sample", "4")
    key_before = (out / "manual_rating_key.json").read_text(encoding="utf-8")
    (out / "manual_rating_sheet.xlsx").unlink()
    assert main(["rating-sheet", "--dir", str(out), "--sample", "4"]) == 0
    assert (out / "manual_rating_sheet.xlsx").exists()
    assert (out / "manual_rating_key.json").read_text(encoding="utf-8") == key_before


def test_rescore_repairs_stale_results_without_api_calls(tmp_path):
    out = _dry_run(tmp_path, "--limit", "6")
    raw = out / "raw_results.jsonl"
    rows = [json.loads(l) for l in raw.read_text(encoding="utf-8").splitlines()]
    good = [r["passed"] for r in rows]
    outputs = [r["output_raw"] for r in rows]
    for r in rows:
        r["passed"] = not r["passed"]  # simulate results from an older, different set of checks
    raw.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    assert main(["rescore", "--dir", str(out)]) == 0
    fixed = [json.loads(l) for l in raw.read_text(encoding="utf-8").splitlines()]
    assert [r["passed"] for r in fixed] == good
    assert [r["output_raw"] for r in fixed] == outputs  # outputs untouched


def test_real_run_without_key_fails_cleanly(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert main(["run", "--out", str(tmp_path)]) == 2


class _Block:
    type = "text"

    def __init__(self, text):
        self.text = text


class _Usage:
    input_tokens = 11
    output_tokens = 22


class _Resp:
    def __init__(self, text, stop_reason="end_turn"):
        self.content = [_Block(text)]
        self.usage = _Usage()
        self.stop_reason = stop_reason


class _StubClient:
    """Records the kwargs the harness sends, so the real-call path is tested without a network."""

    def __init__(self):
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _Resp("ok")


def test_call_model_builds_the_request_correctly():
    from prompt_eval.harness import call_model
    from prompt_eval.prompts import ALL_PROMPTS

    lead = {"name": "A B", "company": "Acme", "message": "Hello"}
    stub = _StubClient()
    text, latency, tin, tout, stop = call_model(stub, "some-model", ALL_PROMPTS["v1_basic"], lead, None)
    assert (text, tin, tout, stop) == ("ok", 11, 22, "end_turn") and latency >= 0
    first = stub.calls[0]
    assert first["model"] == "some-model" and "system" not in first
    assert "temperature" not in first and "extra_body" not in first
    assert first["max_tokens"] == 700
    assert "Acme" in first["messages"][0]["content"]

    call_model(stub, "some-model", ALL_PROMPTS["v2_structured"], lead, 0.0)
    second = stub.calls[1]
    assert "system" in second
    assert "temperature" not in second  # the SDK has no typed temperature argument
    assert second["extra_body"] == {"temperature": 0.0}


def test_preflight_failure_stops_the_run_before_anything_is_written(tmp_path, monkeypatch):
    import prompt_eval.harness as h

    def boom(*args, **kwargs):
        raise RuntimeError("401 invalid x-api-key")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy")
    monkeypatch.setattr(h, "call_model", boom)
    assert main(["run", "--out", str(tmp_path), "--limit", "2"]) == 1
    assert not (tmp_path / "raw_results.jsonl").exists()


def test_report_warns_loudly_when_calls_failed():
    from prompt_eval.report import render_report

    meta = {"run_at": "now", "model": "m", "temperature": None, "n_leads": 1, "repeats": 1, "dry_run": False,
            "prompt_ids": ["v1_basic"], "prompt_sha": {"v1_basic": "abc"}, "price_in": None, "price_out": None}
    row = {"lead_id": "L01", "tags": ["normal"], "prompt_id": "v1_basic", "repeat": 0, "error": "AuthenticationError: bad key",
           "checks": {}, "passed": False, "words": None, "latency_s": None, "input_tokens": None, "output_tokens": None}
    assert "1 of 1 API calls failed" in render_report(meta, [row])


def test_thinking_effort_and_max_tokens_are_passed_through():
    from prompt_eval.harness import call_model
    from prompt_eval.prompts import ALL_PROMPTS

    lead = {"name": "A B", "company": "Acme", "message": "Hello"}
    stub = _StubClient()
    call_model(stub, "m", ALL_PROMPTS["v2_structured"], lead, None, max_tokens=4000, thinking="disabled", effort="low")
    sent = stub.calls[0]
    assert sent["max_tokens"] == 4000
    assert sent["extra_body"] == {"thinking": {"type": "disabled"}, "output_config": {"effort": "low"}}
    assert "temperature" not in sent
    # "default" thinking must not send anything
    call_model(stub, "m", ALL_PROMPTS["v2_structured"], lead, None, thinking="default")
    assert "extra_body" not in stub.calls[1]


def test_report_flags_replies_that_were_cut_off():
    from prompt_eval.report import render_report

    meta = {"run_at": "now", "model": "m", "temperature": None, "n_leads": 1, "repeats": 1, "dry_run": False,
            "prompt_ids": ["v1_basic"], "prompt_sha": {"v1_basic": "abc"}, "price_in": None, "price_out": None,
            "max_tokens": 700, "thinking": "default", "effort": None}
    row = {"lead_id": "L01", "tags": ["normal"], "prompt_id": "v1_basic", "repeat": 0, "error": None,
           "checks": {"length_ok": False}, "passed": False, "words": 40, "latency_s": 2.0,
           "input_tokens": 100, "output_tokens": 700, "stop_reason": "max_tokens"}
    text = render_report(meta, [row])
    assert "cut off" in text and "| Cut off |" in text
    assert "max_tokens=700, thinking=default" in text


def test_dry_run_report_has_the_cut_off_column(tmp_path):
    out = _dry_run(tmp_path, "--limit", "3")
    assert "| Cut off |" in (out / "report.md").read_text(encoding="utf-8")
