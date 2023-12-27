import re


def clean(name: str) -> str:
    parts = [X.strip().capitalize() for X in name.split()]
    for c, part in enumerate(parts):
        # remove bracketted stuff
        if part[0] == "(":
            parts[c] = ""
            continue
        # remove LR, SR, 50%
        if part.upper() in {"LR", "SR", "50%"}:
            parts[c] = ""
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
