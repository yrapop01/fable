import io
from matplotlib.backend_bases import GraphicsContextBase, FigureManagerBase, FigureCanvasBase
from matplotlib.figure import Figure
from fable.logs import log

_log = log('fab')

class FigureCanvas(FigureCanvasBase):
    pass

class FigureManager(FigureManagerBase):
    pass

def new_figure_manager(num, *args, **kwargs):
    FigureClass = kwargs.pop('FigureClass', Figure)
    thisFig = FigureClass(*args, **kwargs)
    return new_figure_manager_given_figure(num, thisFig)

def new_figure_manager_given_figure(num, figure):
    canvas = FigureCanvas(figure)
    manager = FigureManager(canvas, num)
    return manager

def show(fmt='svg', **kw):
    import matplotlib.pyplot as plt
    from fable.fab import plot

    formats = ('svg', 'png')
    if fmt not in formats:
        raise Exception('Format must be one of: ' + ', '.join(formats))

    with io.BytesIO() as f:
        _log.info('generating plot', fmt)
        plt.gcf().savefig(f, format=fmt, transparent=True)
        _log.info('sending plot')
        if fmt == 'svg':
            plot.show_svg_data(f.getvalue(), **kw)
        elif fmt == 'png':
            plot.show_png_data(f.getvalue(), **kw)
        _log.info('plot sent')
