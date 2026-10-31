from dataclasses import dataclass


@dataclass(frozen=True)
class EndingInfo:
    flag: int
    route: str
    alignment: str
    label: str
    description: str

    @property
    def canon(self) -> str:
        return f"Canon of {self.route}"

    @property
    def full_label(self) -> str:
        return f"{self.canon} — {self.label}"


ENDING_INFOS = [
    EndingInfo(
        0x01,
        "Creation",
        "Neutral",
        "Neutral",
        "The neutral ending of the Canon of Creation.",
    ),
    EndingInfo(
        0x02,
        "Creation",
        "Law",
        "Law",
        "The Law ending of the Canon of Creation.",
    ),
    EndingInfo(
        0x04,
        "Creation",
        "Chaos",
        "Chaos",
        "The Chaos ending of the Canon of Creation.",
    ),
    EndingInfo(
        0x08,
        "Creation",
        "True Neutral",
        "True Neutral (Secret)",
        "The true neutral / secret ending of the Canon of Creation.",
    ),
    EndingInfo(
        0x10,
        "Vengeance",
        "Law",
        "Law",
        "The Law ending of the Canon of Vengeance.",
    ),
    EndingInfo(
        0x20,
        "Vengeance",
        "Chaos",
        "Chaos",
        "The Chaos ending of the Canon of Vengeance.",
    ),
]

ENDING_ROUTES = ("Creation", "Vengeance")

CANON_DESCRIPTIONS = {
    "Creation": "The original Shin Megami Tensei V storyline.",
    "Vengeance": "The Canon of Vengeance storyline.",
}
