# Prompt evaluation report

- Run at: 2026-10-20T07:26:22+00:00
- Model: `claude-haiku-4-5-20251001`
- Leads: 30 | repeats per lead: 1 | emails per prompt: 30
- Prompt versions: `v1_basic` (sha e53530ac73), `v2_structured` (sha bedee07832), `v3_fewshot_json` (sha 67ae0d8e32)

## Summary

| Prompt | Pass rate | Injection leads passed | Avg words | Avg latency (s) | Avg tokens in/out | Est. cost per email | Errors |
|---|---|---|---|---|---|---|---|
| `v1_basic` | 0% | 0% | 98 | 2.18 | 96 / 150 | n/a | 0 |
| `v2_structured` | 47% | 17% | 105 | 2.26 | 343 / 165 | n/a | 0 |
| `v3_fewshot_json` | 93% | 100% | 133 | 2.93 | 1296 / 234 | n/a | 0 |

Pass rate = share of emails that pass every applicable automatic check.

## Pass rate by check

| Check | `v1_basic` | `v2_structured` | `v3_fewshot_json` |
|---|---|---|---|
| format_ok | 0% | 100% | 97% |
| language_ok | 100% | 87% | 97% |
| length_ok | 40% | 50% | 97% |
| mentions_company | 83% | 100% | 100% |
| mentions_detail | 100% | 93% | 100% |
| no_forbidden | 97% | 100% | 100% |
| no_placeholders | 100% | 100% | 100% |
| proposes_call | 97% | 93% | 100% |
| signs_off | 93% | 100% | 100% |

## Pass rate by lead type

| Lead type | `v1_basic` | `v2_structured` | `v3_fewshot_json` |
|---|---|---|---|
| german | 0% | 33% | 100% |
| injection | 0% | 17% | 100% |
| long | 0% | 100% | 50% |
| messy | 0% | 33% | 100% |
| normal | 0% | 58% | 100% |
| short | 0% | 50% | 75% |

## Manual ratings (blind, 1 to 5)

| Prompt | Rated emails | Average rating |
|---|---|---|
| `v1_basic` | 10 | 3.90 |
| `v2_structured` | 10 | 3.30 |
| `v3_fewshot_json` | 10 | 3.80 |

## Example failures

**`v1_basic`**
- L01 (normal): failed format_ok
- L02 (normal): failed format_ok, length_ok
- L03 (normal): failed format_ok
- L04 (normal): failed format_ok, mentions_company, length_ok

**`v2_structured`**
- L01 (normal): failed mentions_detail, length_ok, language_ok
- L04 (normal): failed length_ok, language_ok
- L06 (normal): failed length_ok
- L08 (normal): failed length_ok

**`v3_fewshot_json`**
- L13 (short): failed language_ok
- L18 (long): failed format_ok, length_ok

Full outputs for every email are in `raw_results.jsonl`.

_Limits: automatic checks are heuristics; the lead set is small and synthetic; one model; manual ratings are subjective. Treat differences of a few points as noise._
