from typing import TYPE_CHECKING

from .qt import QWebEngineView, Qt, QEvent, QEnterEvent

from .handler import InterSubsHandler

if TYPE_CHECKING:
    from .main import SubtitleWidget


class Popup(QWebEngineView):
    def __init__(self, subtext: "SubtitleWidget", config, handler: InterSubsHandler):
        super(QWebEngineView, self).__init__(parent=subtext)
        self.subtext = subtext
        self.handler = handler
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowOpacity(1)
        self.setStyleSheet("QWidget{background: #000000}")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.WindowType.Tool, True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        self.setMaximumHeight(400)
        self.setMaximumWidth(400)

        self.setWindowFlag(Qt.WindowType.X11BypassWindowManagerHint, True)

        self.zoom_rate = config.default_zoom_popup
        self.setZoomFactor(self.zoom_rate)

    def enterEvent(self, event: QEnterEvent) -> None:
        self.show()
        self.subtext.mpv.set_property("pause", True)
        return super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.hide()
        self.subtext.mpv.set_property("pause", False)
        return super().leaveEvent(event)
