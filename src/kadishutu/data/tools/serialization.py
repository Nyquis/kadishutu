from typing import Any

from mashumaro import field_options


def hex_int_decode(txt: str) -> int:
    return int(txt, 16)


def hex_int_encoder(t: int, padding: int = 0) -> str:
    unpadded_hex = hex(t)[2:]
    return "0x" + unpadded_hex.rjust(padding, "0")


def hex_int_config(padding: int = 0) -> dict[str, Any]:
    return field_options(
        serialize=lambda x: hex_int_encoder(x, padding),
        deserialize=hex_int_decode,
    )


def bytes_config(size: int) -> dict[str, Any]:
    strlen = size * 2
    return field_options(
        serialize=lambda t: t.hex().rjust(strlen, "0"),
        deserialize=bytes.fromhex,
    )
