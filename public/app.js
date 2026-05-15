// ============================================================
// Доктор Оптика — рендер дашборда из latest.json
// ============================================================

// 1. Проверка авторизации
(function checkAuth(){
  const exp = parseInt(sessionStorage.getItem('do_auth_exp') || '0', 10);
  if (!exp || Date.now() > exp){
    location.href = 'index.html';
  }
})();

// 2. Форматтеры
const fmt = n => (n == null ? '—' : Math.round(n).toLocaleString('ru-RU').replace(/,/g,' '));
const fmtR = n => fmt(n) + ' ₽';
const fmtRsign = n => (n > 0 ? '+ ' : (n < 0 ? '− ' : '')) + fmt(Math.abs(n)) + ' ₽';

// 3. Загрузка данных (с обходом кэша)
async function loadData(){
  const url = 'data/latest.json?t=' + Date.now();
  try{
    const r = await fetch(url, {cache:'no-store'});
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return await r.json();
  } catch(e){
    document.body.innerHTML = '<div style="padding:40px;text-align:center;color:#ef4444">' +
      '<h2>Не удалось загрузить данные</h2><p>' + e.message + '</p>' +
      '<p style="color:#9aa7bd">Проверь, что файл <code>data/latest.json</code> существует.</p>' +
      '</div>';
    throw e;
  }
}

