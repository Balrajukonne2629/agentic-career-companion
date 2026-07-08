"""
tests/test_validation_utils.py
==============================
Unit tests for agents/validation_utils.py.

All tests are:
  - Pure Python (no Granite, no Flask, no session)
  - Deterministic — no randomness, no network calls
  - Self-contained — no test fixtures that require a running server

Run with:
    python -m pytest tests/test_validation_utils.py -v
    (from the backend/ directory)
"""

import sys
import os

# Add backend root to path so imports work without package installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock ibm_watsonx_ai before any backend module is imported (config.py triggers it)
import types
for _mod in [
    "ibm_watsonx_ai", "ibm_watsonx_ai.foundation_models",
    "ibm_watsonx_ai.metanames", "ibm_cloud_sdk_core",
    "ibm_cloud_sdk_core.authenticators", "ibm_watson",
]:
    sys.modules[_mod] = types.ModuleType(_mod)

sys.modules["ibm_watsonx_ai"].APIClient = type("A", (), {})
sys.modules["ibm_watsonx_ai"].Credentials = type("C", (), {})
sys.modules["ibm_watsonx_ai.foundation_models"].ModelInference = type("M", (), {})
sys.modules["ibm_watsonx_ai.metanames"].GenTextParamsMetaNames = type(
    "G", (), {
        "MAX_NEW_TOKENS": "max_new_tokens",
        "TEMPERATURE": "temperature",
        "REPETITION_PENALTY": "repetition_penalty",
    }
)
sys.modules["ibm_cloud_sdk_core.authenticators"].IAMAuthenticator = type("I", (), {})
sys.modules["ibm_watson"].SpeechToTextV1 = type("S", (), {})

# Minimal env for config.py to pass validation
os.environ.setdefault("IBM_API_KEY",      "test_key")
os.environ.setdefault("IBM_PROJECT_ID",   "test_project")
os.environ.setdefault("IBM_WATSONX_URL",  "https://us-south.ml.cloud.ibm.com")
os.environ.setdefault("FLASK_SECRET_KEY", "test_secret_abc")

import pytest
from agents.validation_utils import (
    normalize_cgpa,
    normalize_year,
    normalize_skills,
    extract_availability,
)

# ---------------------------------------------------------------------------
# Canonical skills vocabulary (subset for testing)
# ---------------------------------------------------------------------------
VOCAB = [
    "JavaScript", "TypeScript", "Python", "Java", "C++", "C#",
    "React", "Vue.js", "Angular", "Next.js",
    "Node.js", "Express.js", "Django", "Flask", "FastAPI",
    "SQL", "MySQL", "PostgreSQL", "MongoDB", "Redis",
    "HTML", "CSS", "Sass", "Tailwind CSS",
    "Docker", "Kubernetes", "AWS", "Azure", "Git",
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
    "Pandas", "NumPy", "Scikit-learn",
    "Terraform", "CI/CD", "Linux", "Bash Scripting",
]


# ===========================================================================
# normalize_cgpa — 40 test cases
# ===========================================================================

