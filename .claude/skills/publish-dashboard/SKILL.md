# SKILL: publish-dashboard

> Версия: 1.0 · Платформа: Windows + Git Bash / PowerShell
> Главный скил Claude Code в проекте do-dashboard.

## КОГДА АКТИВИРУЕТСЯ

Любая из реплик Ивана:
- «опубликуй» / «опубликовать»
- «обнови дашборд» / «обнови сайт»
- «publish» / «push dashboard»
- «выложи на гитхаб»

Альтернативно — режим dry-run (только посмотреть, без push):
- «publish dry-run»
- «опубликуй без push»
- «проверь что в inbox»

## ЧТО ДЕЛАТЬ — ПОШАГОВЫЙ АЛГОРИТМ

### Шаг 1. Проверить состояние Git
```bash
git status --porcelain
git branch --show-current
```
Если есть незакоммиченные изменения вне `public/data/` — STATUS=WARN,
показать что не закоммичено, спросить Ивана: «есть лишние изменения,
продолжить?». Без явного «да» — НЕ продолжать.

### Шаг 2. Найти JSON в inbox
```python
from pathlib import Path
inbox = Path("inbox")
files = sorted(inbox.glob("*.json"))
```
- Если `files == []` → вывести `[INFO] inbox пуст, нечего публиковать` и выйти со STATUS=OK.
- Если файлов несколько → обработать каждый отдельной транзакцией, по очереди от старшей даты к младшей.

### Шаг 3. Валидация каждого файла
Запустить `python scripts/validate_json.py inbox/FILENAME.json`.
Скрипт вернёт код 0 (OK) или ненулевой (FAIL).

Проверяется:
- Файл — корректный JSON.
- Присутствуют все обязательные секции (см. `docs/JSON_SCHEMA.md`).
- `meta.date` соответствует имени файла.
- Контрольные суммы (money_now, overdraft, pending, loans) сходятся.
- `meta.version` поддерживается сайтом (сейчас 1.0).

Если **FAIL** → STATUS=FAIL, показать вывод валидатора, **НЕ копировать,
НЕ коммитить**. Сказать Ивану: «JSON не валиден, вернись к Claude в чат».

### Шаг 4. Копирование (атомарно)
Для каждого валидного `inbox/YYYY-MM-DD.json`:
```bash
cp inbox/YYYY-MM-DD.json public/data/YYYY-MM-DD.json
cp inbox/YYYY-MM-DD.json public/data/latest.json
```
Использовать `shutil.copy2` (сохраняет таймштампы).

### Шаг 5. Перенос в архив
```bash
mkdir -p archive/YYYY-MM/
mv inbox/YYYY-MM-DD.json archive/YYYY-MM/YYYY-MM-DD.json
```

### Шаг 6. Git операции
```bash
git add public/data/ archive/
git status --short                           # для отчёта
git diff --stat HEAD                         # сколько изменилось
git commit -m "data: dashboard YYYY-MM-DD"
git push origin main
```

**Обёрнуть всё в try/except** (Правило 2 из CLAUDE.md):
```python
try:
    subprocess.run(["git","add","public/data/","archive/"], check=True)
    subprocess.run(["git","commit","-m",f"data: dashboard {date}"], check=True)
    push = subprocess.run(["git","push","origin","main"], capture_output=True, text=True)
    pushed = (push.returncode == 0)
except subprocess.CalledProcessError as e:
    pushed = False; err = str(e)
```

### Шаг 7. Verify-on-disk
```bash
git log -1 --format="%h %s (%ar)"
git status
```
В отчёт ВКЛЮЧИТЬ реальный вывод этих команд.

### Шаг 8. Финальный отчёт (формат)

```
STATUS: OK
============================================
ПУБЛИКАЦИЯ ДАШБОРДА — 2026-05-14
============================================
Время: 2026-05-14 23:50:12 +07:00

[ВАЛИДАЦИЯ]
  inbox/2026-05-14.json: OK
  Все контрольные суммы сошлись.

[ФАЙЛЫ]
  Скопировано: public/data/2026-05-14.json
  Обновлено:   public/data/latest.json
  Архив:       archive/2026-05/2026-05-14.json

[GIT]
  Commit: 4f8a2c1 data: dashboard 2026-05-14
  Push:   OK (origin/main)

[ВАЛИДАЦИЯ ДАННЫХ]
  money_now.total:        1 207 353 ₽
  overdraft:              78% (1 168 594 / 1 500 000)
  выручка дня:            207 668 ₽
  валовая прибыль:        156 197 ₽
  поручений в банке:      15 (626 350 ₽)

[ДЕПЛОЙ]
  GitHub Actions запустится автоматически.
  Сайт обновится через ~60 секунд:
  https://<owner>.github.io/do-dashboard/

[NEXT]
  Открой на телефоне, проверь свежесть данных.
```

Для **dry-run** — те же шаги 1–3, но без 4–7. В конце:
```
STATUS: DRY-RUN
Найдено в inbox: N файлов.
Валидация пройдена: N/N
Что произошло бы при publish:
  - копирование в public/data/...
  - перенос в archive/...
  - git commit + push
Запустить публикацию командой: "опубликуй"
```

## ЕСЛИ ЧТО-ТО СЛОМАЛОСЬ

### Сценарий 1 — push отклонён (не fast-forward)
```bash
git pull --rebase origin main
git push origin main
```
Это может произойти, если кто-то правил репо через web UI.

### Сценарий 2 — auth failed
Не пытаться чинить. Сказать:
> «Авторизация Git не настроена. Проверь `git remote -v` и SSH-ключ /
> personal access token.» Дать ссылку: `docs/SETUP.md` секция «Git auth».

### Сценарий 3 — JSON не валиден
**НЕ исправлять данные.** Показать вывод `validate_json.py`. Сказать:
> «JSON не валидируется. Вернись в claude.ai к скилу
> build-mobile-dashboard, попроси Claude исправить.»

### Сценарий 4 — inbox имеет файл со старой датой (например JSON за 2026-04-30,
а у нас уже есть public/data/2026-04-30.json)
Спросить Ивана: «Перезаписать существующий 2026-04-30.json?». Без явного
«да» — не перезаписывать.

### Сценарий 5 — конфликт в public/data/latest.json
Это всегда «их перезаписать». latest.json — служебный, история не нужна.
```bash
git checkout --theirs public/data/latest.json
```

## ANTI-PATTERNS (нельзя)

- ❌ Не запускать `git push --force`.
- ❌ Не удалять файлы из `inbox/` без копирования в `archive/`.
- ❌ Не перезаписывать существующий JSON в `public/data/` без подтверждения.
- ❌ Не редактировать содержимое JSON. Только перемещать файлы.
- ❌ Не запускать `git commit` если `git status` показывает только
  пробельные изменения — это шум.
