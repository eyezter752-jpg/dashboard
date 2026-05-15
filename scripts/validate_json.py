#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_json.py — проверка структуры одного файла.

Использование:
    python scripts/validate_json.py inbox/2026-05-14.json

Код возврата:
    0 — OK
    1 — найдены ошибки (текст в stdout)
    2 — файл не существует или не JSON
"""
import sys
import io
import json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REQUIRED_KEYS = ["meta", "stoplight", "money_now", "overdraft", "stock",
                 "payment_calendar", "pending_payments", "loans", "sales"]


def main():
    if len(sys.argv) != 2:
        print("[FAIL] Использование: python validate_json.py <файл.json>")
        sys.exit(2)

    p = Path(sys.argv[1])
    if not p.exists():
        print(f"[FAIL] Файл не найден: {p}")
        sys.exit(2)

    try:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[FAIL] Некорректный JSON: {e}")
        sys.exit(2)

    errs = []

    # 1. Обязательные секции
    for k in REQUIRED_KEYS:
        if k not in d:
            errs.append(f"отсутствует секция {k!r}")
    if errs:
        for e in errs:
            print(f"[FAIL] {e}")
        sys.exit(1)

    # 2. Дата
    if d["meta"].get("date") != p.stem:
        errs.append(f"meta.date={d['meta'].get('date')} != имя файла {p.stem}")

    # 3. Контрольные суммы
    s_acc = sum(a["value"] for a in d["money_now"]["accounts"])
    if abs(d["money_now"]["total"] - s_acc) > 1:
        errs.append(f"money_now.total ({d['money_now']['total']}) != Σ accounts ({s_acc})")

    od = d["overdraft"]
    if abs(od["used"] + od["free"] - od["limit"]) > 1:
        errs.append("overdraft: used + free != limit")

    pp = d["pending_payments"]
    if abs(pp["total"] - pp["future"]["total"] - pp["past_or_undated"]["total"]) > 1:
        errs.append("pending_payments: total != future + past")

    ver = d["meta"].get("version", "?")
    if ver not in ("1.0",):
        errs.append(f"неподдерживаемая версия схемы: {ver}")

    if errs:
        for e in errs:
            print(f"[FAIL] {e}")
        sys.exit(1)

    print(f"[OK] {p.name} валиден")
    print(f"     дата: {d['meta']['date']}")
    print(f"     счетов: {len(d['money_now']['accounts'])}")
    print(f"     займов: {len(d['loans']['items'])}")
    print(f"     поручений: {pp['future']['count'] + pp['past_or_undated']['count']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
