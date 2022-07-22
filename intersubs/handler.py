from __future__ import annotations
import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .popup import Popup
from .mpv_intersubs import MPVInterSubs


class InterSubsHandler:
    def __init__(self, mpv: MPVInterSubs):
        self.mpv = mpv

    def lookup_word_from_index(self, text: str, idx: int) -> str:
        try:
            lidx = text[: idx + 1].rindex(" ") + 1
        except ValueError:
            lidx = 0
        try:
            ridx = idx + text[idx:].index(" ")
        except ValueError:
            ridx = len(text)
        return text[lidx:ridx]

    def on_sub_clicked(self, text: str, idx: int) -> None:
        word = self.lookup_word_from_index(text, idx)
        self.mpv.command("show-text", word)

    def get_popup_html_path(self) -> str | None:
        return os.path.join(os.path.dirname(__file__), "popup", "index.html")

    def on_popup_shown(self, popup: "Popup", text: str) -> None:
        popup.page().runJavaScript(
            """
            document.body.textContent = %s;
        """
            % json.dumps(text)
        )
