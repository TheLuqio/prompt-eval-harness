# Prompt evaluation report

- Run at: 2026-10-27T22:39:07+00:00
- Model: `claude-haiku-5-5`
- Leads: 10 | repeats per lead: 3 | emails per prompt: 30
- Prompt versions: `v1_basic` (sha e53530ac73), `v2_structured` (sha bedee07832), `v3_fewshot_json` (sha 67ae0d8e32), `v4_targeted` (sha ec9c8a8a4f)

## Summary

| Prompt | Pass rate | Injection leads passed | Avg words | Avg latency (s) | Avg tokens in/out | Est. cost per email | Errors |
|---|---|---|---|---|---|---|---|
| `v1_basic` | 0% | 0% | 103 | 2.91 | 131 / 379 | $0.00020 | 0 |
| `v2_structured` | 30% | 56% | 62 | 3.32 | 450 / 553 | $0.00032 | 0 |
| `v3_fewshot_json` | 47% | 89% | 84 | 3.08 | 1770 / 504 | $0.00043 | 0 |
| `v4_targeted` | 33% | 89% | 66 | 3.27 | 2685 / 557 | $0.00055 | 0 |

Pass rate = share of emails that pass every applicable automatic check.

## Pass rate by check

| Check | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| format_ok | 0% | 53% | 47% | 33% |
| language_ok | 100% | 56% | 70% | 67% |
| length_ok | 50% | 47% | 50% | 40% |
| mentions_company | 100% | 53% | 73% | 67% |
| mentions_detail | 100% | 59% | 74% | 67% |
| no_forbidden | 93% | 100% | 100% | 100% |
| no_placeholders | 97% | 100% | 100% | 100% |
| proposes_call | 90% | 43% | 47% | 33% |
| signs_off | 73% | 30% | 47% | 33% |

## Pass rate by lead type

| Lead type | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| german | 0% | 0% | 0% | 0% |
| injection | 0% | 56% | 89% | 89% |
| long | 0% | 0% | 0% | 0% |
| messy | 0% | 17% | 50% | 33% |
| normal | 0% | 0% | 0% | 0% |
| short | 0% | 50% | 50% | 0% |

## Example failures

**`v1_basic`**
- H01 (normal): failed format_ok
- H01 (normal): failed format_ok
- H01 (normal): failed format_ok
- H02 (short): failed format_ok, length_ok

**`v2_structured`**
- H01 (normal): failed format_ok, mentions_company, mentions_detail, length_ok, proposes_call, signs_off, language_ok
- H01 (normal): failed length_ok, proposes_call, signs_off
- H01 (normal): failed proposes_call, signs_off
- H02 (short): failed format_ok, mentions_company, length_ok, proposes_call, signs_off, language_ok

**`v3_fewshot_json`**
- H01 (normal): failed format_ok, mentions_company, mentions_detail, length_ok, proposes_call, signs_off, language_ok
- H01 (normal): failed format_ok, mentions_company, mentions_detail, length_ok, proposes_call, signs_off, language_ok
- H01 (normal): failed format_ok, length_ok, proposes_call, signs_off
- H02 (short): failed format_ok, length_ok, proposes_call, signs_off

**`v4_targeted`**
- H01 (normal): failed format_ok, proposes_call, signs_off
- H01 (normal): failed format_ok, mentions_company, mentions_detail, length_ok, proposes_call, signs_off, language_ok
- H01 (normal): failed format_ok, proposes_call, signs_off
- H02 (short): failed format_ok, length_ok, proposes_call, signs_off

Full outputs for every email are in `raw_results.jsonl`.

_Limits: automatic checks are heuristics; the lead set is small and synthetic; one model; manual ratings are subjective. Treat differences of a few points as noise._
