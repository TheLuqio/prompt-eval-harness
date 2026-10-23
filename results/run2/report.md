# Prompt evaluation report

- Run at: 2026-10-20T21:08:56+00:00
- Model: `claude-haiku-4-5-20251001`
- Leads: 30 | repeats per lead: 3 | emails per prompt: 90
- Prompt versions: `v1_basic` (sha e53530ac73), `v2_structured` (sha bedee07832), `v3_fewshot_json` (sha 67ae0d8e32), `v4_targeted` (sha ec9c8a8a4f)

## Summary

| Prompt | Pass rate | Injection leads passed | Avg words | Avg latency (s) | Avg tokens in/out | Est. cost per email | Errors |
|---|---|---|---|---|---|---|---|
| `v1_basic` | 0% | 0% | 99 | 2.17 | 96 / 152 | n/a | 0 |
| `v2_structured` | 62% | 61% | 106 | 2.36 | 343 / 166 | n/a | 0 |
| `v3_fewshot_json` | 97% | 100% | 132 | 2.96 | 1296 / 232 | n/a | 0 |
| `v4_targeted` | 99% | 100% | 126 | 2.90 | 1983 / 216 | n/a | 0 |

Pass rate = share of emails that pass every applicable automatic check.

## Pass rate by check

| Check | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| format_ok | 0% | 100% | 100% | 100% |
| language_ok | 100% | 88% | 98% | 100% |
| length_ok | 42% | 70% | 97% | 99% |
| mentions_company | 89% | 97% | 100% | 100% |
| mentions_detail | 100% | 95% | 100% | 100% |
| no_forbidden | 96% | 100% | 100% | 100% |
| no_placeholders | 100% | 100% | 100% | 100% |
| proposes_call | 100% | 97% | 100% | 100% |
| signs_off | 93% | 100% | 100% | 100% |

## Pass rate by lead type

| Lead type | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| german | 0% | 56% | 100% | 89% |
| injection | 0% | 61% | 100% | 100% |
| long | 0% | 83% | 83% | 100% |
| messy | 0% | 56% | 100% | 100% |
| normal | 0% | 67% | 100% | 100% |
| short | 0% | 50% | 83% | 100% |

## Manual ratings (blind, 1 to 5)

| Prompt | Rated emails | Average rating |
|---|---|---|
| `v1_basic` | 10 | 3.70 |
| `v2_structured` | 10 | 3.40 |
| `v3_fewshot_json` | 10 | 4.10 |
| `v4_targeted` | 10 | 4.00 |

## Example failures

**`v1_basic`**
- L01 (normal): failed format_ok, mentions_company, length_ok
- L01 (normal): failed format_ok
- L01 (normal): failed format_ok
- L02 (normal): failed format_ok, length_ok

**`v2_structured`**
- L01 (normal): failed mentions_detail, length_ok, language_ok
- L01 (normal): failed mentions_detail, length_ok, language_ok
- L01 (normal): failed mentions_detail, length_ok, language_ok
- L02 (normal): failed length_ok

**`v3_fewshot_json`**
- L13 (short): failed length_ok, language_ok
- L13 (short): failed length_ok, language_ok
- L18 (long): failed length_ok

**`v4_targeted`**
- L21 (german): failed length_ok

Full outputs for every email are in `raw_results.jsonl`.

_Limits: automatic checks are heuristics; the lead set is small and synthetic; one model; manual ratings are subjective. Treat differences of a few points as noise._
