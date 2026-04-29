from datetime import date, datetime

from markupsafe import Markup

from mywhiskies.common.filters import (
    date_or_dash,
    float_or_dash,
    multiline_or_dash,
    render_rich_text,
    strip_html,
    value_or_dash,
    yesno,
)

# --- yesno ---


def test_yesno_true():
    assert yesno(True) == "Yes"


def test_yesno_false():
    assert yesno(False) == "No"


def test_yesno_custom_labels():
    assert yesno(1, yes="Yep", no="Nope") == "Yep"
    assert yesno(0, yes="Yep", no="Nope") == "Nope"


def test_yesno_truthy_values():
    assert yesno("something") == "Yes"
    assert yesno([]) == "No"


# --- value_or_dash ---


def test_value_or_dash_with_value():
    result = value_or_dash("hello")
    assert isinstance(result, Markup)
    assert "hello" in result


def test_value_or_dash_with_none():
    result = value_or_dash(None)
    assert isinstance(result, Markup)
    assert "text-muted" in result
    assert "-" in result


def test_value_or_dash_with_empty_string():
    result = value_or_dash("   ")
    assert "text-muted" in result


def test_value_or_dash_custom_fallback():
    result = value_or_dash(None, fallback="N/A")
    assert "N/A" in result


def test_value_or_dash_escapes_html():
    result = value_or_dash("<script>")
    assert "<script>" not in result


# --- multiline_or_dash ---


def test_multiline_or_dash_with_none():
    result = multiline_or_dash(None)
    assert "text-muted" in result
    assert "-" in result


def test_multiline_or_dash_with_single_line():
    result = multiline_or_dash("hello")
    assert "hello" in result
    assert "<br" not in result


def test_multiline_or_dash_with_newlines():
    result = multiline_or_dash("line1\nline2")
    assert "<br />" in result


def test_multiline_or_dash_normalizes_crlf():
    result = multiline_or_dash("line1\r\nline2")
    assert "<br />" in result


def test_multiline_or_dash_escapes_html():
    result = multiline_or_dash("<b>bold</b>")
    assert "<b>" not in result


# --- date_or_dash ---


def test_date_or_dash_with_none():
    result = date_or_dash(None)
    assert "text-muted" in result
    assert "-" in result


def test_date_or_dash_with_date():
    result = date_or_dash(date(2024, 6, 15))
    assert "15 Jun 2024" in result


def test_date_or_dash_with_datetime():
    result = date_or_dash(datetime(2024, 6, 15, 12, 0))
    assert "15 Jun 2024" in result


def test_date_or_dash_custom_format():
    result = date_or_dash(date(2024, 6, 15), fmt="%Y-%m-%d")
    assert "2024-06-15" in result


def test_date_or_dash_with_invalid_type():
    result = date_or_dash("not-a-date")
    assert "text-muted" in result


# --- float_or_dash ---


def test_float_or_dash_with_none():
    result = float_or_dash(None)
    assert "text-muted" in result
    assert "-" in result


def test_float_or_dash_with_float():
    result = float_or_dash(68.4)
    assert "68.40" in result


def test_float_or_dash_with_int():
    result = float_or_dash(50)
    assert "50.00" in result


def test_float_or_dash_custom_precision():
    result = float_or_dash(68.4, precision=1)
    assert "68.4" in result


def test_float_or_dash_with_invalid_value():
    result = float_or_dash("not-a-number")
    assert "text-muted" in result


# --- render_rich_text ---


def test_render_rich_text_with_none():
    result = render_rich_text(None)
    assert "text-muted" in result
    assert "-" in result


def test_render_rich_text_with_empty_string():
    result = render_rich_text("   ")
    assert "text-muted" in result


def test_render_rich_text_passthrough_allowed_tags():
    result = render_rich_text("<strong>bold</strong>")
    assert isinstance(result, Markup)
    assert "<strong>bold</strong>" in result


def test_render_rich_text_strips_disallowed_tags():
    result = render_rich_text("<script>alert('xss')</script>hello")
    assert "<script>" not in result
    assert "hello" in result


def test_render_rich_text_allows_links():
    result = render_rich_text('<a href="https://example.com">link</a>')
    assert 'href="https://example.com"' in result
    assert ">link</a>" in result


# --- strip_html ---


def test_strip_html_removes_tags():
    assert strip_html("<strong>hello</strong>") == "hello"


def test_strip_html_with_none():
    assert strip_html(None) == ""


def test_strip_html_truncates():
    long_text = "a" * 300
    result = strip_html(long_text)
    assert len(result) <= 201  # 200 chars + ellipsis


def test_strip_html_no_truncation_when_short():
    result = strip_html("<em>short</em>")
    assert result == "short"
