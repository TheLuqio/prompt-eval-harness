# Prompt evaluation report

- Run at: 2026-10-27T22:58:39+00:00
- Model: `claude-haiku-5-5`
- Settings: max_tokens=700, thinking=disabled, effort=model default
- Leads: 10 | repeats per lead: 3 | emails per prompt: 30
- Prompt versions: `v1_basic` (sha e53530ac73), `v2_structured` (sha bedee07832), `v3_fewshot_json` (sha 67ae0d8e32), `v4_targeted` (sha ec9c8a8a4f)

## Summary

| Prompt | Pass rate | Pass rate on injection leads | Avg words | Avg latency (s) | Avg tokens in/out | Est. cost per email | Errors | Cut off |
|---|---|---|---|---|---|---|---|---|
| `v1_basic` | 0% | 0% | 102 | 1.93 | 129 / 207 | $0.00012 | 0 | 0 |
| `v2_structured` | 73% | 100% | 126 | 2.20 | 449 / 272 | $0.00018 | 0 | 0 |
| `v3_fewshot_json` | 90% | 100% | 146 | 2.26 | 1769 / 314 | $0.00033 | 0 | 0 |
| `v4_targeted` | 97% | 100% | 134 | 1.94 | 2684 / 293 | $0.00041 | 0 | 0 |

Pass rate = share of emails that pass every applicable automatic check.

## Pass rate by check

| Check | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| format_ok | 3% | 100% | 100% | 100% |
| language_ok | 100% | 78% | 100% | 100% |
| length_ok | 33% | 87% | 90% | 97% |
| mentions_company | 93% | 97% | 100% | 100% |
| mentions_detail | 100% | 89% | 100% | 100% |
| no_forbidden | 100% | 100% | 100% | 100% |
| no_meta_notes | 97% | 100% | 100% | 100% |
| no_placeholders | 100% | 100% | 100% | 100% |
| proposes_call | 100% | 100% | 100% | 100% |
| signs_off | 100% | 100% | 100% | 100% |

## Pass rate by lead type

| Lead type | `v1_basic` | `v2_structured` | `v3_fewshot_json` | `v4_targeted` |
|---|---|---|---|---|
| german | 0% | 100% | 100% | 100% |
| injection | 0% | 100% | 100% | 100% |
| long | 0% | 33% | 0% | 67% |
| messy | 0% | 100% | 100% | 100% |
| normal | 0% | 0% | 100% | 100% |
| short | 0% | 50% | 100% | 100% |

## Example failures

**`v1_basic`**
- H01 (normal): failed format_ok, length_ok
- H01 (normal): failed format_ok, length_ok
- H01 (normal): failed format_ok
- H02 (short): failed format_ok, length_ok

**`v2_structured`**
- H01 (normal): failed mentions_detail, length_ok, language_ok
- H01 (normal): failed mentions_detail, language_ok
- H01 (normal): failed mentions_detail, length_ok, language_ok
- H02 (short): failed language_ok

**`v3_fewshot_json`**
- H05 (long): failed length_ok
- H05 (long): failed length_ok
- H05 (long): failed length_ok

**`v4_targeted`**
- H05 (long): failed length_ok

Full outputs for every email are in `raw_results.jsonl`.

_Limits: automatic checks are heuristics; the lead set is small and synthetic; one model; manual ratings are subjective. Treat differences of a few points as noise._
