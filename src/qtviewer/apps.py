import signal
import sys
from typing import List, NoReturn
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QWidget, QApplication
from pyqtgraph import LayoutWidget
from qtviewer.panels import AbstractStatefulPane
from qtviewer.widgets import AbstractControlWidget


class AppBase(QApplication):
    """
    A general refactoring of the larger application class which extracts some
    of the more basic elements.
    """

    panel: LayoutWidget
    timer: QTimer

    def __init__(self, title="qtviewer"):
        super().__init__([])
        self.panel = LayoutWidget()
        self.panel.setWindowTitle(title)

        # enable close on ctrl-c
        signal.signal(signal.SIGINT, self.__handler_sigint)
        self.timer = QTimer()
        self.timer.timeout.connect(self.__squelch)
        self.timer.start(100)

    def __squelch(self, *args, **kwargs):
        """
        exists purely to return process control to the python layer, allowing
        signals to be processed and actions to be taken accordingly.
        """
        pass

    def __handler_sigint(self, signal, frame):
        """
        A component of the timed event check used to "gracefully shutdown"
        (kill) the application if the user sends the interrupt signal.

        :param signal: [TODO:description]
        :param frame: [TODO:description]
        """
        print("received interrupt signal")
        self.quit()

    def run(self) -> None:  # pyright: ignore # typing exists to shut up pyright
        """
        A conveniece function with launches the Qt GUI and displays the window
        simultaneously.
        """
        self.panel.show()
        sys.exit(self.exec())


class AppMain(AppBase):
    """
    A wrapper around QApplication which provides several creature comforts.
    Serves as a root node for any qtviewer GUI.
    """

    data_displays: List[AbstractStatefulPane]
    data_controls: List[AbstractControlWidget]

    def __init__(self, title="") -> None:
        super().__init__(title=title)
        self.data_controls = []
        self.data_displays = []

    def __enchain_global(self, pane: QWidget):
        pane_type = type(pane)
        if issubclass(pane_type, AbstractStatefulPane):
            s_pane: AbstractStatefulPane = pane  # pyright: ignore
            for x in self.data_controls:
                s_pane.enchain(x)
            self.data_displays.append(s_pane)

        if issubclass(pane_type, AbstractControlWidget):
            s_widget: AbstractControlWidget = pane  # pyright: ignore
            for x in self.data_displays:
                x.enchain(s_widget)
            self.data_controls.append(s_widget)

    def add_panes(self, *panes: QWidget):
        """
        Add the provided pane to the GUI window layout.
        Override in inheriting classes if different behavior is desired.

        :param panes: [TODO:description]
        """

        for x in panes:
            self.panel.addWidget(x)
            self.panel.nextRow()
            self.__enchain_global(x)

    def add_mosaic(self, mosaic: List[List[QWidget]]):
        assert type(mosaic) == list
        assert len(mosaic) != 0 and type(mosaic[0]) == list

        for row in mosaic:
            hbox = QHBoxLayout()
            wrapper = QWidget()
            wrapper.setLayout(hbox)
            for element in row:
                hbox.addWidget(element)
                self.__enchain_global(element)
            self.panel.addWidget(wrapper)
            self.panel.nextRow()

    def run(self):
        # TODO/FIX: should all panes solely use global state, then this results
        # in many unnecessary re-renders on start up. not a major issue for now.
        for x in self.data_displays:
            x.force_flush()
        super().run()


class VisionViewer(AppMain):
    """
    An image data focused viewer. At the time of writing, there are no true
    differences between this class and the parent. Instead, it exists for the
    event more custom changes are needed, reducing future code duplication.
    """

    def __init__(self, title="CV Image Viewer") -> None:
        super().__init__(title=title)


class PlotViewer(AppMain):
    """
    Another superficial class that may exist only temporarily.
    """

    def __init__(self, title="Plot Viewer") -> None:
        super().__init__(title=title)
