"""装备清单全量表。"""
from .csvio import read_csv
from .tables import table


def tokens():
    return {"TBL_PACKING": table(read_csv("packing-list.csv"))}
