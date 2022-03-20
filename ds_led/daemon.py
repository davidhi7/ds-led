import subprocess
import time
from pathlib import Path
from ds_led.lib.controller import DualSense
from ds_led.lib.config import Config, ConfigEntry

class Daemon:

    def search_controllers(self, controllers: list) -> list:
        """Update the provided list of controller objects."""
        # Remove no longer connected controllers from the list
        for curent_controller in controllers:
            if not curent_controller.verify_connection():
                controllers.remove(curent_controller)
        # Find all new device directories matching the pattern /sys/class/power_supply/ps-controller-battery-* that aren't already present in the list
        out = subprocess.run("find /sys/class/power_supply -maxdepth 1 -name 'ps-controller-battery-*' | sed -z '$ s/\\n$//'", shell=True, capture_output=True, text=True)
        if out.stdout != '':
            for power_supply in out.stdout.split('\n'):
                power_supply_path = Path(power_supply)
                if power_supply_path not in [c.power_supply for c in controllers]:
                    controllers.append(DualSense(power_supply_path))
        return controllers

    def run(self, config_path: Path):
        """Start the daemon."""
        controllers = []
        config = Config(config_path)
        interval = int(config.config['daemon']['interval'])
        while True:
            controllers = self.search_controllers(controllers)
            for controller in controllers:
                battery_perc = controller.read_battery()
                if controller.last_battery_perc != battery_perc:
                    print(f'{controller.device}: Battery level: {battery_perc}')
                    controller.last_battery_perc = battery_perc
                    controller.apply_config(config.get_values(battery_perc))
            time.sleep(interval)
