# JSON_SCHEMA.md — структура `public/data/YYYY-MM-DD.json`

Это **контракт** между двумя сторонами:
- **Claude в чате** (claude.ai) — формирует JSON по `skills/build-mobile-dashboard/SKILL.md`
- **Сайт `dashboard.html`** — читает JSON и рендерит UI

**Если меняется структура — обязательно обновить:** скил, схему, рендер `app.js`. Все три файла должны быть в синхронной версии (`meta.version`).

---

## Версии

- **1.0** (2026-05-14) — начальная версия

---

## Полная схема

```jsonc
{
  "meta": {
    "date":          "YYYY-MM-DD",          // дата дня
    "date_display":  "DD.MM.YYYY, дн",      // для шапки
    "updated_at":    "ISO-8601",            // когда собран JSON
    "version":       "1.0",                 // версия схемы
    "source_files":  [ "имя1", "имя2", ... ],
    "warnings":      [ "текст 1", ... ]     // опционально
  },

  "stoplight": {
    "color": "green|amber|red",
    "label": "короткий текст в шапке"
  },

  "money_now": {
    "total":         123456,                // ₽, целое
    "status_color":  "green|amber|red",
    "status_label":  "текст рядом",
    "accounts": [
      { "name": "Р/с Сбер ООО", "value": 479638 },
      { "name": "...",          "value": 0      }
    ]
  },

  "overdraft": {
    "used":             1168594,
    "free":              331406,
    "limit":            1500000,
    "percent":               78,
    "color":          "green|amber|red",
    "kbb_balance":        61157,
    "due_date":      "15.06.2026",
    "monthly_interest":   35000
  },

  "stock": {
    "uncompleted_orders": {
      "to_pay":     310987,    // К ДОПЛАТЕ клиентами
      "orders_qty":    114,
      "older_30d":       3
    },
    "warehouse_cost": 3281244,  // склад по закупке
    "warehouse_sale": 5906000,  // склад по продажным ценам
    "suppliers_debt": 1288029
  },

  "payment_calendar": {
    "next_7_days":  461050,    // план на 7 дней вперёд (минус факт)
    "next_14_days": 718390,    // план на 14 дней вперёд (минус факт)
    "note":         "пояснение"
  },

  "pending_payments": {
    "total": 626350,
    "future": {                  // дата > сегодня — точно ещё ждут
      "total": 27167,
      "count": 4,
      "items": [
        {
          "recipient": "ООО ...",
          "amount":    20400,
          "date":      "DD.MM",
          "purpose":   "короткое описание"
        }
      ]
    },
    "past_or_undated": {         // дата ≤ сегодня или нет даты
      "total": 599183,
      "count": 11,
      "note":  "могут быть уже списаны",
      "items": [ ... ]
    }
  },

  "loans": {
    "total":             14403112,
    "active_qty":              10,
    "frozen_qty":               1,
    "monthly_payment":     431390,
    "interest_part":       240283,
    "interest_percent":        57,
    "body_part":           182060,
    "body_percent":            43,
    "items": [
      {
        "id":       "KBB_OVER",       // строковый ID, стабильный между днями
        "name":     "КББ Овердрафт",
        "priority": true,             // подсветка красным (досрочка)
        "warning":  false,            // подсветка жёлтым (% only / риск)
        "frozen":   false,            // приглушённо (заморожен)
        "tag":      "досрочка",       // короткая плашка (опц.)
        "payment":  35000,
        "balance":  1168594,
        "rate":     "22,9%",          // строкой как в реестре
        "type":     "% only",
        "due":      "15.06.2026"
      }
    ]
  },

  "sales": {
    "kpi": {
      "gross_profit":      156197,
      "margin_percent":     75.2,
      "revenue":           207668,
      "items_qty":            115,
      "cash":              149070,
      "checks_qty":            62,
      "refunds":            -8950,
      "refunds_note":  "Дружбы товар"
    },
    "glasses": {
      "total_qty":   26,
      "total_sum":   107823,
      "bardina":    { "qty":23, "sum":89023 },
      "druzhby":    { "qty":3,  "sum":18800 },
      "lenses":     { "qty":18, "sum":86940 },
      "frames":     { "qty":8,  "sum":20883 }
    },
    "mkl": {
      "total_qty": 8,
      "total_sum": 14050,
      "bardina":  { "qty":0, "sum":0 },
      "druzhby":  { "qty":8, "sum":14050 }
    },
    "services": {
      "total_qty": 69,
      "total_sum": 75850,
      "items": [
        { "name":"ОКТ (все виды)", "qty":16, "sum":32500 }
      ]
    },
    "other": {
      "total_qty": 16,
      "total_sum": 10045,
      "items": [
        { "name":"Аксессуары", "qty":14, "sum":5245 }
      ]
    }
  }
}
```

---

## Правила полей

### Числа
- **Все суммы — целые рубли**. Без копеек, без разделителей. Например: `156197` (не `156 197` и не `156197.00`).
- **Маржа** — `float`, 1 знак после запятой (например `75.2`).
- **Процент овердрафта** — `int`.
- **Отрицательные значения** допустимы только в `sales.kpi.refunds` (возвраты).

### Цвета
Везде только три значения: `"green"`, `"amber"`, `"red"`. Никаких хексов.

### Даты
- `meta.date` → `"YYYY-MM-DD"` (для сортировки)
- `meta.date_display`, `pending_payments.items[].date`, `loans.items[].due`, `overdraft.due_date` → `"DD.MM"` или `"DD.MM.YYYY"` (для отображения)

### Опциональные поля
- `meta.warnings` — можно не передавать, если пусто
- `loans.items[].priority/warning/frozen/tag/type` — каждое опционально
- `stock.warehouse_sale` — может быть `null` если нет свежего среза
- `pending_payments.future.items[].date` — может быть `"—"` если в источнике нет даты

### Если данных нет
Поле либо `null`, либо 0. В `meta.warnings` объяснить.

---

## Контрольные суммы (валидация)

Сайт `app.js` при загрузке JSON проверяет и красным флагом показывает, если:
- `money_now.total ≠ Σ money_now.accounts[].value`
- `overdraft.used + overdraft.free ≠ overdraft.limit`
- `pending_payments.total ≠ future.total + past_or_undated.total`
- `loans.total ≠ Σ loans.items[].balance` (без frozen)

Это страховка от опечаток в JSON.
