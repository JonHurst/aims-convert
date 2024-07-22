#!/usr/bin/python3
import sys
import re
from typing import Final

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBoxHorizontal, LAParams, Rect


X0: Final = 0
Y0: Final = 1
X1: Final = 2
Y1: Final = 3
BBOX: Final = 0
TEXT: Final = 1

COLUMN = list[list[str]]
ELEMENT = tuple[Rect, str]


def raw_columns(htext_elements: list[ELEMENT]) -> list[COLUMN]:
    # find headers
    re_header = re.compile(r"^\d{2}/\d{2}$")
    headers = [X for X in htext_elements if re_header.match(X[TEXT])]
    if not headers:
        return []
    headers.sort()  # sort headers on X0
    # find top of table
    top = headers[0][BBOX][Y1]
    # find bottom of table
    bottom = -1.0
    for e in htext_elements:
        if e[TEXT] == "F" and e[BBOX][X1] < headers[0][BBOX][X0]:
            bottom = e[BBOX][Y1]
            break
    # find table elements
    table_elements = [X for X in htext_elements
                      if bottom < (X[BBOX][Y0] + X[BBOX][Y1]) / 2 < top]
    # put the elements into columns
    columns: list[list[tuple[float, str]]] = [[] for X in headers]
    fuzz = 5
    col_min = [(X[BBOX][X0] + X[BBOX][X1]) / 2 - fuzz for X in headers]
    col_max = [X + 2 * fuzz for X in col_min]
    for el in table_elements:
        centre = (el[BBOX][X0] + el[BBOX][X1]) / 2
        for c, col in enumerate(columns):
            if col_min[c] < centre < col_max[c]:
                col.append((el[BBOX][Y0], el[TEXT]))
                break
    output_columns: list[COLUMN] = []
    for col in columns:
        col.sort(key=lambda X: -X[0])
        last_y0 = col[0][0]
        output_column: COLUMN = [[]]
        for entry in col:
            if last_y0 - entry[0] > 10:
                output_column.append([])
            last_y0 = entry[0]
            output_column[-1].append(entry[1])
        output_columns.append(output_column)
    return output_columns


def htext_elements(page_layout) -> list[ELEMENT]:
    return [(X.bbox, X.get_text().strip().replace("\u200b", ""))
            for X in page_layout
            if isinstance(X, LTTextBoxHorizontal)]


def crew_lines(pages):
    output_rows = []
    re_header = re.compile(r"\d{2}/\d{2}/\d{4}")
    for htext_elements in pages:
        # try to find "Expity Dates" section header to mark bottom
        bottom = 0
        for el in htext_elements:
            if el[TEXT] == "Expiry Dates":
                bottom = el[BBOX][Y1]
        # find all crew entry row headers
        headers = [X for X in htext_elements
                   if X[BBOX][X0] < 50 and X[BBOX][Y0] > bottom
                   and re_header.match(X[TEXT])]
        if not headers:
            continue
        headers.sort(key=lambda X: -X[BBOX][Y0])  # sort headers on Y0
        # establish row boundaries
        row_centres = [(X[BBOX][Y0] + X[BBOX][Y1]) / 2 for X in headers]
        row_boundaries = [(X[0] + X[1]) / 2
                          for X in zip(row_centres[:-1], row_centres[1:])]
        row_tops = [2 * row_centres[0] - row_boundaries[0]] + row_boundaries
        row_bottoms = (row_boundaries
                       + [2 * row_centres[-1] - row_boundaries[-1]])
        # extract data
        rows = [[] for X in headers]
        for el in htext_elements:
            el_centre = (el[BBOX][Y0] + el[BBOX][Y1]) / 2
            for c, row in enumerate(rows):
                if row_bottoms[c] < el_centre < row_tops[c]:
                    row.append(el)
                    break
        # prepare output
        for row in rows:
            row.sort()
            if len(row) == 4 and row[3][BBOX][Y0] > row[2][BBOX][Y0]:
                row[2], row[3] = row[3], row[2]
            output_row = [X[TEXT] for X in row]
            if len(output_row) == 4:
                output_row[2] += " " + output_row.pop()
            output_rows.append(output_row)
        # don't process any more pages if we found "Expiry Dates"
        if bottom:
            break
    return output_rows


def main():
    pages = [htext_elements(X) for X in
             extract_pages(
                 sys.argv[1],
                 laparams=LAParams(line_margin=0.1))]
    for col in raw_columns(pages[0]):
        print(col)
    for row in crew_lines(pages):
        print(row)


if __name__ == "__main__":
    main()
