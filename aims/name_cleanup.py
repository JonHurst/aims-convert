import re


# FIXME: These obviously shouldn't be hard coded!
replacements = {
    "ROBERTS-JONES NANTL": "Roberts-Jones Nantlais",
    "TSAKALLI (STELLA) E": "Tsakalli Stella",
    "Alvarez Alvarez Sar": "Alvarez Sara",
    "SCRIMSHAW CHRISTOPH": "Scrimshaw Christopher",
    "RIVILLA RODRIGUEZ R": "Rivilla Raffa",
    "KIMBERLEY CHRISTOPH": "Kimberley Christopher",
    "KEFALLONITIS ALEXAN": "Kefallonitis Alexander",
    "HIGATE JAMES CHARLI": "Higate Charlie",
    "CUTHBERTSON BENJAMI": "Cuthbertson Benjamin",
}


def clean(name: str) -> str:
    if name in replacements:
        return replacements[name]
    parts = [X.strip().capitalize() for X in name.split()]
    for c, part in enumerate(parts):
        # remove bracketted stuff
        if part[0] == "(":
            parts[c] = None
            continue
        # remove LR, SR, 50%
        if part.upper() in {"LR", "SR", "50%"}:
            parts[c] = None
            continue
        # remove stars
        new = re.sub(r"\*+", "", part)
        # remove commas
        new = new.replace(",", "")
        # capitilize after - and '
        for char in ("-", "'"):
            index = new.find(char)
            if index not in {-1, len(new) - 1}:
                index += 1
                new = new[:index] + new[index:].capitalize()
        # capitilize after Mc
        index = new.find("Mc")
        if index == 0 and len(new) > 2:
            new = new[:2] + new[2:].capitalize()
        parts[c] = new
    return " ".join([X for X in parts if X])
