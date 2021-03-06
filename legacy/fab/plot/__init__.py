import base64
from fable.fab import htmlout

def _format_option(name, value):
    if value is None:
        return ''
    return '{0}="{1}"'.format(name, value)

def show_png_data(value, width=None, height=None):
    text = base64.b64encode(value).decode('ascii')
    settings = ' '.join([_format_option('width', width), _format_option('height', height)])
    htmlout.write('<img alt="plot" ' + settings + ' src="data:image/png;base64,' + text + '"></img>')

def show_svg_data(value, width=None, height=None):
    value = value[value.index(b'<svg')+4:].decode('utf-8')
    settings = ' '.join([_format_option('width', width), _format_option('height', height)])
    value = '<svg ' + settings + value
    htmlout.write(value.replace('\n', ' '))
