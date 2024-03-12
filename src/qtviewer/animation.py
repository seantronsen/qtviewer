from PySide6.QtCore import QTimer
from qtviewer.panels import AbstractStatefulPane
import numpy as np


class Animator:
    animation_content: AbstractStatefulPane
    timer: QTimer
    animation_tick: np.uintp

    def __init__(
        self,
        fps: float,
        contents: AbstractStatefulPane,
    ) -> None:
        assert not fps <= 0
        super().__init__()
        self.animation_content = contents
        self.animation_content.pane_state.onUpdate = self.update
        self.animation_tick = np.uintp(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_tick)
        self.timer.start(int(1000 / fps))

    def __getattr__(self, name):
        return getattr(self.animation_content, name)

    def on_tick(self):
        """
        Exists to provide a timed update feature for animation / sequence data
        where new frames should be delivered at the specified interval.
        """
        self.animation_tick += np.uintp(1)
        self.animation_content.force_flush()

    def update(self, **kwargs):
        """
        This function is the callback provided to the State instance and is
        executed on each state change. The user specified callback is executed
        by this callback. If you wish to exist in user land, don't worry about
        anything other than the one callback you're required to define.
        """

        self.animation_content.update(animation_tick=self.animation_tick, **kwargs)
