import logging
from ds_led.lib.config import Config, ControllerSetting, Colour
from ds_led.lib.controller import DualSense, CONTROLLER_CHARGING, CONTROLLER_DISCHARGING

logger = logging.getLogger(__name__)

class ControllerConfig:
    
    def __init__(self, config):
        self.config = config
        controller_config = config.data['controller']
        self.default = self.parse_setting(controller_config['default'])
        if 'discharging' in controller_config:
            self.table_discharging = sorted(self.parse_settings_list(controller_config['discharging']), reverse=True)
        if 'charging' in controller_config:
            self.table_charging = sorted(self.parse_settings_list(controller_config['charging']), reverse=False)
        self.config = config

    def parse_settings_list(self, settings_list: dict) -> list:
        """Parse list of 'threshold: Setting' configurations, returning an unsorted dictionary."""
        settings_dict = dict()
        for setting in settings_list:
            key = list(setting.keys())[0]
            value = self.parse_setting(setting[key])
            settings_dict[key] = value
        return settings_dict.items()
    
    def parse_setting(self, setting: dict) -> ControllerSetting:
        """Parse"""
        return ControllerSetting(
            Colour(setting.get('colour')) if 'colour' in setting else None,
            setting.get('brightness'),
            int(setting.get('player-leds'), 2) if 'player-leds' in setting else None
        )

    def get_setting(self, battery_perc: int, charging: str) -> ControllerSetting:
        """Return the ControllerSetting object for the given battery level and status (DualSense.CHARGING or DualSense.DISCHARGING)."""
        if charging == CONTROLLER_DISCHARGING:
            for threshold, setting in self.table_discharging:
                if battery_perc >= threshold:
                    return setting.fallback(self.default)
        else:
            fallback = self.get_setting(battery_perc, CONTROLLER_DISCHARGING).fallback(self.default)
            for threshold, setting in self.table_charging:
                if battery_perc <= threshold:
                    return setting.fallback(fallback)
        
    def apply_config(self, controller: DualSense):
        """Apply lightbar colour, brightness and player led status as specified in the ControllerSetting."""
        setting = self.get_setting(controller.get_battery(), controller.get_status())
        logger.debug(f'Applying configuration {setting}')
        controller.set_rgb_colour(setting.colour)
        controller.set_rgb_brightness(setting.brightness)
        controller.set_player_leds(setting.player_leds)
