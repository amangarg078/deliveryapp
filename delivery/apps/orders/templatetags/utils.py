from django import template

register = template.Library()


@register.filter(name='set_element_attributes')
def set_element_attributes(element, attribute_dict):
    """
    WARNING!!! This Overrides the previously-set attribute, so use wisely!
    TODO: update the attributes instead of overriding
    """
    attrs = element.field.widget.attrs

    pairs = attribute_dict.split(',')

    for pair in pairs:
        if ':' in pair:
            kv = pair.split(':')
            attrs[kv[0]] = kv[1]
        else:
            attrs[pair] = ''

    rendered = str(element)

    return rendered
