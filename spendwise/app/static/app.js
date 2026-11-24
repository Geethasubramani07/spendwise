"use strict";
// All dynamic text is inserted with textContent (never innerHTML) to avoid XSS.

const $ = (id) => document.getElementById(id);
const rupees = (n) => "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });
const CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Health", "Education", "Other"];

function el(tag, text, cls) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (cls) e.className = cls;
  return e;
}

function showMessage(text, isError = false) {
  const m = $("message");
  m.textContent = text;
  m.className = "show" + (isError ? " error" : "");
}

async function api(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (_) { /* ignore */ }
    throw new Error(detail);
  }
  return res.json();
}

function currentMonth() { return $("month-select").value; }

async function refresh() {
  const month = currentMonth();
  const q = month ? "?month=" + encodeURIComponent(month) : "";
  const summary = await api("/api/summary" + q);
  renderMonths(summary);
  renderSummary(summary);
  const m = "month=" + encodeURIComponent(summary.month);
  const alerts = await api("/api/alerts?" + m);
  renderAlerts(alerts);
  await refreshTransactions(summary.month);
}

function renderMonths(s) {
  const sel = $("month-select");
  sel.replaceChildren();
  const months = s.months.length ? s.months : [s.month];
  months.forEach((m) => { const o = el("option", m); o.value = m; sel.appendChild(o); });
  sel.value = s.month;
}

function renderSummary(s) {
  $("kpi-total").textContent = rupees(s.total_spent);
  $("kpi-count").textContent = s.transactions;
  $("kpi-alerts").textContent = s.fraud_alerts;
  $("kpi-budgets").textContent = s.budget_alerts.length;

  const bars = $("category-bars");
  bars.replaceChildren();
  s.categories.forEach((c) => {
    const row = el("div", undefined, "bar-row");
    const head = el("div", undefined, "bar-head");
    head.appendChild(el("span", c.category));
    head.appendChild(el("span", rupees(c.spent) + " / " + rupees(c.limit)));
    const bar = el("div", undefined, "bar " + c.status);
    const fill = document.createElement("span");
    fill.style.width = Math.min(100, c.percent || 0) + "%";
    bar.appendChild(fill);
    row.append(head, bar);
    bars.appendChild(row);
  });

  const trend = $("trend");
  trend.replaceChildren();
  const max = Math.max(1, ...s.trend.map((t) => t.total));
  s.trend.forEach((t) => {
    const col = el("div", undefined, "col");
    const bar = document.createElement("span");
    bar.style.height = Math.max(4, (t.total / max) * 80) + "px";
    bar.title = rupees(t.total);
    col.append(bar, el("div", t.month.slice(2)));
    trend.appendChild(col);
  });

  const ba = $("budget-alerts");
  ba.replaceChildren();
  if (!s.budget_alerts.length) ba.appendChild(el("li", "All budgets are within limits.", "empty"));
  s.budget_alerts.forEach((t) => ba.appendChild(el("li", t)));
}

function renderAlerts(list) {
  const ul = $("alerts-list");
  ul.replaceChildren();
  if (!list.length) ul.appendChild(el("li", "No suspicious transactions.", "empty"));
  list.forEach((t) => {
    const li = el("li");
    li.appendChild(el("strong", `${t.ts.slice(0, 16)} · ${rupees(t.amount)} · ${t.category}`));
    li.appendChild(el("div", t.description));
    li.appendChild(el("span", "Why flagged: " + t.reason, "why"));
    ul.appendChild(li);
  });
}

async function refreshTransactions(month) {
  const params = new URLSearchParams({ month: month || currentMonth() });
  if ($("filter-category").value) params.set("category", $("filter-category").value);
  if ($("filter-anomalies").checked) params.set("anomalies_only", "true");
  const rows = await api("/api/transactions?" + params.toString());
  const body = document.querySelector("#txn-table tbody");
  body.replaceChildren();
  rows.forEach((t) => {
    const tr = document.createElement("tr");
    if (t.anomaly) tr.className = "flagged";
    tr.appendChild(el("td", t.ts.slice(0, 16)));
    tr.appendChild(el("td", t.description));
    tr.appendChild(el("td", t.category));
    tr.appendChild(el("td", rupees(t.amount), "num"));
    const flag = el("td");
    if (t.anomaly) flag.appendChild(el("span", "Alert", "tag"));
    tr.appendChild(flag);
    body.appendChild(tr);
  });
}

async function guarded(fn) {
  try { await fn(); } catch (e) { showMessage(e.message, true); }
}

$("btn-demo").addEventListener("click", () => guarded(async () => {
  showMessage("Loading demo data...");
  const r = await api("/api/transactions/demo", { method: "POST" });
  showMessage(`Imported ${r.imported} transactions, ${r.alerts} flagged for review.`);
  await refresh();
}));

$("csv-file").addEventListener("change", (ev) => guarded(async () => {
  const file = ev.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  const r = await api("/api/transactions/import", { method: "POST", body: form });
  showMessage(`Imported ${r.imported}, duplicates ${r.duplicates}, skipped ${r.skipped}; ${r.alerts} flagged.`);
  ev.target.value = "";
  await refresh();
}));

$("btn-reset").addEventListener("click", () => guarded(async () => {
  if (!confirm("Delete all transactions?")) return;
  const token = prompt("Admin token (default for local dev: admin123)");
  if (token === null) return;
  await api("/api/transactions", { method: "DELETE", headers: { "X-Admin-Token": token } });
  showMessage("All transactions cleared.");
  await refresh();
}));

$("budget-form").addEventListener("submit", (ev) => {
  ev.preventDefault();
  guarded(async () => {
    const cat = $("budget-category").value;
    const limit = parseFloat($("budget-limit").value);
    await api("/api/budgets/" + encodeURIComponent(cat), {
      method: "PUT", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ monthly_limit: limit }),
    });
    showMessage(`Budget for ${cat} set to ${rupees(limit)}.`);
    await refresh();
  });
});

$("month-select").addEventListener("change", () => guarded(refresh));
$("filter-category").addEventListener("change", () => guarded(() => refreshTransactions()));
$("filter-anomalies").addEventListener("change", () => guarded(() => refreshTransactions()));

CATEGORIES.forEach((c) => {
  const a = el("option", c); a.value = c; $("budget-category").appendChild(a);
  const b = el("option", c); b.value = c; $("filter-category").appendChild(b);
});

guarded(refresh);