class TestNormalizeCgpa:

    # -----------------------------------------------------------------------
    # None / empty / whitespace
    # -----------------------------------------------------------------------

    def test_none_returns_none(self):
        assert normalize_cgpa(None) is None

    def test_empty_string_returns_none(self):
        assert normalize_cgpa("") is None

    def test_whitespace_only_returns_none(self):
        assert normalize_cgpa("   ") is None

    # -----------------------------------------------------------------------
    # Float and int passthrough
    # -----------------------------------------------------------------------

    def test_float_passthrough(self):
        assert normalize_cgpa(8.58) == 8.58

    def test_int_passthrough(self):
        assert normalize_cgpa(9) == 9.0

    def test_float_zero_is_valid(self):
        assert normalize_cgpa(0.0) == 0.0

    def test_float_ten_is_valid(self):
        assert normalize_cgpa(10.0) == 10.0

    def test_float_above_ten_returns_none(self):
        assert normalize_cgpa(10.1) is None

    def test_negative_float_returns_none(self):
        assert normalize_cgpa(-1.0) is None

    # -----------------------------------------------------------------------
    # String decimal on 10-point scale
    # -----------------------------------------------------------------------

    def test_string_decimal_standard(self):
        assert normalize_cgpa("8.58") == 8.58

    def test_string_decimal_one_dp(self):
        assert normalize_cgpa("8.5") == 8.5

    def test_string_integer(self):
        assert normalize_cgpa("9") == 9.0

    def test_string_with_leading_spaces(self):
        assert normalize_cgpa("  7.8  ") == 7.8

    # -----------------------------------------------------------------------
    # Written number form
    # -----------------------------------------------------------------------

    def test_written_eight_point_five_eight(self):
        assert normalize_cgpa("eight point five eight") == 8.58

    def test_written_seven_point_five(self):
        assert normalize_cgpa("seven point five") == 7.5

    def test_written_nine_point_zero(self):
        assert normalize_cgpa("nine point zero") == 9.0

    def test_written_case_insensitive(self):
        assert normalize_cgpa("EIGHT POINT FIVE EIGHT") == 8.58

    def test_written_in_sentence(self):
        # Embedded in a longer string
        result = normalize_cgpa("My CGPA is eight point five eight currently")
        assert result == 8.58

    def test_written_three_digit_decimal(self):
        # "eight point one two" → 8.12
        assert normalize_cgpa("eight point one two") == 8.12

    # -----------------------------------------------------------------------
    # Percentage → 10-point conversion
    # -----------------------------------------------------------------------

    def test_percentage_whole(self):
        assert normalize_cgpa("85%") == 8.5

    def test_percentage_with_space(self):
        assert normalize_cgpa("85 %") == 8.5

    def test_percentage_word(self):
        assert normalize_cgpa("85 percent") == 8.5

    def test_percentage_decimal(self):
        assert normalize_cgpa("85.5%") == 8.55

    def test_percentage_100(self):
        assert normalize_cgpa("100%") == 10.0

    def test_percentage_in_sentence(self):
        assert normalize_cgpa("I scored 85% in my undergraduate") == 8.5

    def test_percentage_above_100_returns_none(self):
        # 110% → 11.0 → out of bounds → None
        assert normalize_cgpa("110%") is None

    # -----------------------------------------------------------------------
    # 4-point GPA → 10-point conversion
    # -----------------------------------------------------------------------

    def test_four_point_slash(self):
        result = normalize_cgpa("3.9/4")
        assert result == pytest.approx(9.75, abs=0.01)

    def test_four_point_slash_with_zero(self):
        result = normalize_cgpa("3.9/4.0")
        assert result == pytest.approx(9.75, abs=0.01)

    def test_four_point_out_of(self):
        result = normalize_cgpa("3.5 out of 4")
        assert result == pytest.approx(8.75, abs=0.01)

    def test_four_point_on_a(self):
        result = normalize_cgpa("3.0 on a 4 point scale")
        assert result == pytest.approx(7.5, abs=0.01)

    def test_four_point_perfect(self):
        result = normalize_cgpa("4.0/4.0")
        assert result == pytest.approx(10.0, abs=0.01)

    def test_four_point_in_sentence(self):
        result = normalize_cgpa("My GPA is 3.8 out of 4")
        assert result == pytest.approx(9.5, abs=0.01)

    # -----------------------------------------------------------------------
    # Boundary / edge cases
    # -----------------------------------------------------------------------

    def test_cgpa_exactly_zero(self):
        assert normalize_cgpa("0.0") == 0.0

    def test_cgpa_exactly_ten(self):
        assert normalize_cgpa("10.0") == 10.0

    def test_cgpa_eleven_returns_none(self):
        assert normalize_cgpa("11.0") is None

    def test_gibberish_returns_none(self):
        assert normalize_cgpa("twelve") is None

    def test_word_only_no_point(self):
        # "eight" alone — not a written CGPA (no "point X" part)
        # Falls through to plain decimal match → no digit → None
        assert normalize_cgpa("eight") is None

    def test_rounding_to_two_dp(self):
        # 3.333.../4.0 * 10 = 8.333... → rounded to 8.33
        result = normalize_cgpa("3.333/4.0")
        assert result == pytest.approx(8.33, abs=0.01)


# ===========================================================================
# normalize_year — 30 test cases
# ===========================================================================

class TestNormalizeYear:

    # -----------------------------------------------------------------------
    # None / empty / invalid types
    # -----------------------------------------------------------------------

    def test_none_returns_none(self):
        assert normalize_year(None) is None

    def test_empty_string_returns_none(self):
        assert normalize_year("") is None

    def test_whitespace_returns_none(self):
        assert normalize_year("   ") is None

    def test_out_of_range_high_returns_none(self):
        assert normalize_year(7) is None

    def test_out_of_range_zero_returns_none(self):
        assert normalize_year(0) is None

    def test_negative_returns_none(self):
        assert normalize_year(-1) is None

    def test_string_out_of_range(self):
        assert normalize_year("7") is None

    # -----------------------------------------------------------------------
    # Integer input
    # -----------------------------------------------------------------------

    def test_integer_one(self):
        assert normalize_year(1) == 1

    def test_integer_two(self):
        assert normalize_year(2) == 2

    def test_integer_four(self):
        assert normalize_year(4) == 4

    def test_integer_six_boundary(self):
        assert normalize_year(6) == 6

    # -----------------------------------------------------------------------
    # String integer
    # -----------------------------------------------------------------------

    def test_string_integer_two(self):
        assert normalize_year("2") == 2

    def test_string_integer_three(self):
        assert normalize_year("3") == 3

    # -----------------------------------------------------------------------
    # Ordinal abbreviations
    # -----------------------------------------------------------------------

    def test_ordinal_1st(self):
        assert normalize_year("1st") == 1

    def test_ordinal_2nd(self):
        assert normalize_year("2nd") == 2

    def test_ordinal_3rd(self):
        assert normalize_year("3rd") == 3

    def test_ordinal_4th(self):
        assert normalize_year("4th") == 4

    # -----------------------------------------------------------------------
    # Ordinal words
    # -----------------------------------------------------------------------

    def test_word_first(self):
        assert normalize_year("first") == 1

    def test_word_second(self):
        assert normalize_year("second") == 2

    def test_word_third(self):
        assert normalize_year("third") == 3

    def test_word_fourth(self):
        assert normalize_year("fourth") == 4

    def test_word_fifth(self):
        assert normalize_year("fifth") == 5

    def test_word_sixth(self):
        assert normalize_year("sixth") == 6

    # -----------------------------------------------------------------------
    # Compound phrases
    # -----------------------------------------------------------------------

    def test_compound_second_year(self):
        assert normalize_year("second year") == 2

    def test_compound_3rd_year(self):
        assert normalize_year("3rd year") == 3

    def test_compound_fourth_year(self):
        assert normalize_year("fourth year") == 4

    def test_compound_2nd_year_uppercase(self):
        assert normalize_year("2nd Year") == 2

    # -----------------------------------------------------------------------
    # Special: final year
    # -----------------------------------------------------------------------

    def test_final_year(self):
        assert normalize_year("final year") == 4

    def test_final_year_uppercase(self):
        assert normalize_year("Final Year") == 4

    def test_in_my_final_year(self):
        assert normalize_year("I am in my final year") == 4

    # -----------------------------------------------------------------------
    # Case insensitivity
    # -----------------------------------------------------------------------

    def test_case_insensitive_third(self):
        assert normalize_year("THIRD") == 3

    def test_case_insensitive_second_year(self):
        assert normalize_year("SECOND YEAR") == 2


