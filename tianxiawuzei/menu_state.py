from __future__ import annotations

from .controller import Mode


def menu_title_for_mode(mode: Mode) -> str:
    if mode == Mode.NONE:
        return "贼"
    return "警"


def scenario_hint_text(language: str = "zh") -> str:
    if language == "en":
        return "Use when briefly leaving your computer in a cafe or library"
    return "咖啡馆图书馆临时离开电脑时开启使用"


def status_text_for_mode(mode: Mode, alarming: bool, language: str = "zh") -> str:
    if language == "en":
        if alarming:
            return "Status: Alarming"
        if mode == Mode.CHARGER:
            return "Status: Charger alarm monitoring"
        if mode == Mode.LID:
            return "Status: Lid alarm monitoring"
        return "Status: Off"
    if alarming:
        return "状态：报警中"
    if mode == Mode.CHARGER:
        return "状态：充电器报警监控开启中"
    if mode == Mode.LID:
        return "状态：合盖报警监控开启中"
    return "状态：未开启"
