import logging
from pathlib import Path
from ds_led.daemon import Daemon

logger = logging.getLogger(__name__)

def create_config(path_string):
    with open(path_string, 'w') as file:
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

# locations where config files are looked for. First entry has the highest priority and is tried first.
CONFIG_LOCATIONS = [
    '/etc/ds-led.conf'
]

config_path = None
for location in CONFIG_LOCATIONS:
    if Path(location).is_file():
        config_path = Path(location)
        break
    config_path_string = CONFIG_LOCATIONS[0]
    logger.info(f'No configuration file found, creating one at {config_path_string}.')
    create_config(config_path_string)
    config_path = Path(config_path_string)

daemon = Daemon()
daemon.run(config_path)