# ===========================================================================
# normalize_skills — 35 test cases
# ===========================================================================

class TestNormalizeSkills:

    # -----------------------------------------------------------------------
    # Empty / null inputs
    # -----------------------------------------------------------------------

    def test_empty_list_returns_empty(self):
        assert normalize_skills([]) == []

    def test_non_string_items_skipped(self):
        assert normalize_skills([None, 123, True, "Python"], VOCAB) == ["Python"]

    def test_empty_string_items_skipped(self):
        assert normalize_skills(["", "  ", "Python"], VOCAB) == ["Python"]

    # -----------------------------------------------------------------------
    # Exact case-insensitive match
    # -----------------------------------------------------------------------

    def test_exact_match_lowercase(self):
        assert normalize_skills(["javascript"], VOCAB) == ["JavaScript"]

    def test_exact_match_uppercase(self):
        assert normalize_skills(["PYTHON"], VOCAB) == ["Python"]

    def test_exact_match_mixed_case(self):
        assert normalize_skills(["reAcT"], VOCAB) == ["React"]

    def test_exact_match_with_dot(self):
        assert normalize_skills(["node.js"], VOCAB) == ["Node.js"]

    def test_exact_match_sql(self):
        assert normalize_skills(["sql"], VOCAB) == ["SQL"]

    def test_multiple_exact_matches(self):
        result = normalize_skills(["python", "java", "react"], VOCAB)
        assert result == ["Python", "Java", "React"]

    # -----------------------------------------------------------------------
    # Deduplication
    # -----------------------------------------------------------------------

    def test_duplicate_exact_same(self):
        result = normalize_skills(["Python", "Python", "Python"], VOCAB)
        assert result == ["Python"]

    def test_duplicate_different_case(self):
        result = normalize_skills(["python", "PYTHON", "Python"], VOCAB)
        assert result == ["Python"]

    def test_duplicate_after_canonicalization(self):
        # "javascript" and "JavaScript" both canonicalize to "JavaScript"
        result = normalize_skills(["javascript", "JavaScript"], VOCAB)
        assert result == ["JavaScript"]

    # -----------------------------------------------------------------------
    # Prefix / reverse-prefix matching
    # -----------------------------------------------------------------------

    def test_prefix_node(self):
        # "node" → "Node.js" via reverse prefix
        result = normalize_skills(["node"], VOCAB)
        assert result == ["Node.js"]

    def test_prefix_express(self):
        result = normalize_skills(["express"], VOCAB)
        assert result == ["Express.js"]

    def test_prefix_react_js_variant(self):
        # "react.js" exact lower matches "react" prefix → "React"
        result = normalize_skills(["react.js"], VOCAB)
        assert result == ["React"]

    def test_prefix_django(self):
        result = normalize_skills(["django"], VOCAB)
        assert result == ["Django"]

    # -----------------------------------------------------------------------
    # Unknown skills preserved
    # -----------------------------------------------------------------------

    def test_unknown_skill_preserved(self):
        result = normalize_skills(["Selenium"], VOCAB)
        assert result == ["Selenium"]

    def test_unknown_skill_title_cased(self):
        result = normalize_skills(["selenium"], VOCAB)
        assert result == ["Selenium"]

    def test_multiple_unknowns_preserved(self):
        result = normalize_skills(["selenium", "pytest", "cypress"], VOCAB)
        assert "Selenium" in result
        assert "Pytest" in result
        assert "Cypress" in result

    # -----------------------------------------------------------------------
    # Mixed known and unknown
    # -----------------------------------------------------------------------

    def test_mixed_known_unknown(self):
        result = normalize_skills(["Python", "selenium"], VOCAB)
        assert result == ["Python", "Selenium"]

    def test_known_unknown_order_preserved(self):
        result = normalize_skills(["selenium", "Python"], VOCAB)
        assert result[0] == "Selenium"
        assert result[1] == "Python"

    # -----------------------------------------------------------------------
    # Without vocabulary (passthrough mode)
    # -----------------------------------------------------------------------

    def test_no_vocab_deduplicates(self):
        result = normalize_skills(["Python", "python", "PYTHON"])
        assert result == ["Python"]

    def test_no_vocab_preserves_all(self):
        result = normalize_skills(["React", "Django", "pandas"])
        assert len(result) == 3

    def test_no_vocab_empty_items_skipped(self):
        result = normalize_skills(["", "  ", "React"])
        assert result == ["React"]

    # -----------------------------------------------------------------------
    # Common student speech patterns
    # -----------------------------------------------------------------------

    def test_js_abbreviation(self):
        # "JS" — 2 chars, too short for prefix match → kept as "Js" (title-case)
        # This is expected: abbreviations without vocab entry are preserved
        result = normalize_skills(["JS"], VOCAB)
        assert isinstance(result[0], str)
        assert len(result) == 1

    def test_cpp_preserved(self):
        result = normalize_skills(["C++"], VOCAB)
        assert result == ["C++"]

    def test_cplusplus_variant(self):
        # "c++" exact match → "C++"
        result = normalize_skills(["c++"], VOCAB)
        assert result == ["C++"]

    def test_html_css_together(self):
        result = normalize_skills(["html", "css"], VOCAB)
        assert result == ["HTML", "CSS"]

    # -----------------------------------------------------------------------
    # Ordering: first occurrence wins on duplicate
    # -----------------------------------------------------------------------

    def test_first_occurrence_wins(self):
        # "javascript" comes first, "JavaScript" second
        result = normalize_skills(["javascript", "JavaScript", "Python"], VOCAB)
        assert result[0] == "JavaScript"
        assert result[1] == "Python"
        assert len(result) == 2


