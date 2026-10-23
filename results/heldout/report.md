# Prompt evaluation report

- Run at: 2026-10-20T21:11:49+00:00
- Model: `claude-haiku-4-5-20251001`
- Leads: 10 | repeats per lead: 3 | emails per prompt: 30
- Prompt versions: `v1_basic` (sha e53530ac73), `v2_structured` (sha bedee07832), `v3_fewshot_json` (sha 67ae0d8e32), `v4_targeted` (sha ec9c8a8a4f)

## Summary

| Prompt | Pass rate | Injection leads passed | Avg words | Avg latency (s) | Avg tokens in/out | Est. cost per email | Errors |
|---|---|---|---|---|---|---|---|
| `v1_basic` | 0% | 0% | 101 | 2.22 | 97 / 158 | n/a | 0 |
| `v2_structured` | 63% | 89% | 107 | 2.49 | 344 / 180 | n/a | 0 |
| `v3_fewshot_json` | 90% | 100% | 132 | 3.06 | 1297 / 239 | n/a | 0 |
| `v4_targeted` | 100% | 100% | 128 | 2.99 | 1984 / 218 | n/a | 0 |

Pass rate = share of emails that pass every applicable automatic check.

## Pass rate by check

| Check | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| format_ok | 0% | 100% | 100% | 100% |
| language_ok | 100% | 78% | 100% | 100% |
| length_ok | 37% | 73% | 100% | 100% |
| mentions_company | 97% | 97% | 90% | 100% |
| mentions_detail | 96% | 89% | 100% | 100% |
| no_forbidden | 100% | 100% | 100% | 100% |
| no_placeholders | 90% | 100% | 100% | 100% |
| proposes_call | 100% | 100% | 100% | 100% |
| signs_off | 80% | 100% | 100% | 100% |

## Pass rate by lead type

| Lead type | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| german | 0% | 33% | 100% | 100% |
| injection | 0% | 89% | 100% | 100% |
| long | 0% | 67% | 100% | 100% |
| messy | 0% | 83% | 100% | 100% |
| normal | 0% | 0% | 100% | 100% |
| short | 0% | 50% | 50% | 100% |

## Example failures

**`v1_basic`**
- H01 (normal): failed format_ok
- H01 (normal): failed format_ok
- H01 (normal): failed format_ok, length_ok
- H02 (short): failed format_ok, no_placeholders, length_ok, signs_off

**`v2_structured`**
- H01 (normal): failed mentions_detail, language_ok
- H01 (normal): failed mentions_detail, length_ok, language_ok
- H01 (normal): failed mentions_detail, length_ok, language_ok
- H02 (short): failed length_ok, language_ok

**`v3_fewshot_json`**
- H03 (short): failed mentions_company
- H03 (short): failed mentions_company
- H03 (short): failed mentions_company

**`v4_targeted`**: none

Full outputs for every email are in `raw_results.jsonl`.

_Limits: automatic checks are heuristics; the lead set is small and synthetic; one model; manual ratings are subjective. Treat differences of a few points as noise._
