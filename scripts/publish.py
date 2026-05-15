#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publish.py — оркестратор публикации дашборда.

Один проход:
  1. Найти JSON в inbox/
  2. Валидировать
  3. Скопировать в public/data/<DATE>.json + public/data/latest.json
  4. Переместить inbox/<DATE>.json в archive/YYYY-MM/<DATE>.json
  5. git add + commit + push
  6. Verify-on-disk + отчёт

Использование:
    python scripts/publish.py              # боевой режим
    python scripts/publish.py --dry-run    # без копирования и push
"""
import sys
import io
import json
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Правило 1 — ASCII в stdout. Перенаправляем поток на UTF-8 безопасно.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "inbox"
ARCHIVE = ROOT / "archive"
DATA = ROOT / "public" / "data"

REQUIRED_KEYS = ["meta", "stoplight", "money_now", "overdraft", "stock",
                 "payment_calendar", "pending_payments", "loans", "sales"]


def log(level, msg):
    print(f"[{level}] {msg}")


def run(cmd, check=True, capture=True):
    """Запустить shell-команду в корне репо."""
    r = subprocess.run(cmd, cwd=ROOT, check=False,
                       capture_output=capture, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        raise RuntimeError(
            f"Команда {' '.join(cmd)} упала (rc={r.returncode}):\n"
            f"stdout: {r.stdout}\nstderr: {r.stderr}"
        )
    return r


# ============================================================
# ВАЛИДАЦИЯ JSON (правила из docs/JSON_SCHEMA.md)
# ============================================================
def validate(path):
    errs = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
    except json.JSONDecodeError as e:
        return None, [f"некорректный JSON: {e}"]

    # 1. Обязательные секции
    for k in REQUIRED_KEYS:
        if k not in d:
            errs.append(f"отсутствует секция {k!r}")
    if errs:
        return d, errs

    # 2. Дата в имени файла = meta.date
    date_in_name = path.stem  # 2026-05-14
    if d["meta"].get("date") != date_in_name:
        errs.append(f"meta.date={d['meta'].get('date')} != имя файла {date_in_name}")

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

    # 4. Версия
    ver = d["meta"].get("version", "?")
    if ver not in ("1.0",):
        errs.append(f"неподдерживаемая версия схемы: {ver}")

    return d, errs


# ============================================================
# GIT-ОПЕРАЦИИ
# ============================================================
def git_status():
    return run(["git", "status", "--porcelain"]).stdout.strip()


def git_current_branch():
    return run(["git", "branch", "--show-current"]).stdout.strip()


def git_has_remote_main_ahead():
    """Проверить, не отстал ли локальный main от origin/main."""
    try:
        run(["git", "fetch", "origin"], check=False)
        ahead_behind = run(["git", "rev-list", "--left-right", "--count",
                            "HEAD...origin/main"]).stdout.strip()
        a, b = ahead_behind.split()
        return int(a), int(b)
    except Exception:
        return 0, 0


def git_publish(date_str):
    """git add + commit + push с обработкой ошибок."""
    run(["git", "add", "public/data/", "archive/"])
    # Если нечего коммитить (вдруг)
    if not run(["git", "diff", "--cached", "--name-only"]).stdout.strip():
        return False, "ничего не закоммичено (нет изменений)"
    run(["git", "commit", "-m", f"data: dashboard {date_str}"])

    push = run(["git", "push", "origin", "main"], check=False)
    if push.returncode == 0:
        return True, push.stdout + push.stderr
    # Попытка fast-forward через rebase
    log("WARN", "push отклонён, пробую git pull --rebase")
    pull = run(["git", "pull", "--rebase", "origin", "main"], check=False)
    if pull.returncode != 0:
        return False, "pull --rebase упал:\n" + pull.stdout + pull.stderr
    push2 = run(["git", "push", "origin", "main"], check=False)
    if push2.returncode == 0:
        return True, push2.stdout + push2.stderr
    return False, "повторный push упал:\n" + push2.stdout + push2.stderr


def git_last_commit():
    return run(["git", "log", "-1", "--format=%h %s (%ar)"]).stdout.strip()


def git_remote_url():
    return run(["git", "remote", "get-url", "origin"]).stdout.strip()


# ============================================================
# ГЛАВНЫЙ ЦИКЛ
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="ничего не копировать и не пушить")
    args = parser.parse_args()

    print()
    print("=" * 60)
    print(f"ПУБЛИКАЦИЯ ДАШБОРДА {'(DRY-RUN)' if args.dry_run else ''}")
    print("=" * 60)
    print(f"Время: {datetime.now().isoformat(timespec='seconds')}")
    print()

    # 1. Проверки окружения
    if not (ROOT / ".git").exists():
        log("FAIL", "не похоже на Git-репозиторий")
        sys.exit(2)

    branch = git_current_branch()
    if branch != "main":
        log("WARN", f"текущая ветка {branch}, ожидалась main. Продолжать опасно.")

    dirty = git_status()
    relevant_dirty = [ln for ln in dirty.split("\n")
                      if ln and not ln[3:].startswith("public/data/")
                      and not ln[3:].startswith("archive/")
                      and not ln[3:].startswith("inbox/")]
    if relevant_dirty:
        log("WARN", "есть незакоммиченные изменения вне data/archive/inbox:")
        for ln in relevant_dirty:
            print("  " + ln)
        log("INFO", "продолжаю — эти изменения НЕ войдут в коммит.")

    # 2. Inbox
    if not INBOX.exists():
        INBOX.mkdir()
    files = sorted(INBOX.glob("*.json"))
    if not files:
        log("INFO", "inbox пуст, нечего публиковать")
        print("\nSTATUS: OK")
        return 0

    log("INFO", f"найдено в inbox: {len(files)} файлов")

    # 3. Обрабатываем по очереди
    successes, failures = [], []

    for src in files:
        date_str = src.stem
        print()
        print(f"--- {src.name} ---")

        d, errs = validate(src)
        if errs:
            log("FAIL", f"валидация не пройдена ({len(errs)} ошибок):")
            for e in errs:
                print(f"  - {e}")
            failures.append((src, errs))
            continue
        log("OK", "JSON валиден")

        if args.dry_run:
            log("INFO", "DRY-RUN: пропускаю копирование и git")
            successes.append((src, None))
            continue

        # 4. Копируем
        dst_archive_full = DATA / src.name
        dst_latest = DATA / "latest.json"
        if dst_archive_full.exists():
            log("WARN", f"public/data/{src.name} уже существует — перезаписываю")
        shutil.copy2(src, dst_archive_full)
        shutil.copy2(src, dst_latest)
        log("OK", f"скопировано → public/data/{src.name} и latest.json")

        # 5. Архив
        year_month = src.stem[:7]  # 2026-05
        archive_dir = ARCHIVE / year_month
        archive_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), archive_dir / src.name)
        log("OK", f"исходник → archive/{year_month}/{src.name}")

        # 6. Git
        pushed, msg = git_publish(date_str)
        if pushed:
            log("OK", "git push успешен")
            successes.append((src, d))
        else:
            log("FAIL", f"git push провалился: {msg}")
            failures.append((src, [msg]))

    # 7. Итог
    print()
    print("=" * 60)
    if failures:
        print("STATUS: FAIL")
        print(f"Успешно: {len(successes)} / Провалено: {len(failures)}")
        for src, errs in failures:
            print(f"\n  {src.name}:")
            for e in errs:
                print(f"    - {e}")
        sys.exit(1)
    else:
        print("STATUS: OK" if not args.dry_run else "STATUS: DRY-RUN OK")
        print(f"Обработано файлов: {len(successes)}")
        if not args.dry_run and successes:
            print(f"Последний commit: {git_last_commit()}")
            remote = git_remote_url()
            owner = "<owner>"
            if "github.com" in remote:
                # извлечь owner/repo из URL
                tail = remote.split("github.com")[1].lstrip(":/").rstrip(".git")
                owner = tail.split("/")[0]
            print(f"\nДеплой займёт ~60 секунд.")
            print(f"Открой на телефоне: https://{owner}.github.io/do-dashboard/")
        # Краткая сводка по последнему
        if successes and successes[-1][1]:
            d = successes[-1][1]
            print(f"\nКлючевые цифры дня:")
            print(f"  Деньги на счетах:   {d['money_now']['total']:,} ₽".replace(",", " "))
            print(f"  Овердрафт:          {d['overdraft']['percent']}%")
            print(f"  Касса дня:          {d['sales']['kpi']['cash']:,} ₽".replace(",", " "))
            print(f"  Валовая прибыль:    {d['sales']['kpi']['gross_profit']:,} ₽".replace(",", " "))
            pp = d['pending_payments']
            print(f"  Поручений в банке:  {pp['future']['count'] + pp['past_or_undated']['count']} ({pp['total']:,} ₽)".replace(",", " "))
    return 0


if __name__ == "__main__":
    sys.exit(main())
