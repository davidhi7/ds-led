import logging
import subprocess
import time
from pathlib import Path

from ds_led.lib.config import Config
from ds_led.lib.controller import DualSense
from ds_led.lib.controllerconfig import ControllerConfig

logger = logging.getLogger(__name__)


class Daemon:

    @staticmethod
    def search_controllers(controllers: list) -> list:
        """Update the provided list of controller objects."""
        # Remove no longer connected controllers from the list
        for current_controller in controllers:
            if not current_controller.verify_connection():
                controllers.remove(current_controller)
        # Find all new device directories matching the pattern /sys/class/power_supply/ps-controller-battery-* that
        # aren't already present in the list
        controller_discovery = "find /sys/class/power_supply -maxdepth 1 -name 'ps-controller-battery-*'" \
                               "| sed -z '$s/\\n$//'"
        out = subprocess.run(controller_discovery, shell=True, capture_output=True, text=True)
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
        controller_config = ControllerConfig(config)
        # Interval between two iterations
        interval = int(config.data['daemon']['interval'])
        # if True, only write controller settings on battery level change
        battery_change_required = bool(config.data['daemon']['require_battery_change'])
        while True:
            controllers = self.search_controllers(controllers)
            for controller in controllers:
                battery_status_change = controller.test_battery_change()
                if battery_status_change or not battery_change_required:
                    if battery_status_change:
                        logger.info(f'{controller.power_supply}: Battery level: {controller.get_battery()}')
                    controller_config.apply_config(controller)
            time.sleep(interval)
