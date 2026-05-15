# Доктор Оптика — Дашборд

Мобильный дашборд для собственника, обновляется через Claude Code за 10 секунд.
PIN на входе: **1406**.

## Быстрый старт

Если только клонировал:
```bash
python scripts/setup.py
```

Каждый день:
1. Получаешь JSON от Claude (claude.ai) → кидаешь в `inbox/`.
2. В Claude Code: `опубликуй`.
3. Через 60 сек открываешь сайт на телефоне.

Подробная установка с нуля: [`docs/SETUP.md`](docs/SETUP.md).

## Структура

| Папка | Что внутри |
|---|---|
| `inbox/` | Сюда кидаешь свежий JSON. Claude Code заберёт. |
| `archive/` | Обработанные JSON по месяцам (`archive/2026-05/...`). |
| `public/` | Сайт. То, что отдаётся в браузер. |
| `public/data/latest.json` | Читается сайтом. |
| `public/data/YYYY-MM-DD.json` | Архив дней в Git. |
| `.claude/skills/publish-dashboard/` | Скил для CC: что делать по команде «опубликуй». |
| `scripts/` | `publish.py` — главный оркестратор. |
| `docs/` | SETUP, ARCHITECTURE, JSON_SCHEMA, DAILY_CHECKLIST. |

## Команды для Claude Code

| Команда | Что делает |
|---|---|
| `опубликуй` / `publish` | Полный цикл: валидация → копирование → git push |
| `publish dry-run` | То же, но без push. Просто посмотреть. |
| `проверь inbox` | Что лежит в inbox, валидно ли. |

## Команды вручную (если нужно)

```bash
python scripts/publish.py              # боевой режим
python scripts/publish.py --dry-run    # без push
python scripts/validate_json.py inbox/2026-05-14.json
```

## Что НЕ делать

- Не редактировать `public/data/*.json` вручную в Git.
- Не удалять файлы из `archive/` — это история.
- Не запускать `git push --force`.

См. [`CLAUDE.md`](CLAUDE.md) — главный контекст для Claude Code.
