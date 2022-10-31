#! /usr/bin/env python

import sys

from . import config
from .handler import InterSubsHandler
from .mpv_intersubs import MPVInterSubs
from .popup import Popup

from .qt import (
    QApplication,
    QColor,
    QFont,
    QFrame,
    QHBoxLayout,
    QMargins,
    QMouseEvent,
    QPainter,
    QPen,
    QPoint,
    QRect,
    QSize,
    Qt,
    QTextCursor,
    QTextEdit,
    QVBoxLayout,
    pyqtSignal,
)


class SubtitleWidget(QTextEdit):
    def __init__(self, parent: "ParentFrame", mpv, handler: InterSubsHandler):
        super().__init__(parent=parent)
        self.parent_frame = parent
        self.mpv = mpv
        self.handler = handler

        self.setMouseTracking(True)
        self.setReadOnly(True)
        self.setCursorWidth(0)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        self.document().setDocumentMargin(0)
        self.setContentsMargins(0, 0, 0, 0)

        self.verticalScrollBar().setEnabled(False)
        self.horizontalScrollBar().setEnabled(False)

        self.n_lines = 1

        self.text = ""

        self.previous_lookup = ""

        self.pos_parent = QPoint(0, 0)

        self.popup = Popup(self, config, self.handler)
        self.handler.on_popup_created(self.popup)
        self.popup.move(
            self.parent_frame.config.x_screen, self.parent_frame.config.y_screen
        )
        self.popup.resize(600, 500)

        font = self.currentFont()
        font.setPointSize(self.parent_frame.config.default_font_point_size)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.setFont(font)

        self.render_ready = 0

        self.released = True

        # `True` corresponds to the case where there is currently no popup being shown
        self.no_popup = True

        self.transparent_pen = QPen(Qt.GlobalColor.transparent)
        self.outline_pen = QPen(Qt.GlobalColor.black, 8)

        # whether or not the cursor is on the QTextEdit
        self.already_in = False

        # index of the character the mouse is on when popup is to be shown
        self.char_index_popup = -1

        # number of characters to highlight when the popup is shown
        self.length_highlight = 0

    def after_popup_loaded(self):
        self.popup.base_height = 500
        self.popup.base_width = 600
        self.show_popup()

    def show_popup(self):
        if (
            self.already_in
        ):  # it could be that we exited the subtitles before getting there
            # we need this to take into account the zoom setting previously set

            width = (
                self.popup.base_width * (self.parent_frame.config.default_zoom_popup)
                + 5
            )
            height = (
                self.popup.base_height * (self.parent_frame.config.default_zoom_popup)
                + 5
            )

            # the pop up is shown above the subtitles, and it should not exceed the
            # available space there, namely `self.pos_parent.y()`
            height = min(self.pos_parent.y(), height)

            text = self.document().toPlainText()
            char_index = self.char_index_popup
            if char_index < 0 or len(text) <= char_index:
                return
            self.set_text_selection(char_index, char_index + self.length_highlight)

            rect = self.cursorRect(self.textCursor())

            # absolute coordinate of the top left of the current selection
            cursor_top = self.viewport().mapToGlobal(QPoint(rect.left(), rect.top()))

            x_screen = self.parent_frame.config.x_screen
            x_popup = cursor_top.x() - (
                self.fontMetrics().horizontalAdvance(
                    text[char_index : char_index + self.length_highlight]
                )
                + self.fontMetrics().horizontalAdvance(text[char_index]) // 4
                if char_index < len(text)
                else 0
            )

            # make sure we don't go out of the screen
            if x_popup + width >= (x_screen + self.parent_frame.config.screen_width):
                x_popup = x_screen + self.parent_frame.config.screen_width - width

            y_popup = cursor_top.y() - height
            # # This is a workaround to make the poup appear directly above the subs
            # # FIXME: remove this once I understand the code better and find a better way to handle this
            y_popup += 100

            # we need to be careful to never cover the QTextEdit when changing popup
            if self.popup.height() > height:
                self.popup.resize(width, height)
                self.popup.move(x_popup, y_popup)
            else:
                self.popup.move(x_popup, y_popup)
                self.popup.resize(width, height)

            self.popup.show()

        self.no_popup = True

    def mouseMoveEvent(self, event: QMouseEvent):
        char_index = (
            self.document()
            .documentLayout()
            .hitTest(
                event.pos(),
                Qt.HitTestAccuracy.ExactHit,
            )
        )

        text = self.document().toPlainText()
        # print(f"{text=} {char_index=} {self.previous_lookup=}")
        clicked_word = self.handler.lookup_word_from_index(text, char_index)
        # print(f"{clicked_word=}")
        if not clicked_word:
            return
        if (
            clicked_word != self.previous_lookup
            and 0 <= char_index
            and char_index < len(text)
        ):

            self.previous_lookup = clicked_word
            self.setUpdatesEnabled(True)  # we needs updates for highlighting text
            self.no_popup = False  # a popup is likely to be shown, disable highlighting

        if self.handler.on_popup_will_show(self.popup, clicked_word):
            self.char_index_popup = char_index

            # this resize is "needed" as I could so far not set the width of
            # the popup no matter the size of the window. We make it bigger so that
            # the `scrollWidth` value we get later makes sense
            resize_value = (
                self.parent_frame.config.x_screen
                + self.parent_frame.config.screen_width
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
            self.mpv.set_property("pause", True)

        super().enterEvent(event)

    def leaveEvent(self, event):
        pos = self.cursor().pos()
        pos = self.popup.mapFrom(self, pos)
        rect = self.popup.rect().marginsAdded(QMargins(5, 5, 5, 5))
        if not rect.contains(pos):
            self.popup.hide()

        self.mpv.set_property("pause", False)

        self.already_in = False

        self.setUpdatesEnabled(True)

        # reset selection
        self.set_text_selection(0, 0)

        # reset it in case we want to look back at the same position
        self.previous_lookup = ""

        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        char_index = (
            self.document()
            .documentLayout()
            .hitTest(
                event.pos(),
                Qt.HitTestAccuracy.ExactHit,
            )
        )

        self.handler.on_sub_clicked(self.document().toPlainText(), char_index)

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
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(cursor)


class ParentFrame(QFrame):
    update_subtitles = pyqtSignal(bool, str)

    def __init__(self, config, mpv: MPVInterSubs, handler: InterSubsHandler):
        super().__init__()
        self.config = config
        self.mpv = mpv
        self.handler = handler

        self.setWindowFlag(Qt.WindowType.X11BypassWindowManagerHint, True)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
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
        self.stretch_pixels = 1

        self.update_subtitles.connect(self.render_subtitles)
        self._listen_to_subtitle_change()
        self._listen_to_focus_state()

    def _listen_to_subtitle_change(self):
        def on_sub_text_changed(message):
            if isinstance(message, dict):
                return
            else:
                subs = message
            to_hide = not subs
            self.update_subtitles.emit(to_hide, subs)

        self.mpv.register_property_callback("sub-text", on_sub_text_changed)

    def _listen_to_focus_state(self):
        def on_focused_change(focused):
            if not self.subtext.popup.hasFocus():
                try:
                    subs = self.mpv.get_property("sub-text")
                except:
                    subs = ""
                self.update_subtitles.emit(not focused, subs)

        self.mpv.register_property_callback("focused", on_focused_change)

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

        self.subtext.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )  # this should be before .show()
        self.show()

        subs2 = text

        subs2 = subs2.split("\n")
        for i in range(len(subs2)):
            subs2[i] = subs2[i].strip()
            subs2[i] = " " + subs2[i] + " "

        subs2 = "\n".join(subs2)

        self.subtext.len_text = len(subs2)
        self.subtext.text = subs2
        max_sub_line_words = self.config.max_sub_line_words
        split_text = []
        for i, line in enumerate(subs2.split("\n")):
            words = line.split()
            split_lines = [
                " ".join(words[i : i + 8])
                for i in range(0, len(words), max_sub_line_words)
            ]
            split_text.extend(split_lines)

        self.subtext.split_text = split_text
        self.subtext.n_lines = len(self.subtext.split_text)

        # the longest line is not necessarily the one with the most characters
        # as we may use non-monospace fonts
        width_subtext = 0
        for line in self.subtext.split_text:
            width_subtext = max(
                width_subtext,
                self.subtext.fontMetrics()
                .boundingRect(QRect(), Qt.AlignmentFlag.AlignCenter, line)
                .width()
                + 4,
            )

        height_subtext = self.subtext.fontMetrics().height() * self.subtext.n_lines + 4

        mpv_width = self.mpv.get_property("osd-width") * (
            self.mpv.get_property("osd-bar-w") / 100
        )
        width = width_subtext if width_subtext < mpv_width else mpv_width
        height = height_subtext + self.stretch_pixels

        x = (self.config.screen_width / 2) - (width / 2)
        y = self.config.screen_height - height - config.bottom_spacing_pixels

        self.setGeometry(
            config.x_screen + int(x), config.y_screen + int(y), width, height
        )

        self.subtext.setGeometry(
            0, self.stretch_pixels // 2, width_subtext, height_subtext
        )

        for line in self.subtext.split_text:
            self.subtext.append(line)

        self.subtext.pos_parent = self.pos()

        self.subtext.render_ready += 1

    def paintEvent(self, event):
        if self.subtext.render_ready >= 1:
            p = QPainter(self)
            p.fillRect(event.rect(), QColor(0, 0, 0, 128))

        super().paintEvent(event)


