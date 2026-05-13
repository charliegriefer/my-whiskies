import re
from datetime import date, datetime
from typing import Any

import nh3
from markupsafe import Markup, escape

_RICH_TEXT_ALLOWED_TAGS = {
    "a",
    "b",
    "blockquote",
    "br",
    "del",
    "div",
    "em",
    "h1",
    "li",
    "ol",
    "pre",
    "strong",
    "ul",
}
_RICH_TEXT_ALLOWED_ATTRS = {"a": {"href", "title"}}


def yesno(value: Any, yes: str = "Yes", no: str = "No") -> str:
    """Return 'Yes' if value is true, 'No' otherwise."""
    return yes if value else no


def value_or_dash(value: Any, fallback: str = "-", dash_class: str = "text-muted") -> Markup:
    """Return the value if it is not None or empty, otherwise return a dash with a CSS class."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return Markup(f'<span class="{dash_class}">{escape(fallback)}</span>')
    return Markup(escape(value))


def multiline_or_dash(value: Any, fallback: str = "-", dash_class: str = "text-muted") -> Markup:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return Markup(f'<span class="{dash_class}">{escape(fallback)}</span>')

    # normalize newlines
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    # escape user input (protects against HTML injection)
    escaped = escape(normalized)
    # insert <br /> after escaping
    with_breaks = escaped.replace("\n", Markup("<br />"))

    return Markup(with_breaks)


def date_or_dash(
    value: Any,
    fmt: str = "%d %b %Y",
    fallback: str = "-",
    dash_class: str = "text-muted",
) -> Markup:
    """Format a date or datetime using `fmt`, or return a styled dash if None/invalid."""
    if not value or not isinstance(value, (date, datetime)):
        return Markup(f'<span class="{dash_class}">{escape(fallback)}</span>')
    return Markup(escape(value.strftime(fmt)))


def float_or_dash(value: Any, precision: int = 2, fallback: str = "-", dash_class: str = "text-muted") -> Markup:
    """Format a float to the given precision or return a fallback dash wrapped in a span."""
    if value is None:
        return Markup(f'<span class="{dash_class}">{escape(fallback)}</span>')
    try:
        formatted = f"{float(value):.{precision}f}"
    except (ValueError, TypeError):
        return Markup(f'<span class="{dash_class}">{escape(fallback)}</span>')
    return Markup(escape(formatted))


def render_rich_text(value: Any, fallback: str = "-", dash_class: str = "text-muted") -> Markup:
    """Sanitize stored rich-text HTML and return safe Markup, or a styled dash if empty."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return Markup(f'<span class="{dash_class}">{escape(fallback)}</span>')
    sanitized = nh3.clean(
        str(value),
        tags=_RICH_TEXT_ALLOWED_TAGS,
        attributes=_RICH_TEXT_ALLOWED_ATTRS,
    )
    sanitized = re.sub(r"<br\s*/?>\s*<br\s*/?>", '<br><div class="rte-para-break"></div>', sanitized)
    return Markup(sanitized)


def strip_html(value: Any, max_chars: int = 200) -> str:
    """Strip HTML tags and return plain text, truncated to max_chars. Safe for use in attributes."""
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", "", str(value))
    text = text.strip()
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "…"
    return text


def register_filters(app) -> None:
    app.jinja_env.filters["yesno"] = yesno
    app.jinja_env.filters["multiline_or_dash"] = multiline_or_dash
    app.jinja_env.filters["date_or_dash"] = date_or_dash
    app.jinja_env.filters["value_or_dash"] = value_or_dash
    app.jinja_env.filters["float_or_dash"] = float_or_dash
    app.jinja_env.filters["render_rich_text"] = render_rich_text
    app.jinja_env.filters["strip_html"] = strip_html
