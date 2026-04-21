# test_scraper.py
import pytest
# We import from your existing file, which is now testable!
from yt_scraper 
import clean_transcript_text, get_dx_error_response

# -- Red-Green-Refactor for Data Cleaning --

def test_clean_text_removes_fillers():
    # Input with verbal 'noise'
    raw_input = "Okay, um, basically, like, here is the code, right?"
    expected_output = "Okay, here is the code,"
    
    assert clean_transcript_text(raw_input) == expected_output

def test_clean_text_ignores_case_fillers():
    raw_input = "Um, Basically, Here Is Like, The Data."
    expected_output = "Here Is The Data."
    assert clean_transcript_text(raw_input) == expected_output

def test_clean_text_collapses_whitespace():
    raw_input = "Line one.      Line two with um like extra spaces."
    expected_output = "Line one. Line two with extra spaces."
    assert clean_transcript_text(raw_input) == expected_output

def test_clean_text_removes_brackets():
    raw_input = "Welcome back [Music] um and applause [Applause] let's code."
    expected_output = "Welcome back and let's code."
    assert clean_transcript_text(raw_input) == expected_output

# -- DX Validation Tests --

def test_dx_error_returns_valid_link():
    payload = get_dx_error_response("dQw4w9WgXcQ", "TRANSCRIPT_DISABLED")
    
    assert payload["status"] == 404
    assert payload["error_code"] == "YT_TRANSCRIPT_UNAVAILABLE"
    # Verify the deep-link is present (the most important part from the image)
    assert "dx_deep_link" in payload
    assert payload["dx_deep_link"].endswith("#transcript-unavailable")