from __future__ import annotations

import subprocess
from dataclasses import dataclass, field


class MacPlatform:
    def run(self, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(args, check=check, text=True, capture_output=True)

    def shell(self, script: str, *, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["/bin/zsh", "-lc", script], check=check, text=True, capture_output=True)

    def power_source(self) -> str:
        result = self.shell("pmset -g ps | sed -n '1p'")
        if "Battery Power" in result.stdout:
            return "Battery Power"
        return "AC Power"

    def lid_closed(self) -> bool:
        result = self.shell(
            "ioreg -r -k AppleClamshellState -d 4 | "
            "awk -F'= ' '/AppleClamshellState/ {print $2; exit}'"
        )
        return result.stdout.strip() == "Yes"

    def set_output(self, volume: int, muted: bool) -> None:
        mute_clause = "with output muted" if muted else "without output muted"
        self.run(
            [
                "osascript",
                "-e",
                f"set volume output volume {volume}",
                "-e",
                f"set volume alert volume {volume}",
                "-e",
                f"set volume {mute_clause}",
            ]
        )

    def speak(self, voice: str, rate: int, text: str) -> None:
        subprocess.Popen(["say", "-v", voice, "-r", str(rate), text])

    def is_speaking(self) -> bool:
        result = self.shell("pgrep -x say >/dev/null 2>&1", check=False)
        return result.returncode == 0

    def stop_speech(self) -> None:
        self.shell("pkill -x say >/dev/null 2>&1 || true")

    def set_sleep_disabled(self, value: int) -> bool:
        command = f"pmset -a disablesleep {value}"
        result = self.run(
            [
                "osascript",
                "-e",
                f'do shell script "{command}" with administrator privileges',
            ],
            check=False,
        )
        return result.returncode == 0

    def sleep_disabled(self) -> int:
        result = self.shell("pmset -g | awk '/SleepDisabled/ {print $2; exit}'", check=False)
        try:
            return int(result.stdout.strip())
        except ValueError:
            return -1


@dataclass
class FakeMacPlatform:
    current_power_source: str = "AC Power"
    current_lid_closed: bool = False
    output_volume: int = 0
    output_muted: bool = True
    sleep_disabled: int = 0
    fail_enable_sleep: bool = False
    fail_restore_sleep: bool = False
    spoken: list[tuple[str, int, str]] = field(default_factory=list)
    speech_stopped: int = 0
    output_changes: int = 0
    speaking: bool = False

    def power_source(self) -> str:
        return self.current_power_source

    def lid_closed(self) -> bool:
        return self.current_lid_closed

    def set_output(self, volume: int, muted: bool) -> None:
        self.output_changes += 1
        self.output_volume = volume
        self.output_muted = muted

    def speak(self, voice: str, rate: int, text: str) -> None:
        self.spoken.append((voice, rate, text))
        self.speaking = True

    def is_speaking(self) -> bool:
        return self.speaking

    def stop_speech(self) -> None:
        self.speech_stopped += 1
        self.speaking = False

    def set_sleep_disabled(self, value: int) -> bool:
        if value == 1 and self.fail_enable_sleep:
            return False
        if value == 0 and self.fail_restore_sleep:
            return False
        self.sleep_disabled = value
        return True
