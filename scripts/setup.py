#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup.py — одноразовая установка проекта.

Запускать после клонирования репозитория:
    python scripts/setup.py

Создаёт нужные папки, проверяет, что Git настроен, и говорит,
что делать дальше.
"""
import sys
import io
import subprocess
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent


def check_git():
    try:
        v = subprocess.run(["git", "--version"], capture_output=True, text=True)
        print(f"[OK] Git найден: {v.stdout.strip()}")
    except FileNotFoundError:
        print("[FAIL] Git не установлен. Установи: https://git-scm.com/download/win")
        return False
    # remote
    r = subprocess.run(["git", "remote", "-v"], cwd=ROOT, capture_output=True, text=True)
    if not r.stdout.strip():
        print("[WARN] Git remote не настроен. После git push сначала:")
        print("       git remote add origin https://github.com/<owner>/do-dashboard.git")
    else:
        print(f"[OK] Git remote: {r.stdout.strip().splitlines()[0]}")
    return True


def main():
    print("=" * 60)
    print("УСТАНОВКА do-dashboard")
    print("=" * 60)

    # Создаём папки
    for d in ["inbox", "archive", "public/data"]:
        p = ROOT / d
        p.mkdir(parents=True, exist_ok=True)
        keep = p / ".gitkeep"
        if not keep.exists() and not any(p.iterdir()):
            keep.touch()
        print(f"[OK] {d}/")

    check_git()

    print()
    print("=" * 60)
    print("ГОТОВО. Что дальше:")
    print("=" * 60)
    print("1. Скинь свежий JSON от Claude в папку  inbox/")
    print("2. Запусти:  python scripts/publish.py")
    print("3. Открой сайт на телефоне (PIN: 1406)")
    print()
    print("Для проверки без публикации:")
    print("   python scripts/publish.py --dry-run")


if __name__ == "__main__":
    main()
