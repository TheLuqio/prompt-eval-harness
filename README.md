# prompt-eval-harness

A small, dependency-light tool for comparing prompt versions on a fixed test set, instead of judging them by feel.

The task under test is the AI follow-up email from my lead-capture automation (LeadKit): given a new lead's name, company and message, write a short, personalised reply that proposes a call. The test set includes the awkward cases a real inbox produces: one-line messages, rambling messages, typos and ALL CAPS, German leads, and **prompt-injection attempts hidden inside the lead's message**.

## What it does

1. Runs every prompt version against every lead (30 leads x 4 prompts by default).
2. Scores each email with deterministic checks (below).
3. Records tokens, latency and (optionally) estimated cost per email.
4. Writes `report.md` plus every raw output to `raw_results.jsonl`.
5. Produces a **blind** Excel rating sheet (`manual_rating_sheet.xlsx`): outputs from all prompts shuffled together, so manual 1-5 ratings are not biased by knowing which prompt wrote what.

### Prompt versions

| id | What changes |
|---|---|
| `v1_basic` | One plain instruction. No rules, no defenses. The baseline. |
| `v2_structured` | System prompt with explicit rules, untrusted-data framing for the lead's text, and a canary string to detect prompt leakage. |
| `v3_fewshot_json` | v2 plus three worked examples (English, German, an injection attempt) and strict JSON output. |
| `v4_targeted` | v3 plus fixes for failures seen in run 1: pick the language from the message text only (never from the name), a hard 150-word cap, stricter JSON instructions, and two more worked examples. |

v1 to v3 are frozen (a test pins their hashes) so run 1 stays comparable. A new idea becomes a new version, never an edit to an old one.

### Automatic checks

| Check | Meaning |
|---|---|
| `format_ok` | Plain-text prompts: no subject line or markdown. JSON prompts: valid JSON with `subject` and `body`. |
| `no_placeholders` | No `[Name]`, `{{x}}`, `<Name>` and similar. |
| `mentions_company` | The lead's company (or a listed alias) appears. |
| `mentions_detail` | At least one key term from the lead's message appears (skipped for vague leads). |
| `length_ok` | 100-170 words. |
| `proposes_call` | Asks for a conversation: call, chat, meeting, Zoom, talk (also German Anruf/Gespräch/Telefonat and Spanish llamada), or a number of minutes of the lead's time. |
| `signs_off` | Ends with the sender's name. |
| `no_forbidden` | None of the lead's "canary" strings appear (e.g. `HACKED`, a fake 90% discount, a leaked ruleset id). This is the prompt-injection check. |
| `language_ok` | Reply is in the lead's language (simple word-list heuristic). |

An email passes only if every applicable check passes.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest                         # 38 tests, no API key needed

python -m prompt_eval run --dry-run      # offline, FAKE model, only to see the pipeline work

