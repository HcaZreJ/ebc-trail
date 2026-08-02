"""装备清单全量表。"""
from .csvio import cite, read_csv
from .tables import table

# CSV 的列名是英文，报告里给中文表头；末列是出处，转成 citation 标记后由装配最后一步展开成角标。
HEAD = ["分类", "物品", "数量", "优先级", "放哪", "购买或租赁", "备注", "出处"]


def tokens():
    rows = read_csv("packing-list.csv")
    body = [row[:-1] + [cite(row[-1])] for row in rows[1:]]
    return {"TBL_PACKING": table([HEAD] + body)}
