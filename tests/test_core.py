import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tianxiawuzei.config import AppConfig, ConfigStore
from tianxiawuzei.controller import AlarmController, CloseResult, Mode
from tianxiawuzei.menu_state import menu_title_for_mode, scenario_hint_text, status_text_for_mode
from tianxiawuzei.platform import FakeMacPlatform
from tianxiawuzei.support import FEEDBACK_EMAIL, feedback_mailto, usage_text


class ConfigStoreTest(unittest.TestCase):
    def test_loads_defaults_when_config_file_is_missing(self):
        with TemporaryDirectory() as tmp:
            store = ConfigStore(Path(tmp) / "config.json")

            config = store.load()

        self.assertEqual(config.alarm_volume, 60)
        self.assertEqual(config.alarm_text, "请不要碰我电脑")
        self.assertEqual(config.close_password, "1111")
        self.assertEqual(config.voice, "Sin-ji")
        self.assertEqual(config.language, "zh")

    def test_saves_and_loads_public_configuration(self):
        with TemporaryDirectory() as tmp:
            store = ConfigStore(Path(tmp) / "config.json")
            store.save(
                AppConfig(
                    alarm_volume=35,
                    alarm_text="不要碰",
                    close_password="2468",
                    voice="Li-Mu",
                    language="en",
                )
            )

            config = store.load()

        self.assertEqual(config.alarm_volume, 35)
        self.assertEqual(config.alarm_text, "不要碰")
        self.assertEqual(config.close_password, "2468")
        self.assertEqual(config.voice, "Li-Mu")
        self.assertEqual(config.language, "en")


class AlarmControllerTest(unittest.TestCase):
    def setUp(self):
        self.platform = FakeMacPlatform(current_power_source="AC Power", current_lid_closed=False)
        self.config = AppConfig()
        self.controller = AlarmController(self.platform, self.config)

    def test_computer_monitor_starts_with_expected_status_message(self):
        message = self.controller.start_computer_monitor()

        self.assertEqual(message, "电脑监控开启中")
        self.assertEqual(self.controller.mode, Mode.COMPUTER)
        self.assertEqual(self.platform.output_changes, 0)
        self.assertEqual(self.platform.sleep_disabled, 1)
        self.assertEqual(self.platform.sleep_disabled_changes, [1])

    def test_monitor_does_not_modify_sleep_disabled_when_it_was_already_enabled(self):
        self.platform.sleep_disabled = 1

        message = self.controller.start_computer_monitor()
        result = self.controller.close("1111")

        self.assertEqual(message, "电脑监控开启中")
        self.assertEqual(result, CloseResult.CLOSED)
        self.assertEqual(self.platform.sleep_disabled, 1)
        self.assertEqual(self.platform.sleep_disabled_changes, [])

    def test_computer_monitor_alarms_on_battery_and_stops_on_ac(self):
        self.platform.output_volume = 35
        self.platform.output_muted = False
        self.controller.start_computer_monitor()

        self.platform.current_power_source = "Battery Power"
        self.controller.poll_once()

        self.assertTrue(self.controller.alarming)
        self.assertEqual(self.platform.output_volume, 60)
        self.assertEqual(self.platform.spoken[-1], ("Sin-ji", 165, "请不要碰我电脑"))

        self.platform.current_power_source = "AC Power"
        self.controller.poll_once()

        self.assertFalse(self.controller.alarming)
        self.assertEqual(self.platform.output_volume, 35)
        self.assertFalse(self.platform.output_muted)

    def test_alarm_restores_configured_volume_if_someone_turns_it_down(self):
        self.controller.start_computer_monitor()
        self.platform.current_power_source = "Battery Power"
        self.controller.poll_once()

        self.platform.output_volume = 1
        self.platform.output_muted = True
        self.controller.poll_once()

        self.assertEqual(self.platform.output_volume, 60)
        self.assertFalse(self.platform.output_muted)

    def test_computer_monitor_sets_sleep_disabled_and_latches_alarm_after_lid_close(self):
        message = self.controller.start_computer_monitor()

        self.assertEqual(message, "电脑监控开启中")
        self.assertEqual(self.controller.mode, Mode.COMPUTER)
        self.assertEqual(self.platform.sleep_disabled, 1)

        self.platform.current_lid_closed = True
        self.controller.poll_once()
        self.platform.current_lid_closed = False
        self.controller.poll_once()

        self.assertTrue(self.controller.alarming)
        self.assertEqual(self.platform.output_volume, 60)
        self.assertEqual(len(self.platform.spoken), 1)

    def test_computer_monitor_close_restores_output_from_before_alarm(self):
        self.platform.output_volume = 35
        self.platform.output_muted = False
        self.controller.start_computer_monitor()

        self.platform.current_lid_closed = True
        self.controller.poll_once()
        result = self.controller.close("1111")

        self.assertEqual(result, CloseResult.CLOSED)
        self.assertEqual(self.platform.output_volume, 35)
        self.assertFalse(self.platform.output_muted)

    def test_alarm_repeats_after_previous_phrase_finishes(self):
        self.controller.start_computer_monitor()
        self.platform.current_power_source = "Battery Power"
        self.controller.poll_once()

        self.platform.speaking = False
        self.controller.poll_once()

        self.assertEqual(len(self.platform.spoken), 2)

    def test_computer_monitor_does_not_start_when_sleep_disabled_cannot_be_enabled(self):
        self.platform.fail_enable_sleep = True

        with self.assertRaises(RuntimeError):
            self.controller.start_computer_monitor()

        self.assertEqual(self.controller.mode, Mode.NONE)
        self.assertEqual(self.platform.sleep_disabled, 0)

    def test_wrong_close_password_does_not_stop_monitor_or_change_volume(self):
        self.controller.start_computer_monitor()
        self.platform.current_power_source = "Battery Power"
        self.controller.poll_once()

        result = self.controller.close("wrong")

        self.assertEqual(result, CloseResult.WRONG_PASSWORD)
        self.assertEqual(self.controller.mode, Mode.COMPUTER)
        self.assertTrue(self.controller.alarming)
        self.assertEqual(self.platform.output_volume, 60)
        self.assertEqual(self.platform.sleep_disabled, 1)
        self.assertFalse(self.controller.sleep_restore_pending)

    def test_correct_close_password_stops_computer_monitor(self):
        self.controller.start_computer_monitor()

        result = self.controller.close("1111")

        self.assertEqual(result, CloseResult.CLOSED)
        self.assertEqual(self.controller.mode, Mode.NONE)
        self.assertEqual(self.platform.output_volume, 0)
        self.assertTrue(self.platform.output_muted)
        self.assertEqual(self.platform.sleep_disabled, 0)

    def test_computer_monitor_is_not_fully_closed_when_sleep_restore_fails(self):
        self.platform.fail_restore_sleep = True
        self.controller.start_computer_monitor()

        result = self.controller.close("1111")

        self.assertEqual(result, CloseResult.ALARM_STOPPED_SETTINGS_NOT_RESTORED)
        self.assertEqual(self.controller.mode, Mode.NONE)
        self.assertEqual(self.platform.sleep_disabled, 1)
        self.assertTrue(self.controller.sleep_restore_pending)

    def test_pending_sleep_restore_can_be_retried_successfully(self):
        self.platform.fail_restore_sleep = True
        self.controller.start_computer_monitor()
        self.controller.close("1111")

        self.platform.fail_restore_sleep = False
        restored = self.controller.restore_sleep_disabled()

        self.assertTrue(restored)
        self.assertEqual(self.platform.sleep_disabled, 0)
        self.assertFalse(self.controller.sleep_restore_pending)

    def test_pending_sleep_restore_blocks_starting_monitor_until_restored(self):
        self.platform.fail_restore_sleep = True
        self.controller.start_computer_monitor()
        self.controller.close("1111")

        with self.assertRaises(RuntimeError):
            self.controller.start_computer_monitor()

        self.assertEqual(self.controller.mode, Mode.NONE)
        self.assertTrue(self.controller.sleep_restore_pending)

    def test_public_config_cannot_change_while_monitor_is_running(self):
        self.controller.start_computer_monitor()

        with self.assertRaises(RuntimeError):
            self.controller.update_config(AppConfig(alarm_volume=25))

        self.assertEqual(self.controller.config.alarm_volume, 60)

    def test_preview_voice_restores_previous_output_after_speech_finishes(self):
        self.platform.output_volume = 35
        self.platform.output_muted = False

        self.controller.preview_voice()

        self.assertEqual(
            self.platform.output_history,
            [(60, False), (35, False)],
        )
        self.assertEqual(self.platform.spoken[-1], ("Sin-ji", 165, "请不要碰我电脑"))
        self.assertEqual(self.platform.output_muted_during_last_speech, False)

    def test_preview_voice_restores_previous_muted_output_after_speech_finishes(self):
        self.platform.output_volume = 0
        self.platform.output_muted = True

        self.controller.preview_voice()

        self.assertEqual(
            self.platform.output_history,
            [(60, False), (0, True)],
        )


