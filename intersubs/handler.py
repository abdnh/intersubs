from __future__ import annotations
import json
import os
from typing import TYPE_CHECKING

from PyQt6.QtCore import QUrl

if TYPE_CHECKING:
    from .popup import Popup
from .mpv_intersubs import MPVInterSubs


class InterSubsHandler:
    def __init__(self, mpv: MPVInterSubs):
        self.mpv = mpv

    def lookup_word_from_index(self, text: str, idx: int) -> str:
        if idx >= len(text):
            return ""
        seps = [" ", "\t", "\n"]
        lidx = 0
        for i in range(idx, -1, -1):
            if text[i] in seps:
                lidx = i
                break
        ridx = len(text)
        for i in range(idx, len(text)):
            if text[i] in seps:
                ridx = i
                break
        return text[lidx:ridx]

    def on_sub_clicked(self, text: str, idx: int) -> None:
        word = self.lookup_word_from_index(text, idx)
        self.mpv.command("show-text", word)

    def on_popup_created(self, popup: Popup) -> None:
        popup.load(
            QUrl.fromLocalFile(
                os.path.join(os.path.dirname(__file__), "popup", "index.html")
            )
        )

    def on_popup_will_show(self, popup: Popup, text: str) -> bool:
        popup.page().runJavaScript(
            """
            document.body.textContent = %s;
        """
            % json.dumps(text)
        )
        return True
