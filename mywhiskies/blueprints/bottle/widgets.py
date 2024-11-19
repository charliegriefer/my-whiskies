from markupsafe import Markup
from wtforms.fields import SelectMultipleField
from wtforms.widgets import html_params


class Select2Widget:
    """Custom widget for a Select2 multiselect dropdown."""

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        classes = kwargs.pop("class", "")
        kwargs["class"] = f"js-select2 form-control {classes}".strip()
        # Add data-placeholder if placeholder is specified in render_kw
        if "placeholder" in kwargs:
            kwargs["data-placeholder"] = kwargs.pop("placeholder")
        kwargs["multiple"] = "multiple"
        html = [f"<select {html_params(name=field.name, **kwargs)}>"]
        for value, label, selected in field.iter_choices():
            selected_attr = "selected" if selected else ""
            html.append(f'<option value="{value}" {selected_attr}>{label}</option>')
        html.append("</select>")
        return Markup("".join(html))


class Select2Field(SelectMultipleField):
    """Custom field for Select2 multiselect dropdown."""

    widget = Select2Widget()
