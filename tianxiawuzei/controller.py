from __future__ import annotations

from enum import Enum

from .config import AppConfig
from .platform import OutputState


class Mode(str, Enum):
    NONE = "none"
    COMPUTER = "computer"


class CloseResult(str, Enum):
    CLOSED = "closed"
    WRONG_PASSWORD = "wrong_password"
    ALARM_STOPPED_SETTINGS_NOT_RESTORED = "alarm_stopped_settings_not_restored"


class AlarmController:
    def __init__(self, platform, config: AppConfig):
        self.platform = platform
        self.config = config.normalized()
        self.mode = Mode.NONE
        self.alarming = False
        self._lid_triggered = False
        self._speech_output_before_alarm: OutputState | None = None
        self.sleep_restore_pending = False
        self._sleep_disabled_changed_by_app = False

    def update_config(self, config: AppConfig) -> None:
        if self.mode != Mode.NONE:
            raise RuntimeError("报警监控运行期间不允许修改公共配置")
        self.config = config.normalized()

    def start_computer_monitor(self) -> str:
        if self.sleep_restore_pending and not self.restore_sleep_disabled():
            raise RuntimeError("系统休眠设置尚未恢复，请先恢复 SleepDisabled 后再开启电脑监控")
        self._reset_runtime_state()
        if self._current_sleep_disabled() == 1:
            self._sleep_disabled_changed_by_app = False
        elif not self.platform.set_sleep_disabled(1):
            self.mode = Mode.NONE
            raise RuntimeError("无法开启合盖不睡眠，电脑监控未启动")
        else:
            self._sleep_disabled_changed_by_app = True
        self.sleep_restore_pending = False
        self.mode = Mode.COMPUTER
        return "电脑监控开启中"

    def poll_once(self) -> None:
        if self.mode == Mode.COMPUTER:
            self._poll_computer()

    def close(self, password: str) -> CloseResult:
        if password != self.config.close_password:
            return CloseResult.WRONG_PASSWORD

        needs_sleep_restore = self.mode == Mode.COMPUTER and self._sleep_disabled_changed_by_app
        self.platform.stop_speech()
        self._restore_speech_output()
        self._reset_runtime_state()
        self.mode = Mode.NONE

        if needs_sleep_restore and not self.restore_sleep_disabled():
            self.sleep_restore_pending = True
            return CloseResult.ALARM_STOPPED_SETTINGS_NOT_RESTORED
        return CloseResult.CLOSED

    def restore_sleep_disabled(self) -> bool:
        if self.platform.set_sleep_disabled(0):
            self.sleep_restore_pending = False
            self._sleep_disabled_changed_by_app = False
            return True
        self.sleep_restore_pending = True
        return False

    def _current_sleep_disabled(self) -> int:
        sleep_disabled = getattr(self.platform, "sleep_disabled", -1)
        if callable(sleep_disabled):
            return sleep_disabled()
        return sleep_disabled

    def preview_voice(self) -> None:
        if self.mode != Mode.NONE:
            raise RuntimeError("报警监控运行期间不允许试听报警语音")
        self._remember_speech_output()
        self.platform.set_output(self.config.alarm_volume, False)
        try:
            self.platform.speak(
                self.config.voice,
                self.config.speech_rate,
                self.config.alarm_text,
                wait=True,
            )
        finally:
            self._restore_speech_output()

    def _poll_computer(self) -> None:
        if self.platform.lid_closed():
            self._lid_triggered = True

        charger_triggered = self.platform.power_source() == "Battery Power"
        if charger_triggered or self._lid_triggered:
            self._speak_alarm()
            self.alarming = True
        else:
            self.platform.stop_speech()
            self._restore_speech_output()
            self.alarming = False

    def _speak_alarm(self) -> None:
        self._remember_speech_output()
        self.platform.set_output(self.config.alarm_volume, False)
        if not self.platform.is_speaking():
            self.platform.speak(self.config.voice, self.config.speech_rate, self.config.alarm_text)

    def _remember_speech_output(self) -> None:
        if self._speech_output_before_alarm is None:
            self._speech_output_before_alarm = self.platform.output_state()

    def _restore_speech_output(self) -> None:
        if self._speech_output_before_alarm is None:
            return
        previous_output = self._speech_output_before_alarm
        self._speech_output_before_alarm = None
        self.platform.set_output(previous_output.volume, previous_output.muted)

    def _reset_runtime_state(self) -> None:
        self.alarming = False
        self._lid_triggered = False
        self._speech_output_before_alarm = None
