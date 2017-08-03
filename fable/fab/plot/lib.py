from matplotlib.backend_bases import GraphicsContextBase, FigureManagerBase, FigureCanvasBase
from matplotlib.figure import Figure
import io
from fable.fab.plot import show_png_data

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
    with io.BytesIO() as f:
        plt.gcf().savefig(f, format='png', transparent=True)
        show_png_data(f.getvalue(), width=width, height=height)