def run(paths, app=None, mpv=None, handler=None) -> None:
    if not paths:
        return
    is_external_app = bool(app)
    if not app:
        app = QApplication(sys.argv)
    if not mpv:
        mpv = MPVInterSubs()
    # mpv.debug = True
    mpv.set_property("script-opts", "osc-deadzonesize=1")

    config.screen_width = app.screens()[config.n_screen].size().width()
    config.screen_height = app.screens()[config.n_screen].size().height()
    config.x_screen = app.screens()[config.n_screen].geometry().x()
    config.y_screen = app.screens()[config.n_screen].geometry().y()

    def on_file_loaded(message) -> None:
        mpv.start_intersubs()

    def on_end_file(message) -> None:
        if message["reason"] in ("quit", "stop"):
            frame.deleteLater()
            # Fix an issue where the subtitle widget gets stuck when intersubs is used with an external app
            app.processEvents()
            if not is_external_app:
                app.exit()
            handler.on_shutdown()

    mpv.register_callback("file-loaded", on_file_loaded)
    mpv.register_callback("end-file", on_end_file)
    # FIXME: the shutdown event is apparently not always received by programs using the JSON IPC
    # mpv.register_callback("shutdown", on_shutdown)
    for path in paths:
        mpv.command("loadfile", path, "append-play")
    if not handler:
        handler = InterSubsHandler(mpv)
    frame = ParentFrame(config, mpv, handler)
    if not is_external_app:
        app.exec()


def main() -> None:
    paths = [sys.argv[1]] if len(sys.argv) >= 2 else []
    run(paths)


if __name__ == "__main__":
    main()