# ===========================================================================
# extract_availability — 25 test cases
# ===========================================================================

class TestExtractAvailability:

    # -----------------------------------------------------------------------
    # None / empty / no match
    # -----------------------------------------------------------------------

    def test_empty_string_returns_none(self):
        assert extract_availability("") is None

    def test_none_input_returns_none(self):
        assert extract_availability(None) is None

    def test_no_availability_statement(self):
        assert extract_availability("I am a second year IT student") is None

    def test_vague_statement_returns_none(self):
        assert extract_availability("I have limited time") is None

    def test_vague_statement_2_returns_none(self):
        assert extract_availability("I am busy with college") is None

    # -----------------------------------------------------------------------
    # "X hours a/per week" pattern
    # -----------------------------------------------------------------------

    def test_hours_a_week(self):
        assert extract_availability("I can study 15 hours a week") == 15

    def test_hours_per_week(self):
        assert extract_availability("I have 10 hours per week available") == 10

    def test_hour_singular_a_week(self):
        assert extract_availability("I have 1 hour a week") == 1

    def test_hours_a_week_at_start(self):
        assert extract_availability("20 hours a week is what I can give") == 20

    # -----------------------------------------------------------------------
    # "X hrs" variants
    # -----------------------------------------------------------------------

    def test_hrs_per_week(self):
        assert extract_availability("I have 10 hrs per week") == 10

    def test_hrs_slash_week(self):
        assert extract_availability("available 8 hrs/week") == 8

    def test_hrs_a_week(self):
        assert extract_availability("study 12 hrs a week") == 12

    # -----------------------------------------------------------------------
    # "Xh per/a week" compact form
    # -----------------------------------------------------------------------

    def test_h_per_week(self):
        assert extract_availability("I dedicate 8h per week") == 8

    def test_h_a_week(self):
        assert extract_availability("10h a week") == 10

    # -----------------------------------------------------------------------
    # "X hours weekly / every week"
    # -----------------------------------------------------------------------

    def test_hours_weekly(self):
        assert extract_availability("I study 14 hours weekly") == 14

    def test_hours_every_week(self):
        assert extract_availability("I can give 12 hours every week") == 12

    # -----------------------------------------------------------------------
    # "study for X hours" pattern (least specific)
    # -----------------------------------------------------------------------

    def test_study_for_hours(self):
        assert extract_availability("I can study for 20 hours") == 20

    def test_study_hours_no_for(self):
        assert extract_availability("I study 18 hours normally") == 18

    # -----------------------------------------------------------------------
    # Bounds validation
    # -----------------------------------------------------------------------

    def test_above_80_returns_none(self):
        assert extract_availability("I can study 100 hours a week") is None

    def test_exactly_80_is_valid(self):
        assert extract_availability("I can study 80 hours a week") == 80

    def test_exactly_1_is_valid(self):
        assert extract_availability("I can study 1 hour a week") == 1

    def test_zero_returns_none(self):
        # "0 hours" is out of bounds — implausible
        assert extract_availability("0 hours a week") is None

    # -----------------------------------------------------------------------
    # Case insensitivity
    # -----------------------------------------------------------------------

    def test_case_hours_uppercase(self):
        assert extract_availability("15 HOURS A WEEK") == 15

    def test_case_per_uppercase(self):
        assert extract_availability("10 Hrs Per Week") == 10

    # -----------------------------------------------------------------------
    # Embedded in longer text
    # -----------------------------------------------------------------------

    def test_embedded_in_full_transcript(self):
        transcript = (
            "Hi I am Balraju second year IT student CGPA 8.58 "
            "I know Java C++ and React I want to become a full stack developer "
            "I can study 15 hours a week"
        )
        assert extract_availability(transcript) == 15

    def test_returns_first_match_in_text(self):
        # Two availability statements — should return first match
        transcript = "I can study 10 hours a week and maybe 15 hours per week on weekends"
        result = extract_availability(transcript)
        assert result in (10, 15)  # Either is acceptable; first-found wins


