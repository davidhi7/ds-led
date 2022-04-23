import logging
from pathlib import Path
from ds_led.daemon import Daemon

logger = logging.getLogger(__name__)


def create_config(path_string):
    with open(path_string, 'w') as file:
        # noinspection PyPep8
        file.write("""daemon:
  # Interval between checking the battery and writing controller settings
  interval: 15
  # If False, write controller settings even if the battery level did not change since the last time.
  # Useful to overwrite Steams attempt to manage the controller lightbar on its own.
  require_battery_change: false

controller:
  # Default values to be used as fallback if no more specific values are found.
  default:
    colour: "FFFFFF"
    brightness: 128
    player-leds: "00000"

  # Values applied when the controller is discharging. The setting with the highest threshold greater than or equal to the battery level is chosen.
  discharging:
    - 100:
        colour: "001000"
    - 60: 
        colour: "104000"
    - 40:
        colour: "404000"
    - 20:
        colour: "800000"
    - 10:
        colour: "FF0000"
        brightness: 255

  # Values applied when the controller is charging (including full battery). The setting with the highest threshold greater than or equal to the battery level is chosen.
  charging:
    - 0:
        player-leds: "00100"
    - 100:
        player-leds: "11111"
""")


def discover_config(locations: list[str]) -> str:
    for path in locations:
        if Path(path).is_file():
            return path
    fallback = locations[0]
    logger.info(f'No configuration file found, creating one at {fallback}.')
    create_config(fallback)
    return fallback


# locations where config files are looked for. First entry has the highest priority and is tried first.
CONFIG_LOCATIONS = [
    '/etc/ds-led.conf'
]

config_path = Path(discover_config(CONFIG_LOCATIONS))
daemon = Daemon()
daemon.run(config_path)
