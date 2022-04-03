import logging
from ds_led.lib.config import Config, ControllerSetting, Colour
from ds_led.lib.controller import DualSense, CONTROLLER_CHARGING, CONTROLLER_DISCHARGING, CONTROLLER_FULL

logger = logging.getLogger(__name__)

class ControllerConfig:
    
    def __init__(self, config):
        self.config = config
        self.tables = dict()
        self.fallbacks = dict()
        controller_config = config.data['controller']
        if 'default' in controller_config:
            self.tables['Default'] = sorted({0: self.parse_setting(controller_config['default']), 100: self.parse_setting(controller_config['default'])}.items())
        if 'discharging' in controller_config:
            self.tables[CONTROLLER_DISCHARGING] = sorted(self.parse_settings_list(controller_config['discharging']), reverse=False)
        if 'charging' in controller_config:
            self.tables[CONTROLLER_CHARGING] = sorted(self.parse_settings_list(controller_config['charging']), reverse=False)
            self.tables[CONTROLLER_FULL] = self.tables[CONTROLLER_CHARGING]
        self.fallbacks['Default'] = None
        self.fallbacks[CONTROLLER_DISCHARGING] = 'Default'
        self.fallbacks[CONTROLLER_CHARGING] = CONTROLLER_DISCHARGING
        self.fallbacks[CONTROLLER_FULL] = CONTROLLER_DISCHARGING

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

    def get_setting(self, battery_perc: int, status: str) -> ControllerSetting:
        """Return the ControllerSetting object for the given battery level and status (DualSense.CONTROLLER_{CHARGING, DISCHARGING, FULL})."""
        if self.fallbacks[status] != None:
            fallback = self.get_setting(battery_perc, self.fallbacks[status])
        else:
            # final fallback if all other fallback options failed
            fallback = ControllerSetting(Colour('#000000'), 0, 0)
        if status not in self.tables or self.tables[status] == None:
            return fallback
        for threshold, setting in self.tables[status]:
            if battery_perc <= threshold:
                return setting.fallback(fallback)

        
    def apply_config(self, controller: DualSense):
        """Apply lightbar colour, brightness and player led status as specified in the ControllerSetting."""
        setting = self.get_setting(controller.get_battery(), controller.get_status())
        logger.debug(f'Applying configuration {setting}')
        controller.set_rgb_colour(setting.colour)
        controller.set_rgb_brightness(setting.brightness)
        controller.set_player_leds(setting.player_leds)
