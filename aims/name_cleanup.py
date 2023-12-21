import re


# FIXME: These obviously shouldn't be hard coded!
replacement_list = (
    ("Alexan", "Alexander"),
    ("Nantl", "Nantlais"),
    ("Christoph", "Christopher"),
    ("Benjami", "Benjamin"),
    ("E", "Stella")
)


def clean(name: str) -> str:
    parts = [X.strip().capitalize() for X in name.split()]
    for c, part in enumerate(parts):
        for r in replacement_list:
            if part == r[0]:
                parts[c] = r[1]
                break
    s = " ".join(parts)
    s = re.sub(r"\*+", "", s)
    for char in ("-", "'"):
        index = s.find(char)
        if index not in {-1, len(s) - 1}:
            index += 1
            s = s[:index] + s[index:].capitalize()
    index = s.find("Mc")
    if index != -1:
        s = s[:index] + s[index:].capitalize()
    return s
