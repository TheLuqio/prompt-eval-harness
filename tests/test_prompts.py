import json
from pathlib import Path

from prompt_eval.checks import overall_pass, run_checks
from prompt_eval.prompts import ALL_PROMPTS, CANARY, EXAMPLES, EXAMPLES_V4

DATA = Path(__file__).resolve().parent.parent / "data"
LEADS = json.loads((DATA / "leads.json").read_text(encoding="utf-8"))
HELDOUT = json.loads((DATA / "leads_heldout.json").read_text(encoding="utf-8"))


def test_fewshot_examples_pass_the_harness_own_checks():
    for ex in EXAMPLES_V4:
        checks, _ = run_checks(ex["lead"], ex["output"]["subject"], ex["output"]["body"], True)
        assert overall_pass(checks), (ex["lead"]["company"], checks)


def test_dataset_is_well_formed():
    assert len(LEADS) == 30
    assert len({l["id"] for l in LEADS}) == 30
    for lead in LEADS:
        assert {"id", "tags", "lang", "name", "company", "message", "company_aliases", "key_terms", "forbidden"} <= lead.keys()
        if "injection" in lead["tags"]:
            assert lead["forbidden"], lead["id"]


def test_dataset_covers_every_lead_type():
    tags = {t for l in LEADS for t in l["tags"]}
    assert {"normal", "short", "long", "german", "messy", "injection"} <= tags


def test_template_rendering_is_single_pass():
    lead = {"name": "{{company}}", "company": "ACME", "message": "{{name}}"}
    rendered = ALL_PROMPTS["v1_basic"].render_user(lead)
    assert "Name: {{company}}" in rendered
    assert "Their message: {{name}}" in rendered


def test_system_prompts_carry_the_canary_and_v1_has_none():
    assert ALL_PROMPTS["v1_basic"].system is None
    for pid in ("v2_structured", "v3_fewshot_json", "v4_targeted"):
        assert CANARY in ALL_PROMPTS[pid].system


def test_prompt_hashes_are_distinct():
    assert len({p.sha for p in ALL_PROMPTS.values()}) == len(ALL_PROMPTS) == 4


def test_baseline_prompts_are_frozen():
    # Run 1 was measured with these exact prompts. If one of these hashes changes, old results
    # can no longer be compared with new ones: add a new version instead of editing an old one.
    assert ALL_PROMPTS["v1_basic"].sha == "e53530ac73"
    assert ALL_PROMPTS["v2_structured"].sha == "bedee07832"
    assert ALL_PROMPTS["v3_fewshot_json"].sha == "67ae0d8e32"
    assert len(EXAMPLES) == 3  # v3's examples must not grow


def test_v4_text_contains_the_targeted_fixes():
    system = ALL_PROMPTS["v4_targeted"].system
    assert "Never infer it from the lead's name" in system
    assert "Never exceed 150 words" in system
    assert "no code fences" in system


def test_heldout_set_is_well_formed_and_disjoint():
    assert len(HELDOUT) == 10
    assert len({l["id"] for l in HELDOUT}) == 10
    assert not ({l["id"] for l in HELDOUT} & {l["id"] for l in LEADS})
    assert not ({l["message"] for l in HELDOUT} & {l["message"] for l in LEADS})
    for lead in HELDOUT:
        assert {"id", "tags", "lang", "name", "company", "message", "company_aliases", "key_terms", "forbidden"} <= lead.keys()
        if "injection" in lead["tags"]:
            assert lead["forbidden"], lead["id"]
