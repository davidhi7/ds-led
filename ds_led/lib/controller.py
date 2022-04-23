import logging
import subprocess
from pathlib import Path
from ds_led.lib.config import Colour
from ds_led.lib.errors import IllegalArgumentError

logger = logging.getLogger(__name__)

CONTROLLER_CHARGING = 'Charging'
CONTROLLER_DISCHARGING = 'Discharging'
CONTROLLER_FULL = 'Full'


class DualSense:
    power_supply = None
    device = None
    rgb_led = None
    player_leds = None
    last_queried_battery = -1

    def __init__(self, power_supply_path: Path):
        """Initialise new controller object. 'power_supply_path' must be a path matching
        '/sys/class/power_supply/ps-controller-battery-*'. """
        self.power_supply = power_supply_path
        self.device = power_supply_path / 'device'
        find_rgb_led = f"find {self.device}/leds -maxdepth 1 -name 'input*:rgb:indicator' | sed -z '$ s/\\n$//'"
        self.rgb_led = Path(subprocess.run(find_rgb_led, shell=True, capture_output=True, text=True).stdout)
        find_player_leds = f"find {self.device}/leds -maxdepth 1 -name 'input*:white:player-*' | sort -nr" \
                           f"| sed -z '$ s/\\n$//'"
        self.player_leds = [
            Path(led) for led in
            subprocess.run(find_player_leds, shell=True, capture_output=True, text=True).stdout.split('\n')
        ]
        logger.info(f"New controller '{self.device}' connected.")

    def verify_connection(self):
        """Test whether the connection to the controller is still present. Return True if so, otherwise False."""
        # try to read battery level. If the file containing the value no longer exists, the controller is most likely
        # not connected anymore.
        try:
            self.get_battery()
        except FileNotFoundError:
            logger.info(f"Controller '{self.device}' is not connected anymore.")
            return False
        return True

    def get_battery(self):
        """Read the battery level of the controller."""
        with open(self.power_supply / 'capacity', 'r') as file:
            return int(file.read())

    def get_status(self):
        """Return the status of the battery. Possible values: 'Charging', 'Discharging' and 'Full'."""
        with open(self.power_supply / 'status', 'r') as file:
            return file.read().rstrip()

    def set_rgb_colour(self, colour: Colour):
        """Set the colour of the builtin RGB LED."""
        # Order of the red, green, blue values is provided by the file 'multi_index'.
        try:
            with open(self.rgb_led / 'multi_index', 'r') as file:
                pattern = file.readline().replace('\n', '')
        except FileNotFoundError:
            pattern = 'red green blue'

        values = pattern \
            .replace('red', str(colour.red)) \
            .replace('green', str(colour.green)) \
            .replace('blue', str(colour.blue))
        with open(self.rgb_led / 'multi_intensity', 'w') as file:
            file.write(values)

    def set_rgb_brightness(self, brightness: int):
        """Set the brightness of the builtin RGB LED."""
        min_brightness = 0
        try:
            with open(self.rgb_led / 'max_brightness', 'r') as file:
                max_brightness = int(file.read())
        except FileNotFoundError:
            max_brightness = 255

        if brightness > max_brightness or brightness < min_brightness:
            raise IllegalArgumentError(
                f'Invalid brightness value {brightness}, must be between {min_brightness} and {max_brightness}.')
        with open(self.rgb_led / 'brightness', 'w') as file:
            file.write(str(brightness))

    def set_player_leds(self, player_leds: int):
        """Set the status of each of the 5 player leds."""
        # Use of bitwise operators might seem unnecessary complicated, but I finally found a usage for them, and I
        # didn't want to miss it
        if player_leds >> 5 != 0:
            bit_count = len(bin(player_leds)[2:])
            raise IllegalArgumentError(f'Expected number with at most 5 bits, got {bit_count}.')
        for n in range(0, 5):
            with open(self.player_leds[n] / 'brightness', 'w') as file:
                file.write(str((player_leds >> n) & 1))

    def test_battery_change(self) -> bool:
        """Test whether the battery level has changed since the last call of this method."""
        new_battery = self.get_battery()
        if self.last_queried_battery != new_battery:
            self.last_queried_battery = new_battery
            return True
        return False
