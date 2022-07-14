from typing import Any
from mpv import MPV


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
        return self.get_property("sub") == "no" or self.get_property("sub") == "auto"

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
        self.set_property("fullscreen", True)
        self.hide_native_subs()

        # mp.register_event("shutdown", stop_intersub)
        # is_running = true
        # self.register_callback("shutdown", self.stop_intersub)
        return True

    # def stop_intersub(self) -> None:
    #     print('stop_intersub')
    #     self.command('show-text', 'Quitting interSubs...')
    #     # os.execute(put_cmd_in_bg("pkill -f "..mpv_socket_file_path))
    #     # destroy_mpv_socket_file()
    #     # destroy_subs_file()
    #     self.restore_subs_settings()
    #     self.unregister_callback("shutdown", self.stop_intersub)
    #     # is_running = false

    # def on_shutdown(self):
    #     print('on_shutdown')
    #     try:
    #         self.close()
    #     except Exception:
    #         # Ignore pywintypes.error: (232, 'WriteFile', 'The pipe is being closed.')
    #         pass
