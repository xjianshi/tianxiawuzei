from __future__ import annotations

from urllib.parse import quote


FEEDBACK_EMAIL = "xjianshi@163.com"
FEEDBACK_SUBJECTS = {
    "zh": "天下无贼APP使用反馈和建议",
    "en": "Tianxiawuzei App Feedback and Suggestions",
}


def usage_text(language: str = "zh") -> str:
    if language == "en":
        return """Tianxiawuzei is a macOS menu bar alarm tool for short moments away from your computer, such as in a cafe, library, bookstore, or office.

Disclaimer:
This app is built as an interest project and provided for free. The developer is not responsible for any loss of computer, data, property, or anything else that may occur while using it. The purpose of this app is temporary deterrence. It cannot prevent theft and cannot replace personal care or a safe environment. It is a reminder tool, not a guarantee. Keep your computer in a safe place whenever possible.

Use cases:
- You are worried that someone may unplug the charger, move the computer, or close the lid.
- You briefly leave your seat and want the computer to speak an alarm when touched.

Computer monitoring:
- Use “Start Computer Monitoring (charger/lid alarm)” from the menu bar.
- The menu bar title changes from “贼” to “警” after monitoring starts.
- Unplugging power triggers the alarm.
- Plugging power back in stops charger-triggered speech and keeps monitoring.
- Closing the lid triggers the alarm.
- Lid alarm is latched: it keeps alarming after the lid is opened until the close password is entered.

Why computer monitoring needs the system password:
macOS may immediately sleep when the lid is closed, and a normal app cannot keep alarming after sleep. To make lid monitoring more reliable, Tianxiawuzei temporarily changes the system power setting SleepDisabled. This is a system-level setting, so macOS requires administrator authorization when enabling or disabling lid alarm monitoring.

Closing and safety:
- Closing any alarm monitor requires the close password.
- After the close password is accepted, computer monitoring is considered closed.
- The app only shows system sleep restore success or failure if it actually tried to restore SleepDisabled during this close.
- If the system password dialog is canceled or closed, monitoring stops but SleepDisabled may remain unrestored. The menu shows “Monitoring status: system settings need restore”, and “Start Computer Monitoring” stays disabled until restoration succeeds.
- If SleepDisabled is not restored during close, the app retries automatically and you can use “Restore System Sleep Settings” from the menu.
- If SleepDisabled was already enabled before monitoring started, Tianxiawuzei does not change it and will not show a sleep restore result when closing monitoring.
- After an alarm is triggered, the app keeps restoring the system volume to your configured alarm volume to prevent someone from turning it down.
- While monitoring is active, alarm volume, alarm text, and close password cannot be changed.
"""
    return """天下无贼是一款 macOS 菜单栏防触碰报警工具，适合在咖啡馆、图书馆、办公室等短暂离开电脑的场景使用。

免责声明：
本应用基于兴趣开发，免费提供使用。使用本应用过程中如出现电脑、数据、财物或其他任何损失，开发者不承担任何责任。本应用的目的只是临时震慑别有用心的人，无法避免被偷，也不能替代个人看管和安全环境。它更像是“防君子不防小人”的提醒工具。电脑仍应尽量放在安全环境中使用和保存，例如我个人一般会选择先锋书店五台山总店这类相对安全的地方临时使用。

使用场景：
- 担心别人拔掉充电器、移动电脑或合上屏幕。
- 临时离开座位，希望电脑被触碰时发出语音提醒。

电脑监控：
- 从菜单栏点击“开启电脑监控（拔充电器/合盖触发报警）”。
- 开启后，菜单栏从“贼”变为“警”。
- 拔掉电源时触发报警。
- 插回电源后停止由充电器触发的播报，并继续保持监控。
- 检测到合盖后触发报警。
- 合盖报警采用锁存规则：开盖后也会继续报警，直到输入关闭密码关闭监控。

为什么开关电脑监控需要输入系统密码：
合盖后 macOS 默认可能立即睡眠，普通 App 无法继续报警。为了让合盖监控尽量可靠，天下无贼需要临时修改系统电源设置 SleepDisabled。这个操作属于系统级设置，macOS 要求管理员授权，所以开启和关闭合盖报警监控时可能会弹出系统密码窗口。

关闭与安全：
- 关闭任何报警监控都需要输入关闭密码。
- 关闭密码正确后，电脑监控即视为关闭成功。
- 只有本次确实执行了系统休眠恢复动作，App 才会提示系统休眠恢复成功或失败。
- 如果系统密码对话框取消或关闭，报警会停止，但 SleepDisabled 可能仍未恢复。菜单会显示“监控状态：系统设置待恢复”，“开启电脑监控”会保持灰化，直到恢复成功。
- 如果关闭时 SleepDisabled 没有恢复，App 会自动重试，也可以从菜单点击“恢复系统休眠设置”。
- 如果开启监控前 SleepDisabled 本来就是 1，天下无贼不会主动修改系统休眠设置；关闭监控时也不会执行恢复动作，因此不会提示系统休眠恢复成功或失败。
- 报警触发后，App 会持续把系统音量恢复到你设置的报警音量，避免被人调小。
- 报警监控运行期间，不允许修改报警音量、报警词汇或关闭密码。
"""


def feedback_mailto(language: str = "zh") -> str:
    subject = quote(FEEDBACK_SUBJECTS.get(language, FEEDBACK_SUBJECTS["zh"]))
    return f"mailto:{FEEDBACK_EMAIL}?subject={subject}"
