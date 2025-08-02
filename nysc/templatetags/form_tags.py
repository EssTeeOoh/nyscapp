# nyscapp/templatetags/form_tags.py
from django import template

register = template.Library()

@register.filter
def add_attrs(field, attr_string):
    """
    Add multiple attributes to a form field.
    attr_string should be a space-separated list of 'name:value' pairs (e.g., "class:form-control autocomplete:username").
    """
    attrs = {}
    if attr_string:
        for attr in attr_string.split():
            if ':' in attr:
                name, value = attr.split(':', 1)
                attrs[name] = value
    return field.as_widget(attrs=attrs)