from typing import Any

from .mpv import MPV


class MPVInterSubs(MPV):
    default_argv = MPV.default_argv + ["--no-config"]

    def __init__(self):
        super().__init__()
        self.saved_sub_settings = {}

    def get_property_or_default(self, name, default=None) -> Any:
        value = super().get_property(name)
        if not value and default is not None:
            return default
        return value

    def no_selected_sub(self) -> bool:
        sub = self.get_property("sub")
        return sub in ("no", "auto")

    def save_current_subs_settings(self) -> None:

        self.saved_sub_settings["sub-visibility"] = self.get_property("sub-visibility")
        self.saved_sub_settings["sub-color"] = self.get_property_or_default(
            "sub-color", "1/1/1/1"
        )
        self.saved_sub_settings["sub-border-color"] = self.get_property_or_default(
            "sub-border-color", "0/0/0/1"
        )
        self.saved_sub_settings["sub-shadow-color"] = self.get_property_or_default(
            "sub-shadow-color", "0/0/0/1"
        )

    def restore_subs_settings(self) -> None:
        for key, value in getattr(self, "saved_sub_settings", {}).items():
            self.command("set_property", key, value)

    def hide_native_subs(self) -> None:
        self.set_property("sub-color", "0/0/0/0")
        self.set_property("sub-border-color", "0/0/0/0")
        self.set_property("sub-shadow-color", "0/0/0/0")

    def start_intersubs(self) -> bool:
        if self.no_selected_sub():
            self.command("show-text", "Select subtitles before starting interSubs.")
            return False

        self.command("show-text", "Starting interSubs...")

        self.save_current_subs_settings()
        self.set_property("sub-visibility", "yes")
        self.set_property("sub-ass-override", "force")
        self.hide_native_subs()
        return True

    def stop_intersubs(self) -> None:
        self.command("show-text", "Quitting interSubs...")
        self.restore_subs_settings()