// 4. Главная функция рендера
async function render(){
  const d = await loadData();

  // === Шапка ===
  document.getElementById('hdr-sub').textContent = d.meta.date_display + ' · обновлено ' + d.meta.updated_at.slice(11,16);
  document.getElementById('footer-date').textContent = d.meta.date_display;
  document.getElementById('footer-ver').textContent = d.meta.version;

  // Светофор
  const sl = document.getElementById('stoplight');
  sl.classList.remove('green','amber','red');
  sl.classList.add(d.stoplight.color);
  document.getElementById('stoplight-label').textContent = d.stoplight.label;

  // === БЛОК: Деньги сейчас ===
  document.getElementById('money-total').innerHTML = fmt(d.money_now.total) + '<span class="cur">₽</span>';
  const ms = document.getElementById('money-status');
  ms.classList.add(d.money_now.status_color);
  ms.textContent = d.money_now.status_label;

  const accBox = document.getElementById('money-accounts');
  accBox.innerHTML = d.money_now.accounts
    .sort((a,b) => b.value - a.value)
    .map(a => `<div class="row"><span class="lbl">${a.name}</span><span class="val">${fmtR(a.value)}</span></div>`)
    .join('');

  // === БЛОК: Овердрафт ===
  const od = d.overdraft;
  document.getElementById('od-badge').classList.add(od.color);
  document.getElementById('od-badge').textContent = od.percent + '%';
  document.getElementById('od-used').textContent  = fmtR(od.used);
  document.getElementById('od-free').textContent  = fmtR(od.free);
  document.getElementById('od-free').style.color  = od.percent > 85 ? 'var(--red)' : 'var(--green)';
  document.getElementById('od-limit').textContent = fmt(od.limit);
  document.getElementById('od-bar').style.width   = od.percent + '%';
  document.getElementById('od-balance').textContent = fmtR(od.kbb_balance);
  document.getElementById('od-due').textContent   = od.due_date;
  document.getElementById('od-int').textContent   = '~' + fmtR(od.monthly_interest);

  // === БЛОК: Товарка ===
  const uc = d.stock.uncompleted_orders;
  document.getElementById('orders-topay').textContent = '+ ' + fmtR(uc.to_pay);
  document.getElementById('orders-note').textContent =
    uc.orders_qty + ' заказов' + (uc.older_30d ? ' · ' + uc.older_30d + ' старше 30 дн.' : '');
  document.getElementById('stock-cost').textContent = fmtR(d.stock.warehouse_cost);
  document.getElementById('stock-sale').textContent = '~' + fmtR(d.stock.warehouse_sale);
  document.getElementById('suppliers-debt').textContent = fmtR(d.stock.suppliers_debt);

  // === БЛОК: Платёжный календарь ===
  document.getElementById('pc-7').textContent = fmtR(d.payment_calendar.next_7_days);
  document.getElementById('pc-14').textContent = fmtR(d.payment_calendar.next_14_days);
  document.getElementById('pc-note').textContent = d.payment_calendar.note || '';

  // === БЛОК: Pending (свернуто во вкладке Деньги) ===
  document.getElementById('pp-total').innerHTML = fmt(d.pending_payments.total) + '<span class="cur">₽</span>';
  document.getElementById('pp-sub').textContent =
    (d.pending_payments.future.count + d.pending_payments.past_or_undated.count) +
    ' поручений · детализация во вкладке «Долги»';
  document.getElementById('pp-today').textContent = d.meta.date_display.split(',')[0];
  document.getElementById('pp-future').textContent =
    fmtR(d.pending_payments.future.total) + ' · ' + d.pending_payments.future.count + ' платежа';
  document.getElementById('pp-past').textContent =
    fmtR(d.pending_payments.past_or_undated.total) + ' · ' + d.pending_payments.past_or_undated.count + ' платежей';

  // === БЛОК: Кредиты (вкладка Долги) ===
  document.getElementById('loans-total').innerHTML = fmt(d.loans.total) + '<span class="cur">₽</span>';
  document.getElementById('loans-counts').textContent =
    d.loans.active_qty + ' активных + ' + d.loans.frozen_qty + ' заморожен';
  document.getElementById('loans-monthly').textContent = fmtR(d.loans.monthly_payment);
  document.getElementById('loans-int').textContent =
    '~' + fmt(d.loans.interest_part / 1000) + ' К · ' + d.loans.interest_percent + '%';
  document.getElementById('loans-body').textContent =
    '~' + fmt(d.loans.body_part / 1000) + ' К · ' + d.loans.body_percent + '%';

  // Список займов
  const ll = document.getElementById('loans-list');
  ll.innerHTML = d.loans.items.map(L => {
    const cls = L.priority ? 'loan priority' : (L.warning ? 'loan warning' : (L.frozen ? 'loan frozen' : 'loan'));
    const icon = L.priority ? '🔴 ' : (L.warning ? '⚠ ' : '');
    const pill = L.tag ? `<span class="pill">${L.tag}</span>` : '';
    const ost  = `остаток ${fmt(L.balance)} ₽ · ${L.rate}${L.type ? ' · ' + L.type : ''}`;
    return `<div class="${cls}">
      <div class="name">${icon}${L.name} ${pill}</div>
      <div class="pay">${fmtR(L.payment)}</div>
      <div class="ost">${ost}</div>
      <div class="dt">${L.due}</div>
    </div>`;
  }).join('');

  // === БЛОК: Pending детально (вкладка Долги) ===
  document.getElementById('pp-badge').textContent =
    (d.pending_payments.future.count + d.pending_payments.past_or_undated.count) +
    ' платежей · ' + fmtR(d.pending_payments.total);

  document.getElementById('pp-f-count').textContent = d.pending_payments.future.count;
  document.getElementById('pp-f-sum').textContent   = fmtR(d.pending_payments.future.total);
  document.getElementById('pp-p-count').textContent = d.pending_payments.past_or_undated.count;
  document.getElementById('pp-p-sum').textContent   = fmtR(d.pending_payments.past_or_undated.total);

  const renderPP = items => items
    .sort((a,b) => b.amount - a.amount)
    .map(p => `<div class="pending-item">
      <div class="pl">${p.recipient}<small>${p.date} · ${p.purpose}</small></div>
      <div class="pv">${fmtR(p.amount)}</div>
    </div>`).join('');
  document.getElementById('pp-future-list').innerHTML = renderPP(d.pending_payments.future.items);
  document.getElementById('pp-past-list').innerHTML   = renderPP(d.pending_payments.past_or_undated.items);

  // === БЛОК: Продажи ===
  document.getElementById('sales-h2').textContent = 'Сегодня · ' + d.meta.date_display.split(',')[0];
  const k = d.sales.kpi;
  document.getElementById('kpi-gp').textContent = fmtR(k.gross_profit);
  document.getElementById('kpi-margin').textContent = 'маржа ' + k.margin_percent.toFixed(1) + '%';
  document.getElementById('kpi-rev').textContent = fmtR(k.revenue);
  document.getElementById('kpi-items').textContent = k.items_qty + ' позиций';
  document.getElementById('kpi-cash').textContent = fmtR(k.cash);
  document.getElementById('kpi-checks').textContent = k.checks_qty + ' чека';
  document.getElementById('kpi-ref').textContent = '−' + fmtR(Math.abs(k.refunds));
  document.getElementById('kpi-ref-note').textContent = k.refunds_note || '';

  // Очки
  const g = d.sales.glasses;
  document.getElementById('glasses-tot').textContent = g.total_qty + ' шт · ' + fmtR(g.total_sum);
  document.getElementById('glasses-list').innerHTML = `
    <div class="item"><div class="lbl"><div class="ic">Б</div><span>Бардина</span><span class="qty">${g.bardina.qty} шт</span></div><div class="v">${fmtR(g.bardina.sum)}</div></div>
    <div class="item"><div class="lbl"><div class="ic">Д</div><span>Дружбы</span><span class="qty">${g.druzhby.qty} шт</span></div><div class="v">${g.druzhby.sum ? fmtR(g.druzhby.sum) : '—'}</div></div>
    <div class="item" style="border-top:1px solid var(--line);margin-top:4px;padding-top:8px"><div class="lbl" style="color:var(--muted);font-size:12px">в т.ч. линзы</div><div class="v" style="color:var(--muted);font-size:12px">${g.lenses.qty} шт · ${fmt(g.lenses.sum)} ₽</div></div>
    <div class="item"><div class="lbl" style="color:var(--muted);font-size:12px">в т.ч. оправы</div><div class="v" style="color:var(--muted);font-size:12px">${g.frames.qty} шт · ${fmt(g.frames.sum)} ₽</div></div>`;

  // МКЛ
  const m = d.sales.mkl;
  document.getElementById('mkl-tot').textContent = m.total_qty + ' уп · ' + fmtR(m.total_sum);
  document.getElementById('mkl-list').innerHTML = `
    <div class="item"><div class="lbl"><div class="ic">Б</div><span>Бардина</span><span class="qty">${m.bardina.qty} уп</span></div><div class="v">${m.bardina.sum ? fmtR(m.bardina.sum) : '<span style="color:var(--muted)">—</span>'}</div></div>
    <div class="item"><div class="lbl"><div class="ic">Д</div><span>Дружбы</span><span class="qty">${m.druzhby.qty} уп</span></div><div class="v">${m.druzhby.sum ? fmtR(m.druzhby.sum) : '<span style="color:var(--muted)">—</span>'}</div></div>`;

  // Услуги
  const s = d.sales.services;
  document.getElementById('services-tot').textContent = s.total_qty + ' шт · ' + fmtR(s.total_sum);
  document.getElementById('services-list').innerHTML = s.items.map(x => `
    <div class="item"><div class="lbl"><div class="ic">${x.name[0].toUpperCase()}</div><span>${x.name}</span><span class="qty">${x.qty} шт</span></div>
    <div class="v" ${x.sum===0?'style="color:var(--muted)"':''}>${x.sum ? fmtR(x.sum) : '0 ₽'}</div></div>`).join('');

  // Прочее
  const o = d.sales.other;
  document.getElementById('other-tot').textContent = o.total_qty + ' шт · ' + fmtR(o.total_sum);
  document.getElementById('other-list').innerHTML = o.items.map(x => `
    <div class="item"><div class="lbl"><div class="ic">${x.name[0].toUpperCase()}</div><span>${x.name}</span><span class="qty">${x.qty} шт</span></div>
    <div class="v">${fmtR(x.sum)}</div></div>`).join('');
}

// 5. Переключатель табов
document.querySelectorAll('.nav button').forEach(b => {
  b.addEventListener('click', () => {
    document.querySelectorAll('.nav button').forEach(x => x.classList.remove('on'));
    b.classList.add('on');
    document.querySelectorAll('.pane').forEach(p => p.classList.remove('on'));
    document.getElementById('pane-' + b.dataset.tab).classList.add('on');
    window.scrollTo({top:0, behavior:'smooth'});
  });
});

// 6. Запуск
render().catch(e => console.error(e));
