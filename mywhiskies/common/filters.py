from datetime import date, datetime
from typing import Any

from markupsafe import Markup, escape


def yesno(value: Any, yes: str = "Yes", no: str = "No") -> str:
    """Return 'Yes' if value is true, 'No' otherwise."""
    return yes if value else no


def value_or_dash(
    value: Any, fallback: str = "-", dash_class: str = "text-muted"
) -> Markup:
    """Return the value if it is not None or empty, otherwise return a dash with a CSS class."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return Markup(f'<span class="{dash_class}">{escape(fallback)}</span>')
    return Markup(escape(value))


def multiline_or_dash(
    value: Any, fallback: str = "-", dash_class: str = "text-muted"
) -> Markup:
    """Return value with <br /> for newlines, or a styled dash if empty or None."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return Markup(f'<span class="{dash_class}">{escape(fallback)}</span>')

    # Replace newlines and escape text
    escaped = escape(value).replace("\n", "<br />")
    return Markup(escaped)


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


def float_or_dash(
    value: Any, precision: int = 2, fallback: str = "-", dash_class: str = "text-muted"
) -> Markup:
    """Format a float to the given precision or return a fallback dash wrapped in a span."""
    if value is None:
        return Markup(f'<span class="{dash_class}">{escape(fallback)}</span>')
    try:
        formatted = f"{float(value):.{precision}f}"
    except (ValueError, TypeError):
        return Markup(f'<span class="{dash_class}">{escape(fallback)}</span>')
    return Markup(escape(formatted))


def register_filters(app) -> None:
    app.jinja_env.filters["yesno"] = yesno
    app.jinja_env.filters["multiline_or_dash"] = multiline_or_dash
    app.jinja_env.filters["date_or_dash"] = date_or_dash
    app.jinja_env.filters["value_or_dash"] = value_or_dash
    app.jinja_env.filters["float_or_dash"] = float_or_dash
