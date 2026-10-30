# Prompt evaluation report

- Run at: 2026-10-27T22:36:19+00:00
- Model: `claude-haiku-5-5`
- Leads: 30 | repeats per lead: 3 | emails per prompt: 90
- Prompt versions: `v1_basic` (sha e53530ac73), `v2_structured` (sha bedee07832), `v3_fewshot_json` (sha 67ae0d8e32), `v4_targeted` (sha ec9c8a8a4f)

## Summary

| Prompt | Pass rate | Injection leads passed | Avg words | Avg latency (s) | Avg tokens in/out | Est. cost per email | Errors |
|---|---|---|---|---|---|---|---|
| `v1_basic` | 0% | 0% | 104 | 2.46 | 132 / 320 | $0.00017 | 0 |
| `v2_structured` | 54% | 72% | 91 | 3.12 | 451 / 451 | $0.00027 | 0 |
| `v3_fewshot_json` | 81% | 94% | 120 | 2.44 | 1771 / 374 | $0.00036 | 0 |
| `v4_targeted` | 40% | 89% | 66 | 3.32 | 2686 / 556 | $0.00055 | 0 |

Pass rate = share of emails that pass every applicable automatic check.

## Pass rate by check

| Check | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| format_ok | 0% | 80% | 81% | 40% |
| language_ok | 100% | 80% | 87% | 60% |
| length_ok | 56% | 64% | 83% | 44% |
| mentions_company | 86% | 78% | 87% | 60% |
| mentions_detail | 100% | 80% | 89% | 64% |
| no_forbidden | 91% | 100% | 100% | 100% |
| no_placeholders | 98% | 100% | 100% | 100% |
| proposes_call | 97% | 64% | 83% | 40% |
| signs_off | 86% | 57% | 81% | 40% |

## Pass rate by lead type

| Lead type | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| german | 0% | 11% | 33% | 0% |
| injection | 0% | 72% | 94% | 89% |
| long | 0% | 17% | 50% | 17% |
| messy | 0% | 56% | 89% | 44% |
| normal | 0% | 64% | 92% | 42% |
| short | 0% | 50% | 75% | 0% |

## Example failures

**`v1_basic`**
- L01 (normal): failed format_ok
- L01 (normal): failed format_ok
- L01 (normal): failed format_ok, length_ok
- L02 (normal): failed format_ok

**`v2_structured`**
- L01 (normal): failed length_ok, proposes_call, signs_off
- L01 (normal): failed format_ok, mentions_company, mentions_detail, length_ok, proposes_call, signs_off, language_ok
- L01 (normal): failed signs_off
- L02 (normal): failed length_ok

**`v3_fewshot_json`**
- L11 (normal): failed format_ok, signs_off
- L11 (normal): failed format_ok, mentions_company, mentions_detail, length_ok, proposes_call, signs_off, language_ok
- L11 (normal): failed format_ok, length_ok, proposes_call, signs_off
- L13 (short): failed format_ok, mentions_company, length_ok, proposes_call, signs_off, language_ok

**`v4_targeted`**
- L01 (normal): failed format_ok, length_ok, proposes_call, signs_off
- L01 (normal): failed format_ok, mentions_company, mentions_detail, length_ok, proposes_call, signs_off, language_ok
- L02 (normal): failed format_ok, length_ok, proposes_call, signs_off
- L03 (normal): failed format_ok, mentions_company, mentions_detail, length_ok, proposes_call, signs_off, language_ok

Full outputs for every email are in `raw_results.jsonl`.

_Limits: automatic checks are heuristics; the lead set is small and synthetic; one model; manual ratings are subjective. Treat differences of a few points as noise._
