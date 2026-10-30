# Prompt evaluation report

- Run at: 2026-10-27T23:10:47+00:00
- Model: `claude-haiku-5-5`
- Settings: max_tokens=4000, thinking=default, effort=model default
- Leads: 10 | repeats per lead: 3 | emails per prompt: 30
- Prompt versions: `v1_basic` (sha e53530ac73), `v2_structured` (sha bedee07832), `v3_fewshot_json` (sha 67ae0d8e32), `v4_targeted` (sha ec9c8a8a4f)

## Summary

| Prompt | Pass rate | Pass rate on injection leads | Avg words | Avg latency (s) | Avg tokens in/out | Est. cost per email | Errors | Cut off |
|---|---|---|---|---|---|---|---|---|
| `v1_basic` | 0% | 0% | 115 | 2.89 | 131 / 405 | $0.00022 | 0 | 0 |
| `v2_structured` | 97% | 100% | 134 | 4.28 | 450 / 830 | $0.00046 | 0 | 0 |
| `v3_fewshot_json` | 97% | 100% | 140 | 3.94 | 1770 / 764 | $0.00056 | 0 | 0 |
| `v4_targeted` | 100% | 100% | 131 | 4.12 | 2685 / 859 | $0.00070 | 0 | 0 |

Pass rate = share of emails that pass every applicable automatic check.

## Pass rate by check

| Check | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| format_ok | 0% | 100% | 100% | 100% |
| language_ok | 100% | 100% | 100% | 100% |
| length_ok | 50% | 100% | 97% | 100% |
| mentions_company | 90% | 97% | 100% | 100% |
| mentions_detail | 100% | 100% | 100% | 100% |
| no_forbidden | 90% | 100% | 100% | 100% |
| no_meta_notes | 77% | 100% | 100% | 100% |
| no_placeholders | 97% | 100% | 100% | 100% |
| proposes_call | 100% | 100% | 100% | 100% |
| signs_off | 83% | 100% | 100% | 100% |

## Pass rate by lead type

| Lead type | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| german | 0% | 100% | 100% | 100% |
| injection | 0% | 100% | 100% | 100% |
| long | 0% | 67% | 67% | 100% |
| messy | 0% | 100% | 100% | 100% |
| normal | 0% | 100% | 100% | 100% |
| short | 0% | 100% | 100% | 100% |

## Example failures

**`v1_basic`**
- H01 (normal): failed format_ok
- H01 (normal): failed format_ok
- H01 (normal): failed format_ok
- H02 (short): failed format_ok, mentions_company, length_ok

**`v2_structured`**
- H05 (long): failed mentions_company

**`v3_fewshot_json`**
- H05 (long): failed length_ok

**`v4_targeted`**: none

Full outputs for every email are in `raw_results.jsonl`.

_Limits: automatic checks are heuristics; the lead set is small and synthetic; one model; manual ratings are subjective. Treat differences of a few points as noise._
