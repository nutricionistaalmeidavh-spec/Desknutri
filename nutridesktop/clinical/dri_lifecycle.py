"""Key DRI values by life stage.

Structured reference support for nutrients represented by the current TACO
schema. Values are versioned clinical content and are not automatic clinical
prescriptions.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class DRI:
    nutrient: str
    value: float
    unit: str
    kind: str = "RDA"


TABLE = {
    ("0-6m", "U"): {
        "calcio": DRI("Cálcio", 200, "mg", "AI"),
        "ferro": DRI("Ferro", 0.27, "mg", "AI"),
        "zinco": DRI("Zinco", 2, "mg", "AI"),
        "vitamina_c": DRI("Vitamina C", 40, "mg", "AI"),
    },
    ("7-12m", "U"): {
        "calcio": DRI("Cálcio", 260, "mg", "AI"),
        "ferro": DRI("Ferro", 11, "mg"),
        "zinco": DRI("Zinco", 3, "mg"),
        "vitamina_c": DRI("Vitamina C", 50, "mg", "AI"),
    },
    ("1-3", "U"): {"calcio": DRI("Cálcio", 700, "mg"), "ferro": DRI("Ferro", 7, "mg"), "zinco": DRI("Zinco", 3, "mg"), "vitamina_c": DRI("Vitamina C", 15, "mg")},
    ("4-8", "U"): {"calcio": DRI("Cálcio", 1000, "mg"), "ferro": DRI("Ferro", 10, "mg"), "zinco": DRI("Zinco", 5, "mg"), "vitamina_c": DRI("Vitamina C", 25, "mg")},
    ("9-13", "M"): {"calcio": DRI("Cálcio", 1300, "mg"), "ferro": DRI("Ferro", 8, "mg"), "zinco": DRI("Zinco", 8, "mg"), "vitamina_c": DRI("Vitamina C", 45, "mg")},
    ("9-13", "F"): {"calcio": DRI("Cálcio", 1300, "mg"), "ferro": DRI("Ferro", 8, "mg"), "zinco": DRI("Zinco", 8, "mg"), "vitamina_c": DRI("Vitamina C", 45, "mg")},
    ("14-18", "M"): {"calcio": DRI("Cálcio", 1300, "mg"), "ferro": DRI("Ferro", 11, "mg"), "zinco": DRI("Zinco", 11, "mg"), "vitamina_c": DRI("Vitamina C", 75, "mg")},
    ("14-18", "F"): {"calcio": DRI("Cálcio", 1300, "mg"), "ferro": DRI("Ferro", 15, "mg"), "zinco": DRI("Zinco", 9, "mg"), "vitamina_c": DRI("Vitamina C", 65, "mg")},
    ("19-50", "M"): {"calcio": DRI("Cálcio", 1000, "mg"), "ferro": DRI("Ferro", 8, "mg"), "zinco": DRI("Zinco", 11, "mg"), "vitamina_c": DRI("Vitamina C", 90, "mg")},
    ("19-50", "F"): {"calcio": DRI("Cálcio", 1000, "mg"), "ferro": DRI("Ferro", 18, "mg"), "zinco": DRI("Zinco", 8, "mg"), "vitamina_c": DRI("Vitamina C", 75, "mg")},
    ("51-70", "M"): {"calcio": DRI("Cálcio", 1000, "mg"), "ferro": DRI("Ferro", 8, "mg"), "zinco": DRI("Zinco", 11, "mg"), "vitamina_c": DRI("Vitamina C", 90, "mg")},
    ("51+", "F"): {"calcio": DRI("Cálcio", 1200, "mg"), "ferro": DRI("Ferro", 8, "mg"), "zinco": DRI("Zinco", 8, "mg"), "vitamina_c": DRI("Vitamina C", 75, "mg")},
    ("71+", "M"): {"calcio": DRI("Cálcio", 1200, "mg"), "ferro": DRI("Ferro", 8, "mg"), "zinco": DRI("Zinco", 11, "mg"), "vitamina_c": DRI("Vitamina C", 90, "mg")},
    ("gestante14-18", "F"): {"calcio": DRI("Cálcio", 1300, "mg"), "ferro": DRI("Ferro", 27, "mg"), "zinco": DRI("Zinco", 12, "mg"), "vitamina_c": DRI("Vitamina C", 80, "mg")},
    ("gestante19+", "F"): {"calcio": DRI("Cálcio", 1000, "mg"), "ferro": DRI("Ferro", 27, "mg"), "zinco": DRI("Zinco", 11, "mg"), "vitamina_c": DRI("Vitamina C", 85, "mg")},
    ("lactante14-18", "F"): {"calcio": DRI("Cálcio", 1300, "mg"), "ferro": DRI("Ferro", 10, "mg"), "zinco": DRI("Zinco", 13, "mg"), "vitamina_c": DRI("Vitamina C", 115, "mg")},
    ("lactante19+", "F"): {"calcio": DRI("Cálcio", 1000, "mg"), "ferro": DRI("Ferro", 9, "mg"), "zinco": DRI("Zinco", 12, "mg"), "vitamina_c": DRI("Vitamina C", 120, "mg")},
}


def stage_for(age, sex, pregnant=False, lactating=False):
    if pregnant:
        return ("gestante14-18" if age < 19 else "gestante19+", "F")
    if lactating:
        return ("lactante14-18" if age < 19 else "lactante19+", "F")
    if age < 0.583:
        return ("0-6m", "U")
    if age < 1:
        return ("7-12m", "U")
    if age < 4:
        return ("1-3", "U")
    if age < 9:
        return ("4-8", "U")
    if age < 14:
        return ("9-13", sex)
    if age < 19:
        return ("14-18", sex)
    if age <= 50:
        return ("19-50", sex)
    if sex == "F":
        return ("51+", "F")
    if age <= 70:
        return ("51-70", "M")
    return ("71+", "M")


def recommendations(age, sex, pregnant=False, lactating=False):
    return TABLE.get(stage_for(float(age), sex, pregnant, lactating), {})
