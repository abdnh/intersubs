#! /usr/bin/env python

import sys
import warnings

from PyQt5.QtCore import (
    QPoint,
    QPointF,
    QRect,
    QSize,
    Qt,
    QUrl,
    pyqtSignal,
)
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QTextCursor
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QTextEdit, QVBoxLayout

from . import config
from .mpv_intersubs import MPVInterSubs
from .popup import Popup
from .handler import InterSubsHandler


class SubtitleWidget(QTextEdit):
    def __init__(self, parent, mpv, handler: InterSubsHandler):
        super().__init__()
        self.mpv = mpv
        self.handler = handler

        self.setMouseTracking(True)
        self.setReadOnly(True)
        self.setCursorWidth(0)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setAlignment(Qt.AlignVCenter)

        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        self.document().setDocumentMargin(0)
        self.setContentsMargins(0, 0, 0, 0)

        self.verticalScrollBar().setEnabled(False)
        self.horizontalScrollBar().setEnabled(False)

        self.n_lines = 1

        self.text = ""

        self.previous_lookup = ""

        self.parent = parent
        self.pos_parent = QPoint(0, 0)

        self.popup = Popup(self, self.handler)
        self.popup.move(self.parent.config.x_screen, self.parent.config.y_screen)
        self.popup.resize(500, 400)

        font = self.currentFont()
        font.setPointSize(self.parent.config.default_font_point_size)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.setFont(font)

        self.render_ready = 0

        self.released = True

        # `True` corresponds to the case where there is currently no popup being shown
        self.no_popup = True

        self.transparent_pen = QPen(Qt.transparent)
        self.outline_pen = QPen(Qt.black, 8)

        # whether or not the cursor is on the QTextEdit
        self.already_in = False

        # index of the character the mouse is on when popup is to be shown
        self.char_index_popup = -1

        # number of characters to highlight when the popup is shown
        self.length_highlight = 0

        self.popup.load(QUrl.fromLocalFile(self.handler.get_popup_html_path()))

        # set to True when a warning message to show only once has been shown
        self.warning_message_unique_shown = False

    def after_popup_loaded(self):
        self.popup.page().runJavaScript(
            """
                    try {
                    document.body.scrollWidth;
                    }
                    catch(err) {
                        err.message;
                    }
                    """,
            self.callback_popup_width,
        )

        self.popup.page().runJavaScript(
            """
                    try {
                    document.body.scrollHeight;
                    }
                    catch(err) {
                        err.message;
                    }
                    """,
            self.callback_popup_height,
        )

        self.handler.on_popup_shown(self.popup, self.previous_lookup)

    def callback_popup_height(self, new_height):
        if new_height != "Cannot read property 'scrollHeight' of null":
            self.popup.base_height = new_height

            self.show_popup()
        else:
            warnings.warn(
                "Popup page loading has failed and this should not happen."
                + " Please fill a bug report if this gets inconvenient.",
                stacklevel=2,
            )

    def callback_popup_width(self, new_width):
        if new_width != "Cannot read property 'scrollHeight' of null":
            self.popup.base_width = new_width
        else:
            warnings.warn(
                "Popup page loading has failed and this should not happen."
                + " Please fill a bug report if this gets inconvenient.",
                stacklevel=2,
            )

    def show_popup(self):
        if (
            self.already_in
        ):  # it could be that we exited the subtitles before getting there
            # we need this to take into account the zoom setting previously set

            width = self.popup.base_width * (self.parent.config.default_zoom_popup) + 5
            height = (
                self.popup.base_height * (self.parent.config.default_zoom_popup) + 5
            )

            # the pop up is shown above the subtitles, and it should not excess the
            # available space there, namely `self.pos_parent.y()`
            height = min(self.pos_parent.y(), height)

            width = int(width)
            height = int(height)

            char_index = self.char_index_popup
            if char_index < 0 or len(self.text) <= char_index:
                return
            self.set_text_selection(char_index, char_index + self.length_highlight)

            rect = self.cursorRect(self.textCursor())

            # absolute coordinate of the top left of the current selection
            cursor_top = self.viewport().mapToGlobal(QPoint(rect.left(), rect.top()))

            x_screen = self.parent.config.x_screen
            x_popup = cursor_top.x() - (
                self.fontMetrics().width(
                    self.text[char_index : char_index + self.length_highlight]
                )
                + self.fontMetrics().width(self.text[char_index]) // 4
                if char_index < len(self.text)
                else 0
            )

            # make sure we don't go out of the screen
            if x_popup + width >= (x_screen + self.parent.config.screen_width):
                x_popup = x_screen + self.parent.config.screen_width - width

            y_popup = max(0, self.pos_parent.y() - height)

            # we need to be careful to never cover the QTextEdit when changing popup
            if self.popup.height() > height:
                self.popup.resize(width, height)
                self.popup.move(x_popup, y_popup)
            else:
                self.popup.move(x_popup, y_popup)
                self.popup.resize(width, height)

            self.popup.show()

        self.no_popup = True

    def mouseMoveEvent(self, event):
        point_position = event.pos()  # this is relative coordinates in the QTextEdit
        char_index = (
            self.document()
            .documentLayout()
            .hitTest(
                QPointF(point_position.x(), point_position.y()),
                Qt.HitTestAccuracy.ExactHit,
            )
        )

        clicked_word = self.handler.lookup_word_from_index(self.text, char_index)
        print(f"{clicked_word=} {self.previous_lookup=}")
        if not clicked_word:
            return
        if (
            clicked_word != self.previous_lookup
            and 0 <= char_index
            and char_index < self.len_text
        ):

            self.previous_lookup = clicked_word
            self.setUpdatesEnabled(True)  # we needs updates for highlighting text
            self.no_popup = False  # a popup is likely to be shown, disable highlighting

        show_popup = True
        if show_popup is True:
            self.char_index_popup = char_index

            # this resize is "needed" as I could so far not set the width of
            # the popup no matter the size of the window. We make it bigger so that
            # the `scrollWidth` value we get later makes sense
            resize_value = (
                self.parent.config.x_screen
                + self.parent.config.screen_width
                - self.popup.pos().x()
            )
            self.popup.resize(resize_value, self.popup.height())

            # this show is needed to record later on the right size of the popup
            # in case it was not shown already
            self.popup.show()
            self.after_popup_loaded()

    def enterEvent(self, event):
        # the case where this event is triggered several times has been encountered,
        # hence the `self.already_in`
        if not self.already_in:
            self.already_in = True
            self.setUpdatesEnabled(True)
            self.previously_paused = self.mpv.get_property("pause")
            self.mpv.set_property("pause", True)

        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.previously_paused:
            self.mpv.set_property("pause", False)

        self.already_in = False

        self.setUpdatesEnabled(True)

        # reset selection
        self.set_text_selection(0, 0)

        # reset it in case we want to look back at the same position
        self.previous_lookup = ""

        # hiding popup in case it was shown
        self.popup.hide()

        super().leaveEvent(event)

    def mousePressEvent(self, event):
        point_position = event.pos()  # this is relative coordinates in the QTextEdit
        char_index = (
            self.document()
            .documentLayout()
            .hitTest(
                QPointF(point_position.x(), point_position.y()),
                Qt.HitTestAccuracy.ExactHit,
            )
        )

        self.handler.on_sub_clicked(self.text, char_index)

        super().mousePressEvent(event)

    # we do not want the context menu to display and steal focus
    def contextMenuEvent(self, event):
        pass

    # def paintEvent(self, event):
    #     # this is just a trick to avoid an infinite loop due to the painting of the
    #     # outline, as the line `my_cursor.select(QTextCursor.SelectionType.Document)`
    #     # triggers a recursive call to `paintEvent`
    #     self.render_ready += 1

    #     if self.render_ready > 3 and self.no_popup:
    #         self.setUpdatesEnabled(False)

    #     # Showing the outline is really slow (at times, more than 100 ms) and
    #     # we do not want to do it when the user shows popups, as it slows everything down.
    #     # Ideally, it could probably be in a separate thread.
    #     if not self.already_in:
    #         painter = QPainter(self.viewport())

    #         my_cursor = self.textCursor()
    #         my_char_format = my_cursor.charFormat()

    #         my_char_format.setTextOutline(self.outline_pen)

    #         my_cursor.select(QTextCursor.SelectionType.Document)
    #         my_cursor.mergeCharFormat(my_char_format)

    #         self.document().drawContents(painter)

    #         my_char_format.setTextOutline(self.transparent_pen)
    #         my_cursor.mergeCharFormat(my_char_format)

    #     super().paintEvent(event)

    def minimumSizeHint(self):
        return QSize(5, 5)

    def set_text_selection(self, start, end):
        cursor = self.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)


