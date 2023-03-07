# Credit: Adapted from aqt.taskman in Anki

from __future__ import annotations

from concurrent.futures.thread import ThreadPoolExecutor
from threading import Lock
from typing import Callable

from .qt import *


Closure = Callable[[], None]


class TaskManager(QObject):
    _closures_pending = pyqtSignal()

    def __init__(self) -> None:
        QObject.__init__(self)
        self._executor = ThreadPoolExecutor()
        self._closures: list[Closure] = []
        self._closures_lock = Lock()
        self._closures_pending.connect(self._on_closures_pending)

    def run_on_main(self, closure: Closure) -> None:
        with self._closures_lock:
            self._closures.append(closure)
        self._closures_pending.emit()  # type: ignore

    def _on_closures_pending(self) -> None:
        with self._closures_lock:
            closures = self._closures
            self._closures = []

        for closure in closures:
            closure()
