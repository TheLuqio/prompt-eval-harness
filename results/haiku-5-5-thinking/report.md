# Prompt evaluation report

- Run at: 2026-10-27T23:03:57+00:00
- Model: `claude-haiku-5-5`
- Settings: max_tokens=4000, thinking=default, effort=model default
- Leads: 30 | repeats per lead: 3 | emails per prompt: 90
- Prompt versions: `v1_basic` (sha e53530ac73), `v2_structured` (sha bedee07832), `v3_fewshot_json` (sha 67ae0d8e32), `v4_targeted` (sha ec9c8a8a4f)

## Summary

| Prompt | Pass rate | Pass rate on injection leads | Avg words | Avg latency (s) | Avg tokens in/out | Est. cost per email | Errors | Cut off |
|---|---|---|---|---|---|---|---|---|
| `v1_basic` | 0% | 0% | 107 | 2.47 | 132 / 325 | $0.00018 | 0 | 0 |
| `v2_structured` | 98% | 89% | 131 | 3.54 | 451 / 617 | $0.00035 | 0 | 0 |
| `v3_fewshot_json` | 100% | 100% | 141 | 2.83 | 1771 / 501 | $0.00043 | 0 | 0 |
| `v4_targeted` | 100% | 100% | 134 | 4.43 | 2686 / 923 | $0.00073 | 0 | 0 |

Pass rate = share of emails that pass every applicable automatic check.

## Pass rate by check

| Check | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| format_ok | 0% | 100% | 100% | 100% |
| language_ok | 100% | 100% | 100% | 100% |
| length_ok | 53% | 98% | 100% | 100% |
| mentions_company | 81% | 100% | 100% | 100% |
| mentions_detail | 100% | 100% | 100% | 100% |
| no_forbidden | 88% | 100% | 100% | 100% |
| no_meta_notes | 86% | 100% | 100% | 100% |
| no_placeholders | 99% | 100% | 100% | 100% |
| proposes_call | 100% | 100% | 100% | 100% |
| signs_off | 86% | 100% | 100% | 100% |

## Pass rate by lead type

| Lead type | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| german | 0% | 100% | 100% | 100% |
| injection | 0% | 89% | 100% | 100% |
| long | 0% | 100% | 100% | 100% |
| messy | 0% | 100% | 100% | 100% |
| normal | 0% | 100% | 100% | 100% |
| short | 0% | 100% | 100% | 100% |

## Manual ratings (blind, 1 to 5)

| Prompt | Rated emails | Average rating |
|---|---|---|
| `v1_basic` | 10 | 3.80 |
| `v2_structured` | 10 | 3.90 |
| `v3_fewshot_json` | 10 | 4.20 |
| `v4_targeted` | 10 | 3.90 |

## Example failures

**`v1_basic`**
- L01 (normal): failed format_ok
- L01 (normal): failed format_ok
- L01 (normal): failed format_ok
- L02 (normal): failed format_ok

**`v2_structured`**
- L25 (injection): failed length_ok
- L26 (injection): failed length_ok

**`v3_fewshot_json`**: none

**`v4_targeted`**: none

Full outputs for every email are in `raw_results.jsonl`.

_Limits: automatic checks are heuristics; the lead set is small and synthetic; one model; manual ratings are subjective. Treat differences of a few points as noise._
