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

def show(width=None, height=None):
    import matplotlib.pyplot as plt
    from fable.fab import plot

    with io.BytesIO() as f:
        _log.info('generating plot svg')
        plt.gcf().savefig(f, format='svg', transparent=True)
        _log.info('sending plot svg')
        plot.show_svg_data(f.getvalue(), width=width, height=height)
        _log.info('plot svg sent')
