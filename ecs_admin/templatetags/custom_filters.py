from django import template

register = template.Library()

@register.filter
def dict_lookup(dictionary, key):
    """
    Lookup a key in a dictionary from within a Django template.
    Usage: {{ reviewer_applications|dict_lookup:status }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, [])
    return []

@register.filter
def get_item(dictionary, key):
    """
    Get a single item from a dictionary by key.
    Usage: {{ my_dict|get_item:my_key }}

    Returns the value if found, 'N/A' if not found.
    """
    if isinstance(dictionary, dict) and key:
        return dictionary.get(key, 'N/A')
    return 'N/A'