class MenuStateTest(unittest.TestCase):
    def test_menu_title_is_thief_when_no_monitor_is_running(self):
        self.assertEqual(menu_title_for_mode(Mode.NONE), "贼")

    def test_menu_title_is_alarm_when_monitor_is_running(self):
        self.assertEqual(menu_title_for_mode(Mode.COMPUTER), "警")

    def test_status_text_returns_to_computer_monitoring_after_alarm_stops(self):
        self.assertEqual(status_text_for_mode(Mode.COMPUTER, True, "zh"), "状态：报警中")
        self.assertEqual(status_text_for_mode(Mode.COMPUTER, False, "zh"), "状态：电脑监控开启中")
        self.assertEqual(status_text_for_mode(Mode.COMPUTER, False, "en"), "Status: Computer monitoring")

    def test_scenario_hint_explains_temporary_away_use_case(self):
        self.assertEqual(scenario_hint_text("zh"), "咖啡馆图书馆临时离开电脑时开启使用")
        self.assertEqual(scenario_hint_text("en"), "Use when briefly leaving your computer in a cafe or library")


class SupportTextTest(unittest.TestCase):
    def test_usage_text_explains_scenarios_and_system_password_reason(self):
        text = usage_text("zh")

        self.assertIn("咖啡馆", text)
        self.assertIn("电脑监控", text)
        self.assertIn("拔掉电源", text)
        self.assertIn("合盖", text)
        self.assertIn("系统密码", text)
        self.assertIn("SleepDisabled", text)
        self.assertIn("基于兴趣开发", text)
        self.assertIn("免费提供使用", text)
        self.assertIn("任何损失", text)
        self.assertIn("临时震慑", text)
        self.assertIn("无法避免被偷", text)
        self.assertIn("先锋书店五台山总店", text)

    def test_feedback_mailto_uses_configured_email_and_subject(self):
        url = feedback_mailto("zh")

        self.assertTrue(url.startswith(f"mailto:{FEEDBACK_EMAIL}?subject="))
        self.assertIn("%E5%A4%A9%E4%B8%8B%E6%97%A0%E8%B4%BCAPP%E4%BD%BF%E7%94%A8%E5%8F%8D%E9%A6%88%E5%92%8C%E5%BB%BA%E8%AE%AE", url)

    def test_english_usage_and_feedback_are_available(self):
        text = usage_text("en")
        url = feedback_mailto("en")

        self.assertIn("Tianxiawuzei", text)
        self.assertIn("Disclaimer", text)
        self.assertIn("system password", text)
        self.assertIn("feedback", url.lower())


if __name__ == "__main__":
    unittest.main()
