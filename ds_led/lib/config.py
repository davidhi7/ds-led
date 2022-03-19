import json
from pathlib import Path
from ds_led.lib.errors import IllegalArgumentError

class Colour:

    def __init__(self, hex_str: str):
        """Create new Colour object. This constructor takes a hexadecimal value like '#FF0000' and decodes it into decimal r/g/b values."""
        if len(hex_str) < 6 or len(hex_str) > 7:
            raise IllegalArgumentError('Given hexadecimal colour representation neither 6 nor 7 characters long.') 
        if hex_str.startswith('#'):
            hex_str = hex_str[1:]
        try:
            self.red = int(hex_str[0:2], 16)
            self.green = int(hex_str[2:4], 16)
            self.blue = int(hex_str[4:6], 16)
        except ValueError:
            raise IllegalArgumentError('Invalid hexadecimal colour representation given.')

    def __str__(self):
        return f'rgb({self.red},{self.green},{self.blue})'

# TODO better class name
class ConfigEntry:

    def __init__(self, threshold, colour, brightness, player_leds):
        self.threshold = threshold
        self.colour = colour
        self.brightness = brightness
        self.player_leds = player_leds

# TODO separate led logic from config class
class Config:
    
    table = list()

    def __init__(self, config_file: Path):
        if not config_file.is_file():
            raise IllegalArgumentError('Provided configuration file is not a valid file')
        config = None
        with open(config_file) as file:
            config = json.load(file)
        default = config['default']
        gradient = sorted(config['gradient'], key=lambda d: d['threshold'])
        for entry in (*gradient, default):
            threshold = entry.get('threshold', 100)
            colour = Colour(entry.get('colour', default['colour']))
            brightness = entry.get('brightness', default['brightness'])
            player_leds = int(entry.get('player-leds', default['player-leds']), 2)
            self.table.append(ConfigEntry(threshold, colour, brightness, player_leds))
        self.config = config
    
    def get_values(self, battery_perc: int):
        for entry in self.table:
            if battery_perc <= entry.threshold:
                return entry
