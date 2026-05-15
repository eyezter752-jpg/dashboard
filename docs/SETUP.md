# SETUP.md — установка проекта с нуля

Полная инструкция от «вообще ничего нет» до «дашборд работает на телефоне».

---

## ШАГ 1. Установить программы (один раз на компьютере)

### 1.1. Python 3
- Скачай: https://www.python.org/downloads/
- При установке **поставь галочку** «Add Python to PATH».
- Проверь в PowerShell: `python --version` → должно быть `Python 3.10+`.

### 1.2. Git
- Скачай: https://git-scm.com/download/win
- Установи со значениями по умолчанию.
- Проверь: `git --version` → должно быть `git version 2.x`.

### 1.3. Claude Code
- Документация: https://docs.claude.com/en/docs/claude-code
- Установка (нужен Node.js 18+):
  ```bash
  npm install -g @anthropic-ai/claude-code
  ```
- Авторизация при первом запуске.

### 1.4. GitHub-аккаунт
- Зарегистрируйся на https://github.com (если ещё нет).
- В **Settings → Developer settings → Personal access tokens → Tokens (classic)**:
  - Создай токен с правами `repo` (полный доступ к репозиториям).
  - Скопируй и сохрани — он показывается ОДИН раз.

---

## ШАГ 2. Создать репозиторий

### 2.1. На GitHub
1. https://github.com/new
2. Repository name: `do-dashboard`
3. **Public** (рекомендую — Pages бесплатно работает только для public).
4. **НЕ ставь** галочку «Add README». Просто Create.

### 2.2. На своём ПК

Открой PowerShell, перейди в нужное место:
```bash
cd C:\Users\User\Desktop\CLAUDE
```

Распакуй сюда `do-dashboard-site.zip` от Claude. Должна появиться папка
`site/`. Переименуй её в `do-dashboard`:
```bash
mv site do-dashboard
cd do-dashboard
```

### 2.3. Привязать к GitHub

```bash
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/<TWOJ_LOGIN>/do-dashboard.git
git push -u origin main
```

При запросе пароля — введи свой **Personal Access Token** (не пароль аккаунта).

### 2.4. Включить GitHub Pages

1. На странице репо: **Settings → Pages**.
2. **Source: GitHub Actions**.
3. Save.
4. Вкладка **Actions** — увидишь, как пошёл деплой (1–2 минуты).
5. Когда жёлтый кружок станет зелёной галкой — твой сайт работает по адресу:
   ```
   https://<TWOJ_LOGIN>.github.io/do-dashboard/
   ```

### 2.5. Открыть на телефоне

1. Открой URL в Safari/Chrome.
2. Введи PIN: **1406**.
3. Кнопка «Поделиться» → «На экран Домой» — иконка как у нативного приложения.

---

## ШАГ 3. Установить проект локально

```bash
cd C:\Users\User\Desktop\CLAUDE\do-dashboard
python scripts/setup.py
```

Скрипт создаст папки `inbox/`, `archive/`, проверит git.

---

## ШАГ 4. Первый запуск Claude Code

В папке `do-dashboard` запусти:
```bash
claude
```

CC прочитает `CLAUDE.md` (главный контекст) и `.claude/skills/publish-dashboard/SKILL.md`.

Скажи ему:
> Это проект do-dashboard. Что ты умеешь?

Он должен ответить, что готов публиковать обновления через скил `publish-dashboard`.

---

## ШАГ 5. Ежедневный цикл (как пользоваться)

### Каждый рабочий день:

1. **В конце дня** — выгрузи 8 файлов из ITIGRIS + банка по чек-листу
   `docs/DAILY_CHECKLIST.md`.

2. **Открой чат claude.ai** с привязанным проектом, прикрепи файлы:
   > Собери JSON за DD.MM.2026 по скилу build-mobile-dashboard.

3. **Скачай JSON-файл**, который вернёт Claude. Имя будет
   `2026-MM-DD.json`.

4. **Положи файл в папку `inbox/`** проекта do-dashboard.

5. **В Claude Code скажи:**
   > опубликуй

6. CC всё сделает сам. Через 60 секунд сайт обновится.

---

## ТИПОВЫЕ ПРОБЛЕМЫ

### «git push» просит логин/пароль каждый раз
Используй Personal Access Token. Один раз введёшь его — Windows сохранит
в credential manager. Если нет — настрой SSH-ключ:
1. `ssh-keygen -t ed25519 -C "your_email"`
2. Скопируй `~/.ssh/id_ed25519.pub`.
3. На GitHub: Settings → SSH and GPG keys → New SSH key → вставь.
4. Поменяй remote на SSH:
   ```bash
   git remote set-url origin git@github.com:<TWOJ_LOGIN>/do-dashboard.git
   ```

### GitHub Pages показывает 404
Проверь:
- Pages включены в Settings (Source = GitHub Actions).
- В Actions последний workflow — зелёный.
- URL правильный: `https://<TWOJ_LOGIN>.github.io/do-dashboard/`.

### После публикации сайт показывает старые данные
- Pages кэширует. Жди до 5 минут.
- Hard refresh на телефоне: для PWA-иконки — удали и переустанови.
- Проверь `public/data/latest.json` в репо — он точно обновился?

### Claude Code говорит «inbox пуст»
Проверь, что JSON-файл реально лежит в `do-dashboard/inbox/` (не в корне,
не в Downloads, не в `public/data`).

### Валидация JSON падает
Не пытайся править JSON руками. Возвращайся в чат claude.ai, скажи:
> JSON не прошёл валидацию: <текст ошибки>. Исправь и пришли заново.
