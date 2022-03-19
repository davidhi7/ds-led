from pathlib import Path
from ds_led.daemon import Daemon

# locations where config files are looked for. First entries have the highest priority.
CONFIG_LOCATIONS = [
    '/etc/ds-led.conf'
]

config_file = None
for location in CONFIG_LOCATIONS:
    if Path(location).is_file():
        config_file = Path(location)
        break

daemon = Daemon()
daemon.run(config_file)
