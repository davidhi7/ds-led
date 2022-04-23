from __future__ import annotations
import yaml
from pathlib import Path
from ds_led.lib.errors import IllegalArgumentError


class Colour:

    def __init__(self, hex_str: str):
        # noinspection PyPep8
        """Create new Colour object. This constructor takes a hexadecimal value like '#FF0000' and decodes it into decimal r/g/b values."""
        if len(hex_str) < 6 or len(hex_str) > 7:
            raise IllegalArgumentError(
                f"Given hexadecimal colour representation '{hex_str}' neither 6 nor 7 characters long.")
        if hex_str.startswith('#'):
            hex_str = hex_str[1:]
        try:
            self.red = int(hex_str[0:2], 16)
            self.green = int(hex_str[2:4], 16)
            self.blue = int(hex_str[4:6], 16)
        except ValueError:
            raise IllegalArgumentError(f"'{hex_str}': Invalid hexadecimal colour representation  given.")

    def to_hex_str(self):
        """Return hexadecimal notation of the colour (e.g. '#ABCDEF')'."""
        return f'#{(self.red << 16) + (self.green << 8) + self.blue:06x}'.upper()

    def __str__(self):
        # hexadecimal colour notation, shorter compared to decimal rgb values
        return self.to_hex_str()


class ControllerSetting:

    def __init__(self, colour: Colour, brightness: int, player_leds: int):
        # noinspection PyPep8
        """
        Create config entry object specifying a state of the controller configuration in a specific battery level range.
        Such a state contains colour and brightness of the lightbar, the player led status and the upper threshold of
        the battery level.
        """
        self.colour = colour
        self.brightness = brightness
        self.player_leds = player_leds

    def fallback(self, fallback: ControllerSetting) -> ControllerSetting:
        # noinspection PyPep8
        """Return new ControllerSetting object containing all values of the calling object while using the fallback object's values if required."""
        # noinspection PyPep8
        return ControllerSetting(
            self.colour if self.colour is not None else fallback.colour,
            self.brightness if self.brightness is not None else fallback.brightness,
            self.player_leds if self.player_leds is not None else fallback.player_leds
        )

    def __str__(self) -> str:
        player_leds_str = format(self.player_leds, 'b').zfill(5)
        return f'ControllerSetting(colour={self.colour}, brightness={self.brightness}, player-leds={player_leds_str})'


class DefaultControllerSetting(ControllerSetting):

    def __init__(self):
        """Create ControllerSetting with hardcoded default values to use as fallback."""
        super().__init__(Colour('#000000'), 0, 0)

    def __str__(self) -> str:
        base_value = super().__str__()
        return base_value.replace('ControllerSetting', 'DefaultControllerSetting')


class Config:

    def __init__(self, config_file: Path):
        """Create wrapper for the configuration file."""
        if not config_file.is_file():
            raise IllegalArgumentError('Provided configuration file is not a valid file')
        with open(config_file) as file:
            self.data = yaml.load(file, Loader=yaml.Loader)