# ===========================================================================
# Integration: all four utilities working together on realistic transcripts
# ===========================================================================

class TestIntegration:

    def test_full_transcript_balraju(self):
        """Simulate what the Validation Agent does with a complete transcript."""
        transcript = (
            "Hi I am Balraju second year Information Technology student "
            "my CGPA is eight point five eight "
            "I know Java C++ and React "
            "I want to become a Full Stack Developer "
            "I prefer learning by doing "
            "I can study 15 hours a week"
        )
        cgpa = normalize_cgpa("eight point five eight")
        year = normalize_year("second")
        skills = normalize_skills(["Java", "C++", "React"], VOCAB)
        avail = extract_availability(transcript)

        assert cgpa == 8.58
        assert year == 2
        assert skills == ["Java", "C++", "React"]
        assert avail == 15

    def test_partial_transcript_priya(self):
        """Simulate extraction from a partial transcript."""
        cgpa = normalize_cgpa("7.5")
        year = normalize_year("final year")
        skills = normalize_skills(["python", "sql", "pandas"], VOCAB)
        avail = extract_availability("I am a busy student with final year projects")

        assert cgpa == 7.5
        assert year == 4
        assert "Python" in skills
        assert "SQL" in skills
        assert "Pandas" in skills
        assert avail is None  # No explicit hours mentioned

    def test_percentage_cgpa_transcript(self):
        """Student states CGPA as percentage."""
        cgpa = normalize_cgpa("85%")
        assert cgpa == 8.5

    def test_four_point_cgpa_transcript(self):
        """Student states CGPA on 4-point scale."""
        cgpa = normalize_cgpa("3.8 out of 4")
        assert cgpa == pytest.approx(9.5, abs=0.01)

    def test_skills_dedup_with_vocab(self):
        """javascript and JS both appear — only one canonical entry."""
        skills = normalize_skills(["javascript", "JS", "react", "React.js"], VOCAB)
        assert skills.count("JavaScript") == 1
        assert skills.count("React") == 1
