import subprocess
from pathlib import Path
from ds_led.lib.errors import IllegalArgumentError
from ds_led.lib.config import ConfigEntry, Colour

class DualSense:

    CONTROLLER_CHARGING = 'Charging'
    CONTROLLER_DISCHARGING = 'Discharging'

    power_supply = None
    device = None
    rgb_led = None
    player_leds = None
    last_battery_perc = -1

    def __init__(self, battery_dev: Path):
        """Initialise new controller object. 'battery_dev' must be a path matching '/sys/class/power_supply/ps-controller-battery-*'."""
        self.power_supply = battery_dev
        self.device = battery_dev / 'device'
        self.rgb_led = Path(subprocess.run(f"find {self.device}/leds -maxdepth 1 -name 'input*:rgb:indicator' | sed -z '$ s/\\n$//'", shell=True, capture_output=True, text=True).stdout)
        self.player_leds = [Path(led) for led in subprocess.run(f"find {self.device}/leds -maxdepth 1 -name 'input*:white:player-*' | sort -nr | sed -z '$ s/\\n$//'", shell=True, capture_output=True, text=True).stdout.split('\n')]
        print(f"New controller '{self.device}' connected.")

    def verify_connection(self):
        """Test whether the connection to the controller is still present. Return True if so, otherwise False."""
        # try to read battery level. If the file containing the value no longer exists, the controller is most likely not connected anymore.
        try:
            self.read_battery()
        except FileNotFoundError:
            print(f"Controller '{self.device}' is not connected anymore.")
            return False
        return True
    
    def read_battery(self):
        """Read the battery level of the controller."""
        with open(self.power_supply / 'capacity', 'r') as file:
            return int(file.read())
            
    def get_status(self):
        """Return the status of the battery. Possible values: 'Charging' and 'Discharging'."""
        with open(self.power_supply / 'status', 'r') as file:
            value = file.read()
            if value.startswith(self.CONTROLLER_CHARGING):
                return self.CONTROLLER_CHARGING
            else:
                return self.CONTROLLER_DISCHARGING

    def set_rgb_colour(self, colour: Colour):
        """Set the colour of the builtin RGB LED."""
        # Order of the red, green, blue values is provided by the file 'multi_index'.
        pattern = 'red green blue'
        with open(self.rgb_led / 'multi_index', 'r') as file:
            pattern = file.readline().replace('\n', '')
        values = pattern.replace('red', str(colour.red)).replace('green', str(colour.green)).replace('blue', str(colour.blue))
        with open(self.rgb_led / 'multi_intensity', 'w') as file:
            file.write(values)

    def set_rgb_brightness(self, brightness: int):
        """Set the brightness of the builtin RGB LED."""
        min_brightness = 0
        max_brightness = 255
        with open(self.rgb_led / 'max_brightness', 'r') as file:
            max_brightness = int(file.read())
        if brightness > max_brightness or brightness < min_brightness:
            raise IllegalArgumentError(f'Invalid brightness value {brightness}, must be between {min_brightness} and {max_brightness}.')
            return
        with open(self.rgb_led / 'brightness', 'w') as file:
            file.write(str(brightness))

    def set_player_leds(self, player_leds: int):
        """Set the status of each of the 5 player leds."""
        # use of bitwise operators might seem unnecessary complicated but I finally found a usage for them and I didn't want to miss it
        if player_leds >> 5 != 0:
            bitcount = len(bin(player_leds)[2:])
            raise IllegalArgumentError(f'Expected number with at most 5 bits, got {bitcount}.')
        for n in range(0, 5):
            with open(self.player_leds[n] / 'brightness', 'w') as file:
                file.write(str((player_leds >> n) & 1))
    
    def apply_config(self, config: ConfigEntry):
        """Apply lightbar colour, brightness and player led status as specified in th config entry."""
        self.set_rgb_colour(config.colour)
        self.set_rgb_brightness(config.brightness)
        self.set_player_leds(config.player_leds)
