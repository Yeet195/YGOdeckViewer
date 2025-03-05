import base64
import zlib
import struct
import numpy as np


class FormatDecodeException(Exception):
    pass


class TypedDeck:
    def __init__(self, main, extra, side):
        self.main = main
        self.extra = extra
        self.side = side


def base64_to_passcodes(base64_string):
    """Convert base64 string to card IDs (passcodes)"""
    return np.frombuffer(base64.b64decode(base64_string), dtype=np.uint32)


def parse_ydke_url(ydke_url):
    """Parse a YDKE URL and return a TypedDeck object"""
    if not ydke_url.startswith("ydke://"):
        raise ValueError("Unrecognized URL protocol")
    components = ydke_url[len("ydke://"):].split("!")
    if len(components) < 3:
        raise ValueError("Missing ydke URL component")
    return TypedDeck(
        main=base64_to_passcodes(components[0]),
        extra=base64_to_passcodes(components[1]),
        side=base64_to_passcodes(components[2])
    )


def parse_ydk_file(file_path):
    """Parse a YDK file and separate cards into main, extra, and side decks"""
    deck = {"main": [], "extra": [], "side": []}
    current_section = None

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Handle section markers
            if line.startswith("#"):
                if line == "#main":
                    current_section = "main"
                    continue
                elif line == "#extra":
                    current_section = "extra"
                    continue
                else:
                    # Skip other comment lines
                    continue

            if line == "!side":
                current_section = "side"
                continue

            if current_section is None:
                continue

            # Try to parse the card ID
            try:
                card_id = int(line)
                deck[current_section].append(card_id)
            except ValueError:
                # Skip non-integer lines
                pass

    print(f"Parsed YDK file: {len(deck['main'])} main, {len(deck['extra'])} extra, {len(deck['side'])} side cards")
    return deck


class OmegaFormatDecoder:
    """Decoder for EDOPro/Omega deck format"""

    def decode(self, encoded):
        encoded = encoded.strip()
        deflated = base64.b64decode(encoded)
        try:
            raw = zlib.decompress(deflated, -zlib.MAX_WBITS)
        except zlib.error as e:
            raise FormatDecodeException(f"could not inflate compressed data: {e}")
        main_and_extra_count, raw = self.unpack('B', raw)
        side_count, raw = self.unpack('B', raw)
        deck_list = {"main": [], "extra": [], "side": []}
        for _ in range(main_and_extra_count):
            code, raw = self.unpack_code(raw)
            if len(deck_list["main"]) < 40:
                deck_list["main"].append(code)
            else:
                deck_list["extra"].append(code)
        for _ in range(side_count):
            code, raw = self.unpack_code(raw)
            deck_list["side"].append(code)
        return deck_list

    def unpack_code(self, data):
        return self.unpack('I', data)

    def unpack(self, format, data):
        size = struct.calcsize(format)
        unpacked = struct.unpack(format, data[:size])
        if not unpacked:
            raise FormatDecodeException("unexpected end of input")
        return unpacked[0], data[size:]