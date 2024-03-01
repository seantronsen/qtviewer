from typing import Callable, Optional
from numpy.typing import NDArray
import pyqtgraph as pg
from pyqtgraph import GraphicsLayoutWidget, LayoutWidget

from qtviewer.state import State
from qtviewer.widgets import StatefulWidget


class StatefulPane(LayoutWidget):
    """
    A simple pane/panel class that holds some state used for event handling /
    processing. Layouts are created vertically as this is the simplest scheme
    to use for fast prototyping and allows for the maximal possible viewport
    for data analysis. Override the methods related to layout if different
    behavior is desired.

    """

    __state: State

    def __init__(self, callback) -> None:
        super().__init__()
        self.__state = State(callback)

    def update(self, **_):
        """
        IMPORTANT: A parent method which will fail if not overridden/shadowed.

        This function is the callback provided to the State instance and is
        executed on each state change. The user specified callback is executed
        by this callback. If you wish to exist in user land, don't worry about
        anything other than the one callback you're required to define as this
        detail isn't important to the experience.

        """
        raise NotImplementedError

    def force_flush(self):
        """
        more so here for possible future convenience. don't really have a use
        for this right now... maybe debugging later? depends on the obnoxious
        level of inheritance object oriented programming can aspire to.

        """
        self.__state.flush()

    def enchain(self, widget: StatefulWidget):
        """
        Bond a stateful widget with the pane state such that updates to this control
        widget will affect the pane when configured properly. Ensure proper
        configuration by naming a variable in the user specified call back
        function with the key value for the widget state component.

        :param widget: [TODO:description]
        """

        widget.attach(self.__state)

    def attach_widget(self, widget: StatefulWidget):
        """
        Enchain the pane state with the specified widget and position it
        beneath the main feature pane. Use this method when a control widget
        should be directly associated with a specific data display pane.

        :param widget: [TODO:description]
        """
        self.enchain(widget)
        self.addWidget(widget)
        self.nextRow()


class ImagePane(StatefulPane):
    """
    A pane which can be used to display and analyze image data with a fast
    refresh rate. Functionality dictates an initial image be provided to the
    constructor along with the user specified callback function. The callback
    function can be used to chaneg the currently display image.

    IMPORTANT: Data immutability is a property that should be abided by when
    defining the callback function. That is, the callback function should
    either return entirely new data or a modified copy of the original data.
    Failing to abide by this suggestion will require users to restart the
    application in order to re-obtain the initial state of the image later
    mutated by the callback.

    IMPORTANT: Image data should be normalized and converted to standard bytes
    (uint8). Note the underlying pyqtgraph library supports uint16 and small
    floats, but visualization works best and renders fastest for bytes.
    """

    iv: pg.ImageView
    callback: Callable

    def __init__(self, image: NDArray, calculate: Optional[Callable] = None) -> None:
        super().__init__(self.update)
        self.iv = pg.ImageView()
        self.callback = calculate if calculate is not None else lambda *a, **b: image
        self.addWidget(self.iv)
        self.nextRow()

        # prepare for data display
        self.set_image(image)

    def set_image(self, image: NDArray):
        """
        Set the currently displayed image and immediately render the update on
        the pane.

        :param image: a new image to render encoded as an ndarray
        """
        self.iv.setImage(image, autoRange=True, autoLevels=True, autoHistogramRange=True)

    def update(self, **args):
        new_image = self.callback(**args)
        self.set_image(new_image)


class GraphicsPane(StatefulPane):
    """
    A more complicated to implement image pane which may display data at a
    faster FPS depending on the user's machine and operating system.
    Functionality dictates an initial image be provided to the constructor
    along with the user specified callback function. The callback function can
    be used to chaneg the currently display image.

    IMPORTANT: Data immutability is a property that should be abided by when
    defining the callback function. That is, the callback function should
    either return entirely new data or a modified copy of the original data.
    Failing to abide by this suggestion will require users to restart the
    application in order to re-obtain the initial state of the image later
    mutated by the callback.

    IMPORTANT: Image data should be normalized and converted to standard bytes
    (uint8). Note the underlying pyqtgraph library supports uint16 and small
    floats, but visualization works best and renders fastest for bytes.

    """

    gp: pg.GraphicsView
    callback: Optional[Callable]
    img_item: pg.ImageItem
    vb: pg.ViewBox

    def __init__(self, image: NDArray, calculate: Optional[Callable] = None) -> None:
        super().__init__(self.update)

        # set up graphics view
        self.gp = pg.GraphicsView()
        self.addWidget(self.gp)
        self.nextRow()

        # set up mod image view
        self.callback = calculate
        self.vb = pg.ViewBox()
        self.gp.setCentralWidget(self.vb)
        self.img_item = pg.ImageItem()
        self.vb.setAspectLocked()
        self.vb.addItem(self.img_item)

        # prepare for data display
        self.set_image(image)

    def set_image(self, image: NDArray):
        """
        Set the currently displayed image and immediately render the update on
        the pane.

        :param image: a new image to render encoded as an ndarray
        """
        self.img_item.setImage(image)

    def update(self, **args):
        new_image = self.callback(**args)  # pyright: ignore
        self.set_image(new_image)


class Plot2DPane(StatefulPane):
    """
    IMPORTANT: Data immutability is a property that should be abided by when
    defining the callback function. That is, the callback function should
    either return entirely new data or a modified copy of the original data.
    Failing to abide by this suggestion will require users to restart the
    application in order to re-obtain the initial state of the image later
    mutated by the callback.
    """

    plots_window: pg.GraphicsLayoutWidget
    plotPrimary: pg.PlotItem
    callback: Callable

    def __init__(self, data: NDArray, calculate: Optional[Callable] = None, **kwargs) -> None:
        super().__init__(self.update)
        kwarg_flag = lambda x: kwargs.get(x) if kwargs.get(x) is not None else False

        self.callback = calculate if calculate is not None else lambda *a, **b: data

        # prepare the graphics layout
        self.plots_window = GraphicsLayoutWidget()
        self.addWidget(self.plots_window)
        self.nextRow()

        self.plotPrimary = self.plots_window.addPlot(title=kwargs.get("title"))
        if kwarg_flag("legend"):
            self.plotPrimary.addLegend()

        self.plotPrimary.setLogMode(x=kwarg_flag("logx"), y=kwarg_flag("logy"))
        self.plotPrimary.showGrid(x=kwarg_flag("gridx"), y=kwarg_flag("gridy"))

        plot_args = dict()
        plot_args["pen"] = None if kwarg_flag("scatter") else 'g'
        plot_args["symbol"] = 't' if kwarg_flag("scatter") else None
        plot_args["symbolSize"] = 10
        plot_args["symbolBrush"] = (0, 255, 0, 90)

        self.curve = self.plotPrimary.plot(**plot_args)
        self.set_data(data)

    def set_data(self, data: NDArray):
        """
        Provide an NDArray either of shape (N,) or (N, 2). When the first case
        is true, the plotter assumes you have provided the y-coordinates and a
        uniform spacing of x-coordinates will be generated for you. In the
        second case, it is assumed that both kinds of points were provided.

        :param data: [TODO:description]
        """

        self.curve.setData(data)

    def update(self, **args):
        data = self.callback(**args)
        self.set_data(data)
