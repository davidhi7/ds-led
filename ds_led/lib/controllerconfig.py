import logging
from ds_led.lib.config import ControllerSetting, DefaultControllerSetting, Colour
from ds_led.lib.controller import DualSense, CONTROLLER_CHARGING, CONTROLLER_DISCHARGING, CONTROLLER_FULL
from ds_led.lib.errors import InvalidConfigurationError

logger = logging.getLogger(__name__)


class ControllerConfig:

    def __init__(self, config):
        """Create new ControllerConfig object using the given configuration and parse setting values."""
        self.config = config
        self.tables = dict()
        self.fallbacks = dict()
        if 'controller' not in config.data or config.data['controller'] is None:
            raise InvalidConfigurationError('Configuration file lacks essential "controller" list.')
        controller_config = config.data['controller']
        if 'default' in controller_config:
            self.tables['Default'] = ((100, self.parse_setting(controller_config['default'])),)
        else:
            self.tables['Default'] = ((100, DefaultControllerSetting()),)
        if 'discharging' in controller_config:
            self.tables[CONTROLLER_DISCHARGING] = sorted(self.parse_settings_list(controller_config['discharging']),
                                                         reverse=False)
        if 'charging' in controller_config:
            self.tables[CONTROLLER_CHARGING] = sorted(self.parse_settings_list(controller_config['charging']),
                                                      reverse=False)
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
        return list(settings_dict.items())

    def get_setting(self, battery_perc: int, status: str) -> ControllerSetting:
        """Return the ControllerSetting object for the given battery level and status (DualSense.CONTROLLER_{
        CHARGING, DISCHARGING, FULL}). """
        fallback = None
        if self.fallbacks[status] is not None:
            fallback = self.get_setting(battery_perc, self.fallbacks[status])
        if status not in self.tables or self.tables[status] is None:
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

    @staticmethod
    def parse_setting(setting: dict) -> ControllerSetting:
        """Create a single ControllerSetting of a dictionary containing a colour, brightness and player-led value.
        Use None if no valid value is given. """
        return ControllerSetting(
            Colour(setting.get('colour')) if 'colour' in setting else None,
            setting.get('brightness'),
            int(setting.get('player-leds'), 2) if 'player-leds' in setting else None
        )