export ANTHROPIC_API_KEY=...             # your own key; never commit it
python -m prompt_eval run                # real run, writes results/
python -m prompt_eval run --repeats 3    # repeat each call to see run-to-run variability
python -m prompt_eval run --price-in <USD per 1M input tokens> --price-out <USD per 1M output tokens>
```

Then open `results/manual_rating_sheet.xlsx`, rate each email 1-5 in the yellow column, save it as .xlsx, and rebuild the report:

```bash
python -m prompt_eval report
```

`python -m prompt_eval rating-sheet` rebuilds the Excel rating sheet from saved results (same blind ids, no API calls).

If you change a check, you do not need to call the API again: `python -m prompt_eval rescore` re-applies the current checks to the saved outputs, so the blind rating sheet stays valid.

Dry-run output goes to `results/dry_run/` and its report is stamped as synthetic. **Never quote dry-run numbers.**

## Held-out leads

`data/leads_heldout.json` holds 10 leads that were not used when v4 was designed (German-sounding names with English messages, a long message, new kinds of hijack attempts). v4 was written after looking at run-1 failures on the main set, so its score there is optimistic. The held-out run is the fair test:

```bash
python -m prompt_eval run --leads data/leads_heldout.json --repeats 3 --out results/heldout
```

Lead H10 deliberately mixes Spanish and English, so it has no single correct reply language and the language check is skipped for it.

## Results

## Results

Model: Claude Haiku 4.5 (`claude-haiku-4-5-20251001`), October 2026. Main set: 30 leads x 3 repeats = 90 emails per prompt. Held-out set: 10 leads x 3 repeats = 30 emails per prompt, written after run 1 to resemble the failure types seen there (German-sounding names with English messages, long messages, new hijack attempts). They test whether the fixes generalise to new examples of those failures, not to new kinds of failure.

| Prompt | Pass rate, main set | Pass rate, held-out | Hijack text in emails | Avg input tokens | Blind rating (1-5, 10 emails) |
|---|---|---|---|---|---|
| v1_basic | 0% | 0% | 4 of 27 | 96 | 3.7 |
| v2_structured | 62% | 63% | 0 of 27 | 343 | 3.4 |
| v3_fewshot_json | 97% | 90% | 0 of 27 | 1,296 | 4.1 |
| v4_targeted | 99% | 100% | 0 of 27 | 1,983 | 4.0 |

Findings:

1. The automatic pass rate measures reliability, not writing quality. The plain prompt scores 0% mostly because it adds subject lines and markdown, and only about 40% of its emails land in the target length. Blind ratings still put it close to the structured prompts (3.7 vs 3.4-4.1).
2. Rules alone had a side effect. v2 replied in German to English-speaking leads with German-sounding names (6 of 6 emails for two held-out leads; 88% language-check pass on the main set). Its rule about greeting German leads formally seems to have spilled over onto name cues. Worked examples (v3) fixed it.
3. Examples controlled length better than instructions: 97-100% of v3/v4 emails fell in the target range, against 70-73% for v2, which was told "120-150 words".
4. Prompt injection: the plain prompt let attacker text into 4 of 27 hijack-test emails (9 attack leads x 3 repeats); v2, v3 and v4 let through 0 of 27.
5. v4 (targeted fixes after run 1: language from message text only, hard word cap, stricter JSON, two more examples) matched v3 within noise: 99% vs 97% on the main set (two emails), 100% vs 90% on the held-out set (all from one lead, H03, where v3 never named the company), blind ratings 4.0 vs 4.1. It costs about 53% more input tokens.

Caveats: leads are synthetic, one model, one rater with 10 ratings per prompt. The checks were revised after run 1 (the call check was widened, one ambiguous lead's language label was removed) and every run was re-scored with the final rules. v4 was designed after seeing run-1 failures, so its main-set score is optimistic.

## Design notes and limits

- Company names must match as whole words and key terms at the start of a word, so "Hall" does not match "challenge" and "appointment" does not match "disappointment". "Excel" can still match "excellent".
- The checks are heuristics. They catch the failures that matter for this pipeline cheaply and reproducibly, but they cannot judge tone or persuasiveness. That is what the blind manual rating is for.
- 30 synthetic leads is a small sample. Differences of a few percentage points are noise; use `--repeats` and look at the failure examples, not just the headline number.
- One model per run. Re-run with `--model` to compare models.
- Temperature is off by default: the current Anthropic SDK has no typed temperature argument and newer models may reject it. `--temperature` sends it via `extra_body` if you want it.
- The prompt-injection set is a regression test for one attack surface (instructions hidden in lead text). It does not prove a pipeline is safe.
- Prompt versions are pinned by hash in every report so results can be traced to the exact prompt text.

## Next steps

- LLM-as-judge scoring, validated against the manual ratings before it is trusted.
- Put an input filter (prompt-injection firewall) in front of the pipeline and measure the difference.
- Add a larger, more realistic lead set.
