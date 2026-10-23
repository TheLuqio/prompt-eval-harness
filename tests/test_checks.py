import pytest

from prompt_eval.checks import language_ok, overall_pass, parse_output, run_checks, word_count

LEAD = {
    "company": "Keller Dental Praxis",
    "company_aliases": ["Keller"],
    "key_terms": ["appointment", "reminder"],
    "forbidden": ["HACKED"],
    "lang": "en",
}

GOOD = (
    "Hi Maria,\n\nThank you for reaching out about appointment reminders at Keller Dental Praxis. "
    + "Confirming visits by phone takes your team real time, and this is a good task for automation. " * 5
    + "Would you be open to a short 15-minute call this week?\n\nBest regards,\nYigit"
)


def test_good_email_passes_everything():
    checks, wc = run_checks(LEAD, None, GOOD, True)
    assert overall_pass(checks), checks
    assert 100 <= wc <= 170


@pytest.mark.parametrize("bad", ["Hi [Name],", "Dear {{name}},", "Hi <Name>,", "lorem ipsum"])
def test_placeholders_are_caught(bad):
    checks, _ = run_checks(LEAD, None, GOOD + " " + bad, True)
    assert checks["no_placeholders"] is False


def test_company_alias_matching_is_case_insensitive():
    checks, _ = run_checks(LEAD, None, GOOD.replace("Keller Dental Praxis", "keller"), True)
    assert checks["mentions_company"] is True
    checks, _ = run_checks(LEAD, None, GOOD.replace("Keller Dental Praxis", "your practice"), True)
    assert checks["mentions_company"] is False


def test_detail_check_is_not_applicable_without_key_terms():
    lead = {**LEAD, "key_terms": []}
    checks, _ = run_checks(lead, None, GOOD, True)
    assert checks["mentions_detail"] is None


def test_length_bounds():
    short, _ = run_checks(LEAD, None, "Hi Maria, Keller call Yigit", True)
    assert short["length_ok"] is False
    long_text = GOOD + " word" * 100
    checks, _ = run_checks(LEAD, None, long_text, True)
    assert checks["length_ok"] is False


def test_forbidden_strings_detected_in_body_and_subject():
    checks, _ = run_checks(LEAD, None, "HACKED", True)
    assert checks["no_forbidden"] is False
    checks, _ = run_checks(LEAD, "hacked!", GOOD, True)
    assert checks["no_forbidden"] is False


def test_signoff_must_be_at_the_end():
    text = "Yigit says hello. " + GOOD.replace("Yigit", "Someone") + " "
    checks, _ = run_checks(LEAD, None, text, True)
    assert checks["signs_off"] is False


def test_parse_json_variants():
    ok = '{"subject": "Hi", "body": "Hello there"}'
    assert parse_output(ok, "json")[:3] == ("Hi", "Hello there", True)
    fenced = "```json\n" + ok + "\n```"
    assert parse_output(fenced, "json")[2] is True
    assert parse_output(ok + "\nThanks!", "json")[2] is False
    assert parse_output('{"subject": "Hi"}', "json")[2] is False
    assert parse_output("", "json")[2] is False


def test_plain_text_rejects_subject_lines_and_markdown():
    assert parse_output("Subject: Hello\n\nHi", "text")[2] is False
    assert parse_output("Hi **there**", "text")[2] is False
    assert parse_output("Hi there", "text")[2] is True


def test_language_heuristic():
    assert language_ok("Vielen Dank für Ihre Nachricht und wir haben gerne mit Ihnen gesprochen.", "de") is True
    assert language_ok("Thank you for your message and we will call you this week.", "de") is False
    assert language_ok("Thank you for your message and we will call you this week.", "en") is True
    assert language_ok("anything", None) is None


def test_word_count_handles_umlauts():
    assert word_count("Guten Tag, schöne Grüße") == 4


def test_company_alias_must_be_a_whole_word():
    lead = {**LEAD, "company": "Hall Marketing", "company_aliases": ["Hall"]}
    no_hall = GOOD.replace("Keller Dental Praxis", "your team").replace("Keller", "x")
    checks, _ = run_checks(lead, None, no_hall + " This is a real challenge.", True)
    assert checks["mentions_company"] is False  # 'Hall' hides inside 'challenge'
    checks, _ = run_checks(lead, None, no_hall + " Hall's team is welcome.", True)
    assert checks["mentions_company"] is True


def test_detail_terms_match_word_starts_only():
    lead = {**LEAD, "key_terms": ["appointment", "cancel"]}
    base = "Hi Maria, Keller call Yigit. "
    assert run_checks(lead, None, base + "Your cancellations are a pain.", True)[0]["mentions_detail"] is True
    assert run_checks(lead, None, base + "A disappointment, we know.", True)[0]["mentions_detail"] is False


def test_a_request_for_minutes_of_the_leads_time_counts_as_proposing_a_conversation():
    no_call = "Hi Maria, Keller " + "this is about reminders and appointments " * 14 + "Best regards, Yigit"
    assert run_checks(LEAD, None, no_call, True)[0]["proposes_call"] is False
    asks = no_call.replace("Best regards, Yigit", "Would you have 15 minutes this week to discuss it? Best regards, Yigit")
    assert run_checks(LEAD, None, asks, True)[0]["proposes_call"] is True
    assert run_checks(LEAD, None, no_call.replace("Best regards", "Let's talk soon. Best regards"), True)[0]["proposes_call"] is True


def test_calls_in_german_and_spanish_are_recognised():
    base = "Hi Maria, Keller " + "this is about reminders and appointments " * 14
    for phrase in ("einen kurzen 15-Minuten-Anruf", "una llamada rápida", "ein kurzes Telefonat"):
        assert run_checks(LEAD, None, base + phrase + " Best regards, Yigit", True)[0]["proposes_call"] is True
