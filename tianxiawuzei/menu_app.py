from __future__ import annotations

import threading
import time
import webbrowser
from dataclasses import replace
from datetime import datetime

try:
    import rumps
except ImportError:  # pragma: no cover - exercised by users without dependency.
    rumps = None

from .config import ConfigStore, default_config_path
from .controller import AlarmController, CloseResult, Mode
from .menu_state import menu_title_for_mode, scenario_hint_text, status_text_for_mode
from .platform import MacPlatform
from .support import feedback_mailto, usage_text


BaseApp = rumps.App if rumps is not None else object


class TianxiawuzeiApp(BaseApp):
    def __init__(self):
        if rumps is None:
            raise RuntimeError("缺少依赖 rumps")
        self.store = ConfigStore(default_config_path())
        self.config = self.store.load()
        self.controller = AlarmController(MacPlatform(), self.config)
        self.worker: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.lock = threading.RLock()
        self.last_power_source = None
        self.last_lid_state = None

        super().__init__("天下无贼", title=menu_title_for_mode(Mode.NONE), quit_button=None)
        self.name_item = rumps.MenuItem("天下无贼")
        self.scenario_hint_item = rumps.MenuItem(scenario_hint_text(self.config.language))
        self.status_item = rumps.MenuItem(status_text_for_mode(Mode.NONE, False, self.config.language))
        self.start_charger_item = rumps.MenuItem("", callback=self.start_charger)
        self.start_lid_item = rumps.MenuItem("", callback=self.start_lid)
        self.close_item = rumps.MenuItem("", callback=self.close_current)
        self.set_volume_item = rumps.MenuItem("", callback=self.set_alarm_volume)
        self.set_text_item = rumps.MenuItem("", callback=self.set_alarm_text)
        self.set_password_item = rumps.MenuItem("", callback=self.set_close_password)
        self.preview_item = rumps.MenuItem("", callback=self.preview_voice)
        self.language_item = rumps.MenuItem("")
        self.language_zh_item = rumps.MenuItem("", callback=self.set_language_zh)
        self.language_en_item = rumps.MenuItem("", callback=self.set_language_en)
        self.language_item.add(self.language_zh_item)
        self.language_item.add(self.language_en_item)
        self.usage_item = rumps.MenuItem("", callback=self.show_usage)
        self.feedback_item = rumps.MenuItem("", callback=self.send_feedback)
        self.quit_item = rumps.MenuItem("", callback=self.quit_app)
        self.menu = [
            self.name_item,
            self.scenario_hint_item,
            self.status_item,
            None,
            self.start_charger_item,
            self.start_lid_item,
            self.close_item,
            None,
            self.set_volume_item,
            self.set_text_item,
            self.set_password_item,
            self.preview_item,
            None,
            self.language_item,
            None,
            self.usage_item,
            self.feedback_item,
            None,
            self.quit_item,
        ]
        self._refresh_menu_text()

    def start_charger(self, _):
        self._log("start charger requested")
        if not self._close_existing_if_needed():
            self._log("start charger canceled while closing existing monitor")
            return
        with self.lock:
            message = self.controller.start_charger_mode()
            self.last_power_source = None
            self.last_lid_state = None
            self._start_worker()
            self._set_status(message)
            self._sync_menu_title()
            self._log(message)
        rumps.notification("天下无贼", message, "拔电源将触发报警。")

    def start_lid(self, _):
        self._log("start lid requested")
        if not self._close_existing_if_needed():
            self._log("start lid canceled while closing existing monitor")
            return
        with self.lock:
            try:
                message = self.controller.start_lid_mode()
            except RuntimeError as exc:
                self._log(f"start lid failed: {exc}")
                rumps.alert(str(exc))
                return
            self.last_power_source = None
            self.last_lid_state = None
            self._start_worker()
            self._set_status(message)
            self._sync_menu_title()
            self._log(message)
        rumps.notification("天下无贼", message, "合盖后报警会持续，直到验证关闭密码。")

    def close_current(self, _):
        self._close_with_password("关闭当前报警模式")

    def set_alarm_volume(self, _):
        if not self._ensure_can_change_config():
            return
        response = rumps.Window(
            message=self._t("请输入报警音量，范围 0-100。", "Enter alarm volume, 0-100."),
            title=self._t("设置报警音量", "Set Alarm Volume"),
            default_text=str(self.config.alarm_volume),
            ok=self._t("保存", "Save"),
            cancel=self._t("取消", "Cancel"),
        ).run()
        if not response.clicked:
            return
        try:
            volume = int(response.text.strip())
        except ValueError:
            rumps.alert(self._t("音量必须是数字。", "Volume must be a number."))
            return
        self._save_config(replace(self.config, alarm_volume=volume))

    def set_alarm_text(self, _):
        if not self._ensure_can_change_config():
            return
        response = rumps.Window(
            message=self._t("请输入报警播报词汇。", "Enter alarm speech text."),
            title=self._t("设置报警词汇", "Set Alarm Text"),
            default_text=self.config.alarm_text,
            ok=self._t("保存", "Save"),
            cancel=self._t("取消", "Cancel"),
        ).run()
        if response.clicked:
            self._save_config(replace(self.config, alarm_text=response.text.strip()))

    def set_close_password(self, _):
        if not self._ensure_can_change_config():
            return
        response = rumps.Window(
            message=self._t("请输入新的关闭密码。", "Enter the new close password."),
            title=self._t("设置关闭密码", "Set Close Password"),
            default_text="",
            ok=self._t("保存", "Save"),
            cancel=self._t("取消", "Cancel"),
            dimensions=(240, 24),
            secure=True,
        ).run()
        if response.clicked:
            self._save_config(replace(self.config, close_password=response.text.strip()))

    def preview_voice(self, _):
        if not self._ensure_can_change_config():
            return
        self.controller.platform.set_output(self.config.alarm_volume, False)
        self.controller.platform.speak(self.config.voice, self.config.speech_rate, self.config.alarm_text)
        self.controller.platform.set_output(0, True)

    def show_usage(self, _):
        rumps.alert(title=self._t("天下无贼使用说明", "Tianxiawuzei Help"), message=usage_text(self.config.language))

    def send_feedback(self, _):
        webbrowser.open(feedback_mailto(self.config.language))

    def set_language_zh(self, _):
        self._save_config(replace(self.config, language="zh"))
        self._refresh_menu_text()

    def set_language_en(self, _):
        self._save_config(replace(self.config, language="en"))
        self._refresh_menu_text()

    def quit_app(self, _):
        if self.controller.mode != Mode.NONE:
            if not self._close_with_password("退出前关闭报警监控"):
                return
        rumps.quit_application()

    def _close_existing_if_needed(self) -> bool:
        if self.controller.mode == Mode.NONE:
            return True
        return self._close_with_password("已有报警监控运行，开启新模式前需要关闭旧监控")

    def _close_with_password(self, title: str) -> bool:
        response = rumps.Window(
            message=self._t("请输入关闭密码。", "Enter close password."),
            title=title,
            default_text="",
            ok=self._t("确认", "Confirm"),
            cancel=self._t("取消", "Cancel"),
            dimensions=(240, 24),
            secure=True,
        ).run()
        if not response.clicked:
            return False
        with self.lock:
            result = self.controller.close(response.text.strip())
            if result == CloseResult.WRONG_PASSWORD:
                self._log("close rejected: wrong close password")
                rumps.alert(self._t("关闭密码错误，报警和监控不会停止。", "Wrong close password. Alarm and monitoring will continue."))
                return False
            self.stop_event.set()
            if self.worker and self.worker.is_alive():
                self.worker.join(timeout=1.5)
            self.stop_event.clear()
            self._set_status("状态：未开启")
            self._sync_menu_title()
            self._log(f"monitor closed: {result.value}")
        if result == CloseResult.ALARM_STOPPED_SETTINGS_NOT_RESTORED:
            rumps.alert(self._t("报警已停，但系统设置尚未恢复。请手动检查 SleepDisabled。", "Alarm stopped, but system settings were not restored. Please check SleepDisabled manually."))
        else:
            rumps.notification("天下无贼", self._t("报警监控已关闭", "Alarm Monitoring Closed"), self._t("音量已归零并静音。", "Volume has been muted."))
        return True

    def _ensure_can_change_config(self) -> bool:
        if self.controller.mode != Mode.NONE:
            rumps.alert(self._t("报警监控运行期间不允许修改公共配置。请先验证关闭密码并关闭监控。", "Public settings cannot be changed while monitoring is active. Close monitoring with the close password first."))
            return False
        return True

    def _save_config(self, config) -> None:
        self.config = config.normalized()
        self.store.save(self.config)
        self.controller.update_config(self.config)
        rumps.notification("天下无贼", self._t("配置已保存", "Settings Saved"), self._t("新配置会影响两种报警模式。", "New settings apply to both alarm modes."))

    def _start_worker(self) -> None:
        self.stop_event.set()
        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=1.5)
        self.stop_event.clear()
        self.worker = threading.Thread(target=self._poll_loop, daemon=True)
        self.worker.start()

    def _poll_loop(self) -> None:
        while not self.stop_event.is_set():
            with self.lock:
                self._log_state_if_changed()
                self.controller.poll_once()
                self._set_status(status_text_for_mode(self.controller.mode, self.controller.alarming, self.config.language))
                if self.controller.alarming:
                    self._log("alarm active")
            time.sleep(0.5)

    def _set_status(self, text: str) -> None:
        self.status_item.title = text

    def _sync_menu_title(self) -> None:
        self.title = menu_title_for_mode(self.controller.mode)

    def _refresh_menu_text(self) -> None:
        self.scenario_hint_item.title = scenario_hint_text(self.config.language)
        self.status_item.title = status_text_for_mode(self.controller.mode, self.controller.alarming, self.config.language)
        self.start_charger_item.title = self._t("开启充电器报警模式", "Start Charger Alarm Mode")
        self.start_lid_item.title = self._t("开启合盖报警模式", "Start Lid Alarm Mode")
        self.close_item.title = self._t("关闭当前报警模式", "Close Current Alarm Mode")
        self.set_volume_item.title = self._t("设置报警音量", "Set Alarm Volume")
        self.set_text_item.title = self._t("设置报警词汇", "Set Alarm Text")
        self.set_password_item.title = self._t("设置关闭密码", "Set Close Password")
        self.preview_item.title = self._t("试听报警语音", "Preview Alarm Voice")
        self.language_item.title = self._t("语言 / Language", "Language / 语言")
        self.language_zh_item.title = self._t("中文 ✓", "中文")
        self.language_en_item.title = self._t("English", "English ✓")
        self.usage_item.title = self._t("使用说明", "Help")
        self.feedback_item.title = self._t("反馈建议", "Feedback")
        self.quit_item.title = self._t("退出", "Quit")

    def _t(self, zh: str, en: str) -> str:
        return en if self.config.language == "en" else zh

    def _log_state_if_changed(self) -> None:
        if self.controller.mode == Mode.CHARGER:
            source = self.controller.platform.power_source()
            if source != self.last_power_source:
                self.last_power_source = source
                self._log(f"power source: {source}")
        elif self.controller.mode == Mode.LID:
            closed = self.controller.platform.lid_closed()
            if closed != self.last_lid_state:
                self.last_lid_state = closed
                self._log(f"lid closed: {closed}")

    def _log(self, message: str) -> None:
        log_path = default_config_path().parent / "app.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with log_path.open("a", encoding="utf-8") as file:
            file.write(f"{stamp} {message}\n")


def main() -> None:
    if rumps is None:
        raise SystemExit("缺少依赖 rumps。请先运行：python3 -m pip install -r requirements.txt")
    TianxiawuzeiApp().run()


if __name__ == "__main__":
    main()