class ParentFrame(QFrame):
    update_subtitles = pyqtSignal(bool, str)

    def __init__(self, config, mpv: MPVInterSubs, handler: InterSubsHandler):
        super().__init__()
        self.config = config
        self.mpv = mpv
        self.handler = handler

        self.update_subtitles.connect(self.render_subtitles)
        self._listen_to_subtitle_change()

        self.setWindowFlag(Qt.X11BypassWindowManagerHint, True)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowOpacity(0.6)
        self.setStyleSheet("QWidget{background: #000000}")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowFlag(Qt.WindowType.Tool, True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        self.setStyleSheet(config.style_subs)

        self.subtext = SubtitleWidget(self, self.mpv, self.handler)

        self.subtitles_vbox = QVBoxLayout(self)
        self.subtitles_vbox.addStretch()
        self.v_margin = 0
        self.subtitles_vbox.setContentsMargins(0, self.v_margin, 0, self.v_margin)

        hbox = QHBoxLayout()
        hbox.addWidget(self.subtext)

        self.subtitles_vbox.addLayout(hbox)
        self.subtitles_vbox.addStretch()

        # we add some pixels to the semi-transparent background, up and down
        self.stretch_pixels = 20

    def _listen_to_subtitle_change(self):
        def on_sub_text_changed(message):
            if isinstance(message, dict):
                return
            else:
                subs = message
            print("on_sub_text_changed:", subs)
            # hide subs when mpv isn't in fullscreen
            to_hide = not self.mpv.get_property("fullscreen") or not subs
            self.update_subtitles.emit(to_hide, subs)

        self.mpv.register_property_callback("sub-text", on_sub_text_changed)

    def render_subtitles(self, to_hide, text=""):
        self.subtext.render_ready = 0

        if to_hide or not len(text):
            try:
                self.subtext.clear()
                self.hide()
            finally:
                return

        self.subtext.setUpdatesEnabled(True)
        self.subtext.clear()
        self.repaint()

        self.subtext.setAlignment(Qt.AlignCenter)  # this should be before .show()
        self.show()

        subs2 = text

        subs2 = subs2.split("\n")
        for i in range(len(subs2)):
            subs2[i] = subs2[i].strip()
            subs2[i] = " " + subs2[i] + " "

        subs2 = "\n".join(subs2)

        self.subtext.len_text = len(subs2)
        self.subtext.text = subs2
        self.subtext.text_splitted = subs2.split("\n")
        self.subtext.n_lines = len(self.subtext.text_splitted)

        # the longest line is not necessarily the one with the most characters
        # as we may use non-monospace fonts
        width_subtext = 0
        for line in self.subtext.text_splitted:
            width_subtext = max(
                width_subtext,
                self.subtext.fontMetrics()
                .boundingRect(QRect(), Qt.AlignCenter, line)
                .width()
                + 4,
            )

        height_subtext = self.subtext.fontMetrics().height() * self.subtext.n_lines + 4

        width = width_subtext
        height = height_subtext + self.stretch_pixels

        x = (self.config.screen_width / 2) - (width / 2)
        y = self.config.screen_height - height - config.bottom_spacing_pixels

        self.setGeometry(
            config.x_screen + int(x), config.y_screen + int(y), width, height
        )

        self.subtext.setGeometry(
            0, self.stretch_pixels // 2, width_subtext, height_subtext
        )

        for line in self.subtext.text_splitted:
            self.subtext.append(line)

        self.subtext.pos_parent = self.pos()

        self.subtext.render_ready += 1

    def paintEvent(self, event):
        if self.subtext.render_ready >= 1:
            p = QPainter(self)
            p.fillRect(event.rect(), QColor(0, 0, 0, 128))

        super().paintEvent(event)


def run(path=None, mpv=None, handler=None) -> None:
    app = QApplication(sys.argv)
    if not mpv:
        mpv = MPVInterSubs()
    # mpv.debug = True

    config.screen_width = app.screens()[config.n_screen].size().width()
    config.screen_height = app.screens()[config.n_screen].size().height()
    config.x_screen = app.screens()[config.n_screen].geometry().x()
    config.y_screen = app.screens()[config.n_screen].geometry().y()

    def on_end_file(message) -> None:
        print("on_end_file")
        print(f"{message=}")
        if message["reason"] in ("quit", "stop", "eof"):
            mpv.close()
            sys.exit(app.exit())
        else:
            mpv.stop_intersubs()

    def on_file_loaded(message) -> None:
        print("on_file_loaded")
        mpv.start_intersubs()

    # def on_shutdown():
    #     print("on_shutdown")
    #     app.exit()

    mpv.register_callback("file-loaded", on_file_loaded)
    mpv.register_callback("end-file", on_end_file)
    # FIXME: the shutdown event is apparently never received by programs using the JSON IPC
    # mpv.register_callback("shutdown", on_shutdown)
    if path:
        mpv.command("loadfile", path, "replace", "pause=no")
    if not handler:
        handler = InterSubsHandler(mpv)
    form = ParentFrame(config, mpv, handler)
    app.exec()


def main() -> None:
    path = sys.argv[1] if len(sys.argv) >= 2 else None
    run(path)


if __name__ == "__main__":
    main()
