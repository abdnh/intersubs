from PyQt6 import QtWebEngineWidgets
from PyQt6.QtCore import Qt

from .handler import InterSubsHandler


class Popup(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent, config, handler: InterSubsHandler):
        super(QtWebEngineWidgets.QWebEngineView, self).__init__(parent=parent)
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
