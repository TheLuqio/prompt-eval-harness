# Prompt evaluation report

- Run at: 2026-10-27T22:57:12+00:00
- Model: `claude-haiku-5-5`
- Settings: max_tokens=700, thinking=disabled, effort=model default
- Leads: 30 | repeats per lead: 3 | emails per prompt: 90
- Prompt versions: `v1_basic` (sha e53530ac73), `v2_structured` (sha bedee07832), `v3_fewshot_json` (sha 67ae0d8e32), `v4_targeted` (sha ec9c8a8a4f)

## Summary

| Prompt | Pass rate | Pass rate on injection leads | Avg words | Avg latency (s) | Avg tokens in/out | Est. cost per email | Errors | Cut off |
|---|---|---|---|---|---|---|---|---|
| `v1_basic` | 0% | 0% | 106 | 1.97 | 130 / 215 | $0.00012 | 0 | 0 |
| `v2_structured` | 87% | 100% | 132 | 2.24 | 450 / 267 | $0.00018 | 0 | 0 |
| `v3_fewshot_json` | 91% | 100% | 144 | 2.25 | 1770 / 320 | $0.00034 | 0 | 0 |
| `v4_targeted` | 97% | 100% | 130 | 2.09 | 2685 / 296 | $0.00042 | 0 | 0 |

Pass rate = share of emails that pass every applicable automatic check.

## Pass rate by check

| Check | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| format_ok | 2% | 100% | 100% | 100% |
| language_ok | 100% | 91% | 96% | 97% |
| length_ok | 51% | 94% | 96% | 100% |
| mentions_company | 91% | 98% | 100% | 100% |
| mentions_detail | 100% | 94% | 98% | 96% |
| no_forbidden | 93% | 100% | 100% | 100% |
| no_meta_notes | 93% | 100% | 100% | 100% |
| no_placeholders | 100% | 100% | 100% | 100% |
| proposes_call | 100% | 99% | 100% | 100% |
| signs_off | 96% | 100% | 100% | 100% |

## Pass rate by lead type

| Lead type | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| german | 0% | 89% | 100% | 100% |
| injection | 0% | 100% | 100% | 100% |
| long | 0% | 67% | 33% | 100% |
| messy | 0% | 100% | 100% | 100% |
| normal | 0% | 83% | 94% | 92% |
| short | 0% | 75% | 83% | 100% |

## Example failures

**`v1_basic`**
- L01 (normal): failed format_ok, length_ok
- L01 (normal): failed format_ok, length_ok
- L01 (normal): failed format_ok, length_ok
- L02 (normal): failed format_ok, length_ok

**`v2_structured`**
- L01 (normal): failed mentions_detail, language_ok
- L01 (normal): failed mentions_detail, language_ok
- L04 (normal): failed language_ok
- L11 (normal): failed mentions_detail, language_ok

**`v3_fewshot_json`**
- L11 (normal): failed mentions_detail, language_ok
- L11 (normal): failed mentions_detail, language_ok
- L13 (short): failed language_ok
- L13 (short): failed language_ok

**`v4_targeted`**
- L11 (normal): failed mentions_detail, language_ok
- L11 (normal): failed mentions_detail, language_ok
- L11 (normal): failed mentions_detail, language_ok

Full outputs for every email are in `raw_results.jsonl`.

_Limits: automatic checks are heuristics; the lead set is small and synthetic; one model; manual ratings are subjective. Treat differences of a few points as noise._
