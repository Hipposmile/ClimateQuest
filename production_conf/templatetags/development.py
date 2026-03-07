from django import template
from django.conf import settings

register = template.Library()


@register.tag
def development(parser, token):
    nodelist = parser.parse(('enddevelopment',))
    parser.delete_first_token()
    return DevelopmentNode(nodelist)


class DevelopmentNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        if settings.DEBUG:
            return self.nodelist.render(context)
        return ""
