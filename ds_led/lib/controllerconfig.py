import logging
from ds_led.lib.config import Config, ControllerSetting, Colour
from ds_led.lib.controller import DualSense, CONTROLLER_CHARGING, CONTROLLER_DISCHARGING

logger = logging.getLogger(__name__)

class ControllerConfig:
    
    def __init__(self, config):
        self.config = config
        self.default = self.parse_setting(config.data['default'])
        self.table_discharging = self.parse_settings_list( sorted(config.data['discharging'], key=lambda d: d['threshold']) )
        if 'charging' in config.data:
            self.table_charging = self.parse_settings_list( sorted(config.data['charging'], key=lambda d: d['threshold'], reverse=True) )
        self.config = config

    def parse_settings_list(self, settings_list: dict) -> list:
        return [self.parse_setting(setting) for setting in settings_list]
    
    def parse_setting(self, setting: dict) -> ControllerSetting:
        return ControllerSetting(
            setting.get('threshold', 100),
            Colour(setting.get('colour')) if 'colour' in setting else None,
            setting.get('brightness'),
            int(setting.get('player-leds'), 2) if 'player-leds' in setting else None
        )

    def get_setting(self, battery_perc: int, charging: str) -> ControllerSetting:
        """Return the ControllerSetting object for the given battery level and status (DualSense.CHARGING or DualSense.DISCHARGING)."""
        if charging == CONTROLLER_DISCHARGING:
            for entry in self.table_discharging:
                if battery_perc <= entry.threshold:
                    return entry.fallback(self.default)
        else:
            fallback = self.get_setting(battery_perc, CONTROLLER_DISCHARGING).fallback(self.default)
            for entry in self.table_charging:
                if battery_perc > entry.threshold:
                    return entry.fallback(fallback)
        
    def apply_config(self, controller: DualSense):
        """Apply lightbar colour, brightness and player led status as specified in the ControllerSetting."""
        setting = self.get_setting(controller.get_battery(), controller.get_status())
        logger.debug(f'Applying configuration {setting}')
        controller.set_rgb_colour(setting.colour)
        controller.set_rgb_brightness(setting.brightness)
        controller.set_player_leds(setting.player_leds)
