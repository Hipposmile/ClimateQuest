from django import template

register = template.Library()

@register.tag
def production(parser, token):
    nodelist = parser.parse(('endproduction',))
    parser.delete_first_token()
    return ProductionNode(nodelist)

class ProductionNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        debug = context.get('debug', False)
        if not debug:
            return self.nodelist.render(context)
        return ""