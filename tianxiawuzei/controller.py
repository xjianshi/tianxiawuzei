from __future__ import annotations

from enum import Enum

from .config import AppConfig
from .platform import OutputState


class Mode(str, Enum):
    NONE = "none"
    CHARGER = "charger"
    LID = "lid"


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

    def update_config(self, config: AppConfig) -> None:
        if self.mode != Mode.NONE:
            raise RuntimeError("报警监控运行期间不允许修改公共配置")
        self.config = config.normalized()

    def start_charger_mode(self) -> str:
        self._reset_runtime_state()
        self.mode = Mode.CHARGER
        return "充电器报警监控开启中"

    def start_lid_mode(self) -> str:
        self._reset_runtime_state()
        if not self.platform.set_sleep_disabled(1):
            self.mode = Mode.NONE
            raise RuntimeError("无法开启合盖不睡眠，合盖报警模式未启动")
        self.mode = Mode.LID
        return "合盖报警监控开启中"

    def poll_once(self) -> None:
        if self.mode == Mode.CHARGER:
            self._poll_charger()
        elif self.mode == Mode.LID:
            self._poll_lid()

    def close(self, password: str) -> CloseResult:
        if password != self.config.close_password:
            return CloseResult.WRONG_PASSWORD

        was_lid_mode = self.mode == Mode.LID
        self.platform.stop_speech()
        self._restore_speech_output()
        self._reset_runtime_state()
        self.mode = Mode.NONE

        if was_lid_mode and not self.platform.set_sleep_disabled(0):
            return CloseResult.ALARM_STOPPED_SETTINGS_NOT_RESTORED
        return CloseResult.CLOSED

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

    def _poll_charger(self) -> None:
        if self.platform.power_source() == "Battery Power":
            self._speak_alarm()
            self.alarming = True
        else:
            self.platform.stop_speech()
            self._restore_speech_output()
            self.alarming = False

    def _poll_lid(self) -> None:
        if self.platform.lid_closed():
            self._lid_triggered = True
        if self._lid_triggered:
            self._speak_alarm()
            self.alarming = True

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
