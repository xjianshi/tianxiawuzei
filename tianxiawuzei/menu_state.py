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
        if mode == Mode.COMPUTER:
            return "Status: Computer monitoring"
        return "Status: Off"
    if alarming:
        return "状态：报警中"
    if mode == Mode.COMPUTER:
        return "状态：电脑监控开启中"
    return "状态：未开启"


def sleep_status_text(sleep_disabled: int, language: str = "zh") -> str:
    if language == "en":
        if sleep_disabled == 0:
            return "System sleep: Allowed"
        if sleep_disabled == 1:
            return "System sleep: Prevented"
        return "System sleep: Unknown"
    if sleep_disabled == 0:
        return "系统休眠：允许"
    if sleep_disabled == 1:
        return "系统休眠：已阻止"
    return "系统休眠：未知"
