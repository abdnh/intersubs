import math
import os

from PyQt5 import QtWebEngineWidgets
from PyQt5.QtCore import Qt

from .handler import InterSubsHandler


class Popup(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent, handler: InterSubsHandler):
        super(QtWebEngineWidgets.QWebEngineView, self).__init__()
        self.handler = handler
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowOpacity(1)
        self.setStyleSheet("QWidget{background: #000000}")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.WindowType.Tool, True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        self.setMaximumHeight(400)
        self.setMaximumWidth(400)

        self.setWindowFlag(Qt.X11BypassWindowManagerHint, True)

        self.zoom_rate = parent.parent.config.default_zoom_popup
        self.setZoomFactor(self.zoom_rate)

        # used for rounding when rezooming
        self.last_round = 1

        # used to keep track of zoom changes
        self.zoom_timed = 0

        # this record the vertical scrolling in the popup
        self.scroll_y = 0

    # def change_zoom(self, event):
    #     # Ctrl+Alt+"+" or Ctrl+Alt+"-" for zooming
    #     if (event.modifiers() & Qt.ControlModifier) and (
    #         event.modifiers() & Qt.AltModifier
    #     ):
    #         proceed_zooming = False
    #         if event.key() == Qt.Key_Up and self.zoom_rate < 2:
    #             proceed_zooming = True
    #             up_or_down = 1

    #         if event.key() == Qt.Key_Down and self.zoom_rate > 0.3:
    #             proceed_zooming = True
    #             up_or_down = -1

    #         if proceed_zooming is True:
    #             self.zoom_rate = self.zoom_rate + up_or_down * 0.05
    #             self.zoom_timed = self.zoom_timed + up_or_down

    #             self.setZoomFactor(self.zoom_rate)

    #             new_width = self.width() + up_or_down * self.base_width * 0.05
    #             new_height = self.height() + up_or_down * self.base_height * 0.05

    #             new_width_int, new_height_int = self.round_up_down(
    #                 new_width, new_height
    #             )

    #             self.move(
    #                 self.pos().x(), self.pos().y() + self.height() - new_height_int
    #             )

    #             self.resize(new_width_int, new_height_int)


# # this function is needed because depending on the rounding we apply and if the zoom
# # is changed many times, we may encounter unexpected position / size.
# def round_up_down(self, x, y):
#     if self.last_round == -1:
#         self.last_round = 1
#         return math.ceil(x), math.ceil(y)
#     else:
#         self.last_round = -1
#         return math.floor(x), math.floor(y)
