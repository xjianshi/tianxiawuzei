from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    alarm_volume: int = 60
    alarm_text: str = "请不要碰我电脑"
    close_password: str = "1111"
    voice: str = "Sin-ji"
    speech_rate: int = 165
    language: str = "zh"

    def normalized(self) -> "AppConfig":
        volume = max(0, min(100, int(self.alarm_volume)))
        text = self.alarm_text.strip() or "请不要碰我电脑"
        password = self.close_password.strip() or "1111"
        voice = self.voice.strip() or "Sin-ji"
        language = self.language if self.language in {"zh", "en"} else "zh"
        return AppConfig(
            alarm_volume=volume,
            alarm_text=text,
            close_password=password,
            voice=voice,
            speech_rate=int(self.speech_rate),
            language=language,
        )


class ConfigStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data.setdefault("language", "zh")
        return AppConfig(**data).normalized()

    def save(self, config: AppConfig) -> None:
        normalized = config.normalized()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(normalized), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def default_config_path() -> Path:
    return Path.home() / ".tianxiawuzei" / "config.json"
