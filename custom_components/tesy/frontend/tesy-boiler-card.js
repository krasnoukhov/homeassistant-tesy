/*
 * Tesy boiler card for Home Assistant.
 *
 * A thermostat card for Tesy water heaters handled by the `tesy` integration:
 * a dial with a drag handle for the manual setpoint, operation modes, Boost and
 * power, plus dialogs for the weekly programs (P1-P3) and for energy and
 * diagnostics. No external dependencies; served by the integration itself.
 *
 *   type: custom:tesy-boiler-card
 *   entity: water_heater.boiler_modeco_2_heater
 */

export const CARD_VERSION = "0.1.17";

export const DAYS = ["mo", "tu", "we", "th", "fr", "sa", "su"];
export const MODES = ["performance", "p1", "p2", "p3", "eco", "ec2", "ec3"];
export const OFF_TEMP = 14; // a program hour at 14 °C = heating off
export const MIN_TEMP = 15;
export const MAX_TEMP = 75;
const SCALE_MIN = 14;
const SCALE_MAX = 75;

// ---------------------------------------------------------------- strings

const STRINGS = {
  uk: {
    days: ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"],
    daysAcc: ["понеділок", "вівторок", "середу", "четвер", "пʼятницю", "суботу", "неділю"],
    modes: { performance: "Ручний", p1: "P1", p2: "P2", p3: "P3", eco: "Eco Smart", ec2: "Eco Comfort", ec3: "Eco Night" },
    heating: "Нагрів", heatingBoost: "Нагрів · Boost", reached: "Температуру досягнуто",
    off: "Вимкнено", heatOff: "Нагрів вимкнено", idle: "Очікування", unavailable: "Недоступний",
    offShort: "Вимк", boost: "Boost", boostOn: "Гріє до 75 °C", boostOffHint: "Вимкнено",
    power: "Живлення", powerOn: "Увімкнено", powerOff: "Вимкнено",
    schedule: "Розклад", stats: "Статистика", clock: "годинник бойлера",
    clockProblem: "Годинник бойлера збитий — розклад спрацює не вчасно", sync: "Виправити",
    setpoint: "Задана температура", close: "Закрити",
    programs: "Тижневі програми", running: "Зараз працює",
    gridHint: "Температура на кожну годину, за годинником бойлера. Натисніть на клітинку, щоб зафарбувати її вибраною температурою.",
    nowFrame: "Рамка — поточна година бойлера", brush: "Пензель", step: "15–75 °C, крок 1",
    colder: "Холодніше на 1 °C", warmer: "Тепліше на 1 °C",
    copy: "Копіювати", copyTo: "Копіювати {day} в:", copyN: "Копіювати в {n} дн.", pickDays: "Оберіть дні",
    weekdays: "Будні", all: "Усі", source: "джерело", notSet: "не задано",
    noChanges: "Змін немає. Сніжинка — нагрів у цю годину вимкнено.", unsaved: "Не записано: {n} дн.",
    save: "Записати в бойлер", saving: "Записую…", saveFailed: "Не вдалося записати: {e}",
    discard: "Є незаписані зміни. Закрити без запису?", noSchedule: "Бойлер не повідомляє розклад",
    energyTitle: "Енергія та діагностика", energyTotal: "Спожито всього", energyReset: "З останнього скидання",
    errors: "Помилки", none: "Немає", wifi: "Wi-Fi", weak: "слабкий", uptime: "Модуль працює",
    firmware: "Прошивка", clockRow: "Годинник", ok: "в порядку", codes: "Коди помилок",
    e01: "обрив нижнього датчика", e02: "КЗ нижнього датчика", e03: "обрив верхнього датчика", e04: "КЗ верхнього датчика",
    h: "год", min: "хв", kwh: "кВт·год", noEntity: "Сутність не знайдено",
    unsupported: "Ця картка поки підтримує лише перевірені моделі (ModEco 2). Для цього бойлера використовуйте стандартну картку термостата.",
    stale: "Картку оновлено — перезавантажте сторінку", reload: "Оновити",
    failed: "Бойлер не прийняв команду",
  },
  en: {
    days: ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
    daysAcc: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    modes: { performance: "Manual", p1: "P1", p2: "P2", p3: "P3", eco: "Eco Smart", ec2: "Eco Comfort", ec3: "Eco Night" },
    heating: "Heating", heatingBoost: "Heating · Boost", reached: "Target reached",
    off: "Off", heatOff: "Heating off", idle: "Idle", unavailable: "Unavailable",
    offShort: "Off", boost: "Boost", boostOn: "Heats to 75 °C", boostOffHint: "Off",
    power: "Power", powerOn: "On", powerOff: "Off",
    schedule: "Schedule", stats: "Statistics", clock: "heater clock",
    clockProblem: "Heater clock is off — programs will switch at the wrong time", sync: "Fix",
    setpoint: "Setpoint", close: "Close",
    programs: "Weekly programs", running: "Running",
    gridHint: "Temperature for every hour, by the heater clock. Tap a cell to paint it with the selected temperature.",
    nowFrame: "Frame — current heater hour", brush: "Brush", step: "15–75 °C, step 1",
    colder: "1 °C colder", warmer: "1 °C warmer",
    copy: "Copy", copyTo: "Copy {day} to:", copyN: "Copy to {n} days", pickDays: "Pick days",
    weekdays: "Weekdays", all: "All", source: "source", notSet: "not set",
    noChanges: "No changes. Snowflake — heating off for that hour.", unsaved: "Not saved: {n} days",
    save: "Write to heater", saving: "Writing…", saveFailed: "Could not write: {e}",
    discard: "There are unsaved changes. Close without writing?", noSchedule: "The heater reports no schedule",
    energyTitle: "Energy and diagnostics", energyTotal: "Consumed in total", energyReset: "Since last reset",
    errors: "Errors", none: "None", wifi: "Wi-Fi", weak: "weak", uptime: "Module uptime",
    firmware: "Firmware", clockRow: "Clock", ok: "OK", codes: "Error codes",
    e01: "lower sensor open", e02: "lower sensor short", e03: "upper sensor open", e04: "upper sensor short",
    h: "h", min: "min", kwh: "kWh", noEntity: "Entity not found",
    unsupported: "This card supports verified models only (ModEco 2 so far). Use the standard thermostat card for this heater.",
    stale: "The card was updated — reload the page", reload: "Reload",
    failed: "The heater did not accept the command",
  },
};

/** Card language: the Home Assistant UI language if translated, else English. */
export function pickLang(language) {
  const code = String(language || "").toLowerCase().split(/[-_]/)[0];
  return Object.prototype.hasOwnProperty.call(STRINGS, code) ? code : "en";
}

const uiLanguage = (hass) => hass?.locale?.language || hass?.language;

/** A locale Intl accepts for the HA UI language: "uk_UA" -> "uk-UA", else "en". */
export function numberLocale(language) {
  const tag = String(language || "").replace(/_/g, "-");
  try {
    return (tag && Intl.NumberFormat.supportedLocalesOf(tag)[0]) || "en";
  } catch (e) {
    return "en"; // not a valid BCP 47 tag
  }
}

function strings(hass) {
  return STRINGS[pickLang(uiLanguage(hass))];
}

const fmt = (s, vars) => s.replace(/\{(\w+)\}/g, (_, k) => vars[k]);

// ---------------------------------------------------------------- pure logic

/** Colour role for a scheduled temperature. */
export function tempRole(t) {
  if (t === null || t === undefined) return "empty";
  if (t <= OFF_TEMP) return "off";
  if (t <= 20) return "t20";
  if (t <= 30) return "t30";
  if (t <= 45) return "t45";
  if (t <= 55) return "t55";
  if (t <= 65) return "t65";
  return "t75";
}

/** Dial angle (degrees, 0 = top, clockwise) for a temperature. */
export function angleFor(t) {
  const f = (t - SCALE_MIN) / (SCALE_MAX - SCALE_MIN);
  return -135 + 270 * Math.min(1, Math.max(0, f));
}

const CX = 140, CY = 140, R = 116;

export function pointAt(deg) {
  const a = (deg * Math.PI) / 180;
  return [CX + R * Math.sin(a), CY - R * Math.cos(a)];
}

export function arcPath(from, to) {
  const [x0, y0] = pointAt(from);
  const [x1, y1] = pointAt(to);
  const large = to - from > 180 ? 1 : 0;
  return `M ${x0.toFixed(1)} ${y0.toFixed(1)} A ${R} ${R} 0 ${large} 1 ${x1.toFixed(1)} ${y1.toFixed(1)}`;
}

/** Setpoint for a point in the 280×280 dial box (clamped to 15-75 °C). */
export function tempFromPoint(x, y) {
  const dx = x - CX, dy = y - CY;
  let deg = (Math.atan2(dx, -dy) * 180) / Math.PI;
  if (deg > 135 || deg < -135) deg = dx < 0 ? -135 : 135;
  const t = Math.round(SCALE_MIN + ((deg + 135) / 270) * (SCALE_MAX - SCALE_MIN));
  return Math.min(MAX_TEMP, Math.max(MIN_TEMP, t));
}

/**
 * Group edited days into tesy.set_schedule calls: days of one program with
 * identical hours go into one call.
 */
export function scheduleCalls(original, edited) {
  const calls = [];
  for (const program of [1, 2, 3]) {
    const before = original[program] || {};
    const after = edited[program] || {};
    const groups = new Map();
    for (const day of DAYS) {
      if (!after[day]) continue;
      if (JSON.stringify(after[day]) === JSON.stringify(before[day])) continue;
      const key = JSON.stringify(after[day]);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(day);
    }
    for (const [key, days] of groups) {
      calls.push({ program, days, temperatures: JSON.parse(key) });
    }
  }
  return calls;
}

/** Entities of the same device, by translation key (entity_id suffix as fallback). */
export function deviceEntities(hass, entityId) {
  const result = {};
  const entry = hass.entities?.[entityId];
  if (!entry?.device_id) return result;
  const wanted = {
    boost: "switch", child_lock: "switch", sync_timezone: "button",
    clock_problem: "binary_sensor", energy_consumed: "sensor",
    energy_consumed_resettable: "sensor", error_status: "sensor",
    wifi_signal: "sensor", uptime: "sensor",
  };
  for (const e of Object.values(hass.entities)) {
    if (e.device_id !== entry.device_id) continue;
    const domain = e.entity_id.split(".")[0];
    for (const [key, d] of Object.entries(wanted)) {
      if (d !== domain || result[key]) continue;
      if (e.translation_key === key || e.entity_id.endsWith("_" + key)) result[key] = e.entity_id;
    }
  }
  result.device = hass.devices?.[entry.device_id];
  return result;
}

/** What the card shows for a water heater state. */
// The integration enables the card per heater model and lists it in the
// tesy_features attribute. Returns null while that cannot be told (the heater
// is unavailable and reports no attributes).
export function cardSupported(stateObj) {
  if (!stateObj) return null;
  const features = stateObj.attributes?.tesy_features;
  if (Array.isArray(features)) return features.includes("card");
  if (stateObj.state === "unavailable" || stateObj.state === "unknown") return null;
  return false;
}

/**
 * Error sensor state -> what the statistics dialog shows: "ok" for 00, the
 * code for a fault, "unknown" when there is no data (no sensor, unavailable).
 */
export function errorView(state) {
  if (state === undefined || state === null || state === "" || state === "unavailable" || state === "unknown") {
    return { kind: "unknown", code: null };
  }
  const code = String(state).trim();
  if (/^0+$/.test(code)) return { kind: "ok", code: "00" };
  return { kind: "error", code: code.padStart(2, "0") };
}

/**
 * The heater's wall clock from device_time ("2026-10-14T09:05:00", no zone):
 * { day: 0 = Monday … 6, hour, minute }, or null. Read as plain fields, not
 * through the browser's time zone, which would shift hours in its DST gap.
 */
export function wallClock(value) {
  const m = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/.exec(String(value || ""));
  if (!m) return null;
  const [y, mo, d, h, mi] = m.slice(1).map(Number);
  const date = new Date(Date.UTC(y, mo - 1, d)); // UTC only as a container
  if (date.getUTCMonth() !== mo - 1 || h > 23 || mi > 59) return null;
  return { day: (date.getUTCDay() + 6) % 7, hour: h, minute: mi };
}

const DURATION_SECONDS = { ms: 0.001, s: 1, min: 60, h: 3600, d: 86400, w: 604800 };

/**
 * A duration sensor state in seconds, whatever display unit the user picked
 * for it in Home Assistant (s, min, h, d…). null when unknown.
 */
export function durationSeconds(state, unit) {
  const n = Number(state);
  const factor = DURATION_SECONDS[unit || "s"];
  if (state === null || state === undefined || state === "" || Number.isNaN(n) || factor === undefined) return null;
  return n * factor;
}

/** Identifies a control across re-renders (the DOM is rebuilt on updates). */
export function focusKey(el) {
  if (!el) return null;
  const d = el.dataset || {};
  return [d.action || "", d.mode || "", el.getAttribute?.("role") || ""].join("|");
}

export function heaterView(stateObj, boostOn) {
  const a = stateObj?.attributes || {};
  const available = !!stateObj && stateObj.state !== "unavailable" && stateObj.state !== "unknown";
  const power = available && stateObj.state !== "off";
  const mode = power ? stateObj.state : "off";
  const target = a.temperature === null || a.temperature === undefined ? null : Number(a.temperature);
  const current = a.current_temperature === null || a.current_temperature === undefined ? null : Number(a.current_temperature);
  const off = target !== null && target <= OFF_TEMP && !boostOn;
  const heating = power && !!a.is_heating;
  let status = "reached";
  if (!available) status = "unavailable";
  else if (!power) status = "off";
  else if (heating) status = boostOn ? "heatingBoost" : "heating";
  else if (off) status = "heatOff";
  else if (target === null) status = "idle";
  return { available, power, mode, target, current, off, heating, status, manual: mode === "performance" };
}

// ---------------------------------------------------------------- version

/** Version the card was loaded with: the ?v= of its module URL. */
export function loadedVersion(moduleUrl) {
  try {
    return new URL(moduleUrl).searchParams.get("v");
  } catch (e) {
    return null;
  }
}

/**
 * What to do about a page loaded with an older card than the server serves:
 * "ok", "reload" (once per server version) or "banner" (reload did not help).
 */
export function staleAction(loaded, server, reloadedFor) {
  if (!loaded || !server || loaded === server) return "ok";
  return reloadedFor === server ? "banner" : "reload";
}

const RELOAD_KEY = "tesy-boiler-card-reloaded-for";
const LOADED_VERSION = loadedVersion(import.meta.url);
const VERSION_RECHECK_MS = 10 * 60 * 1000;
let versionRequest = null; // the request in flight, shared by all cards
let serverVersion = null; // last version the server reported
let serverVersionAt = 0;
let reloading = false;

/**
 * When a card should ask the server for its version: on its first hass, after
 * Home Assistant reconnects (it may have restarted with a new card), and at
 * most every 10 minutes otherwise.
 */
export function versionCheckDue(old, hass, lastCheck, now) {
  if (!hass?.callApi) return false;
  if (!old) return true;
  if (old.connected === false && hass.connected !== false) return true;
  return now - lastCheck >= VERSION_RECHECK_MS;
}

function fetchServerVersion(hass, fresh) {
  if (versionRequest) return versionRequest;
  if (!fresh && serverVersion && Date.now() - serverVersionAt < VERSION_RECHECK_MS) {
    return Promise.resolve(serverVersion);
  }
  versionRequest = hass
    .callApi("GET", "tesy/card_version")
    .then((r) => r?.version ?? null)
    .catch(() => null) // restarting, or an older integration without the endpoint
    .then((version) => {
      versionRequest = null;
      if (version) { serverVersion = version; serverVersionAt = Date.now(); }
      return version || serverVersion;
    });
  return versionRequest;
}

/**
 * Remember that the page was reloaded for this server version. Returns false
 * if that cannot be stored (storage blocked): then reloading could loop, so
 * the caller shows the banner instead.
 */
export function markReloaded(storage, version) {
  try {
    storage.setItem(RELOAD_KEY, version);
    return storage.getItem(RELOAD_KEY) === version;
  } catch (e) {
    return false;
  }
}

function readReloaded(storage) {
  try {
    return storage.getItem(RELOAD_KEY);
  } catch (e) {
    return null;
  }
}

/**
 * Compare the loaded card with the server's. Each card applies its own
 * auto_reload: one that allows it reloads the page (once per server version),
 * the others show the banner.
 */
async function checkVersion(hass, autoReload, fresh) {
  const server = await fetchServerVersion(hass, fresh);
  let storage = null;
  try { storage = window.sessionStorage; } catch (e) { /* storage blocked */ }
  const action = staleAction(LOADED_VERSION, server, storage ? readReloaded(storage) : null);
  if (action === "ok") return "ok";
  if (action === "reload" && autoReload && (reloading || (storage && markReloaded(storage, server)))) {
    reloading = true;
    window.location.reload();
    return "ok";
  }
  return "banner";
}

// ---------------------------------------------------------------- styles

const PALETTE = `
  :host, .tesy {
    --t-surface: color-mix(in srgb, var(--primary-text-color, #e8ecef) 7%, transparent);
    --t-surface-2: color-mix(in srgb, var(--primary-text-color, #e8ecef) 11%, transparent);
    --t-border: color-mix(in srgb, var(--primary-text-color, #e8ecef) 16%, transparent);
    --t-track: color-mix(in srgb, var(--primary-text-color, #e8ecef) 10%, transparent);
    --t-text: var(--primary-text-color, #e8ecef);
    --t-muted: var(--secondary-text-color, #8c97a3);
    --t-faint: color-mix(in srgb, var(--secondary-text-color, #8c97a3) 70%, transparent);
    --t-heat: #e8913a;
  }
  .dark {
    --t-accent: #f2a541; --t-on-accent: #1b1206;
    --t-warm-bg: #3d2a12; --t-warm-fg: #ffc978; --t-warm-border: #6b4a1f;
    --t-ok-bg: #1f3a2e; --t-ok-fg: #8fe3b5; --t-ok-border: #2f5c45;
    --t-off-bg: #1b3247; --t-off-fg: #9fd3f5; --t-off-border: #2a4c69; --t-on-off: #10202e;
    --t-c20-bg: #26323d; --t-c20-fg: #a9baca;
    --t-c30-bg: #2f4e63; --t-c30-fg: #d3e3ee;
    --t-c45-bg: #7a5220; --t-c45-fg: #ffe7c2;
    --t-inv-bg: #e8ecef; --t-inv-fg: #171b20;
  }
  .light {
    --t-accent: #b0610f; --t-on-accent: #ffffff;
    --t-warm-bg: #fcebd2; --t-warm-fg: #8a4b00; --t-warm-border: #e9c48f;
    --t-ok-bg: #ddf3e6; --t-ok-fg: #1e6b43; --t-ok-border: #a7ddbf;
    --t-off-bg: #dceefb; --t-off-fg: #1f5a85; --t-off-border: #a8cdea; --t-on-off: #ffffff;
    --t-c20-bg: #e3e9ef; --t-c20-fg: #3e4c5a;
    --t-c30-bg: #c9dcea; --t-c30-fg: #22394a;
    --t-c45-bg: #f6d9a8; --t-c45-fg: #5a3a10;
    --t-inv-bg: #14181c; --t-inv-fg: #ffffff;
  }
  .t-empty { background: transparent; color: var(--t-faint); border: 1px dashed var(--t-border); }
  .t-off { background: var(--t-off-bg); color: var(--t-off-fg); border: 1px solid var(--t-off-border); }
  .t-t20 { background: var(--t-c20-bg); color: var(--t-c20-fg); border: 1px solid var(--t-c20-bg); }
  .t-t30 { background: var(--t-c30-bg); color: var(--t-c30-fg); border: 1px solid var(--t-c30-bg); }
  .t-t45 { background: var(--t-c45-bg); color: var(--t-c45-fg); border: 1px solid var(--t-c45-bg); }
  .t-t55 { background: #d9822b; color: #1a1206; border: 1px solid #d9822b; }
  .t-t65 { background: #ee9b3b; color: #1a1206; border: 1px solid #ee9b3b; }
  .t-t75 { background: #ffc15e; color: #1a1206; border: 1px solid #ffc15e; }
  button { font: inherit; color: inherit; cursor: pointer; }
  button:disabled { cursor: default; }
  button:focus-visible, a:focus-visible, svg:focus-visible { outline: 2px solid var(--t-accent); outline-offset: 2px; }
  .num { font-variant-numeric: tabular-nums; }
  .sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
`;

const SNOW = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M12 2v20M4 6.5l16 11M4 17.5l16-11"></path><path d="M9.5 3.5L12 6l2.5-2.5M9.5 20.5L12 18l2.5 2.5"></path></svg>`;
const COPY_ICON = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="12" height="12" rx="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
const CLOSE_ICON = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"></path></svg>`;

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function reducedMotion() {
  return typeof window !== "undefined" && window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function formatTemp(t, s) {
  if (t === null || t === undefined || Number.isNaN(t)) return "—";
  if (t <= OFF_TEMP) return s.offShort;
  return `${Math.round(t)} °C`;
}

/** Water temperature: whole degrees as reported (tmpC), tenths only if present. */
export function formatCurrent(t, hass) {
  if (t === null || t === undefined || Number.isNaN(t)) return "—";
  return new Intl.NumberFormat(numberLocale(uiLanguage(hass)), { minimumFractionDigits: 0, maximumFractionDigits: 1 }).format(t);
}

// ---------------------------------------------------------------- the card

// Lets the pure helpers above be imported outside a browser (unit tests).
const Base = typeof HTMLElement !== "undefined" ? HTMLElement : class {};

class TesyBoilerCard extends Base {
  static getStubConfig(hass) {
    const tesy = Object.keys(hass?.entities || {}).filter(
      (id) => id.startsWith("water_heater.") && hass.entities[id].platform === "tesy"
    );
    const entity = tesy.find((id) => cardSupported(hass.states?.[id])) || tesy[0];
    return { entity: entity || "" };
  }

  setConfig(config) {
    if (!config || !config.entity || !config.entity.startsWith("water_heater.")) {
      throw new Error("entity: water_heater.* is required");
    }
    this._config = config;
    this._render();
  }

  set hass(hass) {
    const old = this._hass;
    this._hass = hass;
    if (this._dialog) this._dialog.hass = hass;
    const now = Date.now();
    if (versionCheckDue(old, hass, this._versionAt || 0, now)) {
      // After a reconnect ask the server again, whatever was cached.
      const fresh = !!old && old.connected === false;
      this._versionAt = now;
      checkVersion(hass, this._config?.auto_reload !== false, fresh).then((r) => {
        if (r !== "ok" && !this._stale) { this._stale = true; this._render(); }
      });
    }
    if (this._drag) return; // keep the handle under the finger
    if (!old || this._changed(old, hass)) this._render();
  }

  getCardSize() {
    return 8;
  }

  getGridOptions() {
    return { columns: 6, min_columns: 6, rows: "auto" };
  }

  disconnectedCallback() {
    this._dialog?.close(true);
  }

  _changed(old, hass) {
    const ids = [this._config?.entity, ...Object.values(this._ents || {}).filter((v) => typeof v === "string")];
    if (old.themes?.darkMode !== hass.themes?.darkMode) return true;
    if (uiLanguage(old) !== uiLanguage(hass)) return true;
    return ids.some((id) => old.states[id] !== hass.states[id]);
  }

  /** Call a service; on failure show a short error. Resolves to true on success. */
  _call(domain, service, data) {
    return this._hass.callService(domain, service, data).then(
      () => true,
      (err) => {
        this._error = err?.message || String(err);
        clearTimeout(this._errorTimer);
        this._errorTimer = setTimeout(() => { this._error = ""; this._render(); }, 8000);
        this._render();
        return false;
      }
    );
  }

  _render() {
    if (!this._config || !this._hass) return;
    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
      this.shadowRoot.addEventListener("click", (e) => this._onClick(e));
    }
    const hass = this._hass;
    const s = strings(hass);
    this._ents = deviceEntities(hass, this._config.entity);
    const stateObj = hass.states[this._config.entity];
    const theme = hass.themes?.darkMode === false ? "light" : "dark";

    if (!stateObj) {
      this.shadowRoot.innerHTML = `<style>${PALETTE}</style><ha-card><div style="padding:16px">${esc(s.noEntity)}: ${esc(this._config.entity)}</div></ha-card>`;
      return;
    }
    if (cardSupported(stateObj) === false) {
      const model = this._ents.device?.model;
      this.shadowRoot.innerHTML = `<style>${PALETTE}</style><ha-card><div style="padding:16px">${esc(s.unsupported)}${model ? ` (${esc(model)})` : ""}</div></ha-card>`;
      return;
    }

    const boostOn = hass.states[this._ents.boost]?.state === "on";
    const v = heaterView(stateObj, boostOn);
    // Right after a setpoint change, show the expected heating state until the
    // heater reports back (the integration polls it ~2 s after a command).
    const opt = this._optimistic;
    if (opt && Date.now() < opt.until && !(Date.parse(stateObj.last_updated) > opt.since + 1500)) {
      if (v.power && v.manual && !boostOn && v.current !== null) {
        v.heating = v.current < opt.target - 0.5;
        v.status = v.heating ? "heating" : "reached";
      }
    } else if (opt) {
      this._optimistic = null;
    }
    this._view = v;
    const rssi = hass.states[this._ents.wifi_signal]?.state;
    const device = this._ents.device;
    const name = this._config.name || device?.name_by_user || device?.name || stateObj.attributes.friendly_name;
    const subtitle = this._config.subtitle ?? [device?.manufacturer, device?.model].filter(Boolean).join(" ");

    const manualSet = stateObj.attributes.manual_temperature ?? v.target;
    if (this._pendingTarget !== undefined && Number(manualSet) === this._pendingTarget) {
      this._pendingTarget = undefined;
      clearTimeout(this._pendingTimer);
    }
    const setpoint = this._pendingTarget ?? (v.manual && manualSet !== null ? Number(manualSet) : null);
    const hasHandle = v.power && v.manual && setpoint !== null;
    const curAngle = v.current === null ? -135 : Math.max(-134, angleFor(v.current));
    const anim = this._config.animation;
    const animate = v.heating && anim !== false && anim !== "off"
      && (anim === true || anim === "always" || !reducedMotion());
    const [hx, hy] = hasHandle ? pointAt(angleFor(setpoint)) : [0, 0];
    const [bx, by] = pointAt(angleFor(75));

    const status = {
      reached: ["ok", s.reached], heating: ["warm", s.heating], heatingBoost: ["warm", s.heatingBoost],
      off: ["neutral", s.off], heatOff: ["snow", s.heatOff], idle: ["neutral", s.idle], unavailable: ["neutral", s.unavailable],
    }[v.status];

    const clock = hass.states[this._ents.clock_problem];
    const clockBad = clock?.state === "on";
    const devTime = wallClock(clock?.attributes?.device_time);
    const clockText = devTime
      ? `${s.days[devTime.day]} ${String(devTime.hour).padStart(2, "0")}:${String(devTime.minute).padStart(2, "0")} · ${s.clock}`
      : "";

    const targetText = v.power
      ? (boostOn ? "75 °C" : formatTemp(v.manual ? setpoint : v.target, s))
      : "—";

    // The DOM is rebuilt below: keep keyboard focus on the same control.
    const focused = focusKey(this.shadowRoot.activeElement);
    this.shadowRoot.innerHTML = `
      <style>${PALETTE}${CARD_CSS}</style>
      <ha-card class="tesy ${theme}">
        <div class="wrap">
          <div class="head">
            <div class="badge" aria-hidden="true"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="2.5" width="12" height="19" rx="5"></rect><path d="M12 8.5v5"></path><circle cx="12" cy="16" r="1.6"></circle></svg></div>
            <div class="title"><div class="name">${esc(name)}</div>${subtitle ? `<div class="sub">${esc(subtitle)}</div>` : ""}</div>
            ${rssi !== undefined && rssi !== "unavailable" ? `<div class="rssi"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M2 8.5a15 15 0 0 1 20 0"></path><path d="M5.5 12a10 10 0 0 1 13 0"></path><path d="M9 15.5a5 5 0 0 1 6 0"></path><circle cx="12" cy="19" r="1"></circle></svg><span class="num">${esc(rssi)} dBm</span></div>` : ""}
          </div>

          <div class="dialwrap">
          <button type="button" class="power ${v.power ? "on" : ""}" aria-pressed="${v.power}" data-action="power"
                  aria-label="${esc(s.power)}: ${esc(v.power ? s.powerOn : s.powerOff)}" title="${esc(s.power)}: ${esc(v.power ? s.powerOn : s.powerOff)}" ${v.available ? "" : "disabled"}><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 2v10"></path><path d="M18.4 6.6a9 9 0 1 1-12.8 0"></path></svg></button>
          <div class="dial">
            <svg viewBox="0 0 280 280" role="slider" tabindex="${hasHandle ? 0 : -1}" aria-label="${esc(s.setpoint)}"
                 aria-valuemin="${MIN_TEMP}" aria-valuemax="${MAX_TEMP}" aria-valuenow="${hasHandle ? setpoint : ""}"
                 aria-disabled="${hasHandle ? "false" : "true"}" class="${hasHandle ? "drag" : ""}">
              <path d="${arcPath(-135, 135)}" fill="none" stroke-width="22" stroke-linecap="round" style="stroke: var(--t-track)"></path>
              ${v.current !== null ? `<path d="${arcPath(-135, curAngle)}" fill="none" stroke-width="22" stroke-linecap="round" style="stroke: var(--t-heat)"></path>` : ""}
              ${animate && v.current !== null ? `<path d="${arcPath(-135, curAngle)}" pathLength="100" fill="none" stroke-width="12" stroke-linecap="round" stroke-dasharray="18 120" stroke-dashoffset="18" style="stroke: rgb(255,238,205); opacity: .8"><animate attributeName="stroke-dashoffset" from="18" to="-100" dur="${boostOn ? "1.8s" : "3s"}" repeatCount="indefinite"></animate></path>` : ""}
              ${v.power && boostOn ? `<circle cx="${bx.toFixed(1)}" cy="${by.toFixed(1)}" r="5" style="fill: var(--t-warm-fg)"></circle>` : ""}
              ${hasHandle ? `<circle class="handle" cx="${hx.toFixed(1)}" cy="${hy.toFixed(1)}" r="15" stroke-width="8" style="fill: var(--ha-card-background, var(--card-background-color, #ffffff)); stroke: var(--t-inv-bg)"></circle>` : ""}
            </svg>
            <div class="center">
              <div class="cur num">${formatCurrent(v.current, hass)}<span>°C</span></div>
              <div class="tgt num">${esc(targetText)}</div>
              <div class="pill ${status[0]}">${v.heating ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22c4 0 7-2.8 7-6.8 0-3.5-2.3-5.6-4-7.7-.6 2-1.6 3-3 3.5.4-3.4-1-6.5-4-9 0 4-4 6.5-4 12.2C4 19.2 7.6 22 12 22z">${animate ? `<animate attributeName="opacity" values="1;0.5;0.85;1" dur="1.6s" repeatCount="indefinite"></animate>` : ""}</path></svg>` : ""}<span>${esc(status[1])}</span></div>
            </div>
          </div>
          </div>

          <div class="modes" role="group">
            ${MODES.filter((m) => (stateObj.attributes.operation_list || MODES).includes(m)).map((m) => `
              <button type="button" class="chip ${v.mode === m ? "on" : ""}" aria-pressed="${v.mode === m}" data-action="mode" data-mode="${m}" ${v.available ? "" : "disabled"}>${esc(s.modes[m])}</button>`).join("")}
          </div>

          <div class="actions">
            ${this._ents.boost ? `<button type="button" class="act ${boostOn ? "warm" : ""}" aria-pressed="${boostOn}" data-action="boost"
                aria-label="${esc(s.boost)}: ${esc(boostOn ? s.boostOn : s.boostOffHint)}" title="${esc(s.boost)}: ${esc(boostOn ? s.boostOn : s.boostOffHint)}" ${v.available ? "" : "disabled"}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2.1-.1-2.9a2.2 2.2 0 0 0-2.9-.1z"></path><path d="M12 15l-3-3a22 22 0 0 1 2-3.9A12.9 12.9 0 0 1 22 2c0 2.7-.8 7.5-6 11a22.4 22.4 0 0 1-4 2z"></path></svg></button>` : ""}
            <button type="button" class="act" data-action="schedule" aria-label="${esc(s.schedule)}" title="${esc(s.schedule)}">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"></rect><path d="M16 2v4M8 2v4M3 10h18"></path></svg></button>
            <button type="button" class="act" data-action="stats" aria-label="${esc(s.stats)}" title="${esc(s.stats)}">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3v18h18"></path><path d="M7 15l4-4 3 3 5-6"></path></svg></button>
          </div>

          ${this._error ? `<div class="warn" role="alert"><span>${esc(s.failed)}: ${esc(this._error)}</span></div>` : ""}
          ${this._stale ? `<div class="warn" role="status"><span>${esc(s.stale)}</span><button type="button" data-action="reload">${esc(s.reload)}</button></div>` : ""}
          ${clockBad ? `<div class="warn" role="status"><span>${esc(s.clockProblem)}</span>${this._ents.sync_timezone ? `<button type="button" data-action="sync">${esc(s.sync)}</button>` : ""}</div>` : ""}
          ${clockText ? `<div class="clock num">${esc(clockText)}</div>` : ""}
        </div>
      </ha-card>`;

    const svg = this.shadowRoot.querySelector(".dial svg");
    if (hasHandle) this._bindDial(svg, setpoint);
    if (focused) {
      const again = [...this.shadowRoot.querySelectorAll("[data-action], [role='slider']")].find(
        (el) => focusKey(el) === focused && !el.disabled
      );
      again?.focus({ preventScroll: true });
    }
  }

  _bindDial(svg, setpoint) {
    const toTemp = (e) => {
      const r = svg.getBoundingClientRect();
      return tempFromPoint(((e.clientX - r.left) * 280) / r.width, ((e.clientY - r.top) * 280) / r.height);
    };
    const show = (t) => {
      const [x, y] = pointAt(angleFor(t));
      const handle = svg.querySelector(".handle");
      handle.setAttribute("cx", x.toFixed(1));
      handle.setAttribute("cy", y.toFixed(1));
      handle.setAttribute("r", this._drag ? "18" : "15");
      svg.setAttribute("aria-valuenow", t);
      const tgt = this.shadowRoot.querySelector(".tgt");
      if (tgt && !(this._hass.states[this._ents.boost]?.state === "on")) tgt.textContent = `${t} °C`;
      this._dragTemp = t;
    };
    svg.addEventListener("pointerdown", (e) => {
      svg.setPointerCapture(e.pointerId);
      this._drag = true;
      show(toTemp(e));
    });
    svg.addEventListener("pointermove", (e) => { if (this._drag) show(toTemp(e)); });
    const end = () => {
      if (!this._drag) return;
      this._drag = false;
      this._commit(this._dragTemp);
    };
    svg.addEventListener("pointerup", end);
    svg.addEventListener("pointercancel", end);
    svg.addEventListener("keydown", (e) => {
      const step = { ArrowUp: 1, ArrowRight: 1, ArrowDown: -1, ArrowLeft: -1 }[e.key];
      if (!step) return;
      e.preventDefault();
      const t = Math.min(MAX_TEMP, Math.max(MIN_TEMP, (this._pendingTarget ?? setpoint) + step));
      show(t);
      clearTimeout(this._keyTimer);
      this._pendingTarget = t;
      this._keyTimer = setTimeout(() => this._commit(t), 600);
    });
  }

  async _commit(t) {
    if (t === undefined || t === null) return;
    const seq = (this._commitSeq = (this._commitSeq || 0) + 1);
    this._pendingTarget = t;
    const now = Date.now();
    this._optimistic = { target: t, since: now, until: now + 15000 };
    clearTimeout(this._optimisticTimer);
    this._optimisticTimer = setTimeout(() => this._render(), 15100);
    clearTimeout(this._pendingTimer);
    this._pendingTimer = setTimeout(() => { this._pendingTarget = undefined; this._render(); }, 8000);
    const ok = await this._call("water_heater", "set_temperature", { entity_id: this._config.entity, temperature: t });
    if (!ok && seq === this._commitSeq) {
      // Do not keep showing a setpoint and heating state the heater never got
      // (unless a newer setpoint was sent since: that one is still on its way).
      this._optimistic = null;
      this._pendingTarget = undefined;
      clearTimeout(this._optimisticTimer);
      clearTimeout(this._pendingTimer);
    }
    this._render();
  }

  _onClick(e) {
    const btn = e.target.closest("[data-action]");
    if (!btn || btn.disabled) return;
    const id = this._config.entity;
    switch (btn.dataset.action) {
      case "mode":
        this._call("water_heater", "set_operation_mode", { entity_id: id, operation_mode: btn.dataset.mode });
        break;
      case "boost":
        this._call("switch", "toggle", { entity_id: this._ents.boost });
        break;
      case "power":
        this._call("water_heater", this._view.power ? "turn_off" : "turn_on", { entity_id: id });
        break;
      case "sync":
        this._call("button", "press", { entity_id: this._ents.sync_timezone });
        break;
      case "reload":
        window.location.reload();
        break;
      case "schedule":
      case "stats":
        this._openDialog(btn.dataset.action, btn);
        break;
    }
  }

  _openDialog(kind, opener) {
    this._dialog?.close(true);
    const dialog = document.createElement("tesy-boiler-dialog");
    dialog.setup(kind, this._config, this._ents, () => {
      if (this._dialog === dialog) this._dialog = null;
      // Back to the button that opened it (re-rendered: find it by action).
      const again = this.shadowRoot?.querySelector(`[data-action="${kind}"]`) || opener;
      if (again?.isConnected) again.focus();
    });
    dialog.hass = this._hass;
    document.body.appendChild(dialog);
    this._dialog = dialog;
  }
}

const CARD_CSS = `
  ha-card { overflow: hidden; }
  .wrap { box-sizing: border-box; padding: 20px; display: flex; flex-direction: column; gap: 20px; color: var(--t-text); }
  .head { display: flex; align-items: center; gap: 12px; }
  .badge { width: 40px; height: 40px; border-radius: 12px; background: var(--t-surface-2); color: var(--t-accent); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .title { flex: 1; min-width: 0; }
  .name { font-size: 17px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .sub { font-size: 13px; color: var(--t-muted); }
  .rssi { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--t-muted); }
  .dial { position: relative; width: min(100%, 350px); aspect-ratio: 1; align-self: center; }
  .dial > svg { position: absolute; inset: 0; width: 100%; height: 100%; touch-action: none; }
  .dial > svg.drag { cursor: pointer; }
  .center { position: absolute; left: 0; right: 0; top: 28%; display: flex; flex-direction: column; align-items: center; gap: 6px; pointer-events: none; }
  .cur { font-size: clamp(40px, 13vw, 64px); font-weight: 600; line-height: 1; }
  .cur span { font-size: 0.44em; color: var(--t-muted); }
  .tgt { font-size: clamp(20px, 6vw, 30px); font-weight: 600; color: var(--t-muted); }
  .pill { display: inline-flex; align-items: center; gap: 6px; margin-top: 4px; padding: 6px 12px; border-radius: 999px; font-size: 14px; font-weight: 500; }
  .pill svg { width: 14px; height: 14px; flex-shrink: 0; }
  .pill.ok { background: var(--t-ok-bg); color: var(--t-ok-fg); }
  .pill.warm { background: var(--t-warm-bg); color: var(--t-warm-fg); }
  .pill.snow { background: var(--t-off-bg); color: var(--t-off-fg); }
  .pill.neutral { background: var(--t-surface-2); color: var(--t-muted); }
  .modes { display: flex; flex-wrap: wrap; gap: 10px; }
  .chip { min-height: 44px; padding: 0 16px; border-radius: 12px; font-size: 14px; font-weight: 500; background: var(--t-surface); border: 1px solid var(--t-border); color: var(--t-text); }
  .chip.on { background: var(--t-accent); border-color: var(--t-accent); color: var(--t-on-accent); }
  .dialwrap { position: relative; display: flex; justify-content: center; }
  .power { position: absolute; top: 0; right: 0; z-index: 1; width: 52px; height: 52px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
           background: var(--t-surface); border: 1px solid var(--t-border); color: var(--t-muted); }
  .power.on { background: var(--t-ok-bg); border-color: var(--t-ok-border); color: var(--t-ok-fg); }
  .actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(0, 1fr)); grid-auto-flow: column; gap: 10px; }
  .act { min-height: 56px; border-radius: 16px; display: flex; align-items: center; justify-content: center; background: var(--t-surface); border: 1px solid var(--t-border); }
  .act.warm { background: var(--t-warm-bg); border-color: var(--t-warm-border); color: var(--t-warm-fg); }
  .warn { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 12px; background: var(--t-warm-bg); color: var(--t-warm-fg); font-size: 13px; }
  .warn span { flex: 1; }
  .warn button { min-height: 36px; padding: 0 12px; border-radius: 10px; border: 1px solid var(--t-warm-border); background: transparent; font-weight: 600; }
  .clock { font-size: 12px; color: var(--t-muted); text-align: center; margin-top: -8px; }
  button:disabled { opacity: .5; }
`;

// ---------------------------------------------------------------- dialogs

class TesyBoilerDialog extends Base {
  setup(kind, config, ents, onClose) {
    this._kind = kind;
    this._config = config;
    this._ents = ents;
    this._onClose = onClose;
    this._st = { prog: null, day: null, brush: 50, lastTemp: 50, copySrc: "mo", copyDst: [], saving: false, error: "" };
    this.attachShadow({ mode: "open" });
    this.shadowRoot.addEventListener("click", (e) => this._onClick(e));
    this.shadowRoot.addEventListener("input", (e) => this._onInput(e));
    this.shadowRoot.addEventListener("change", (e) => this._onInput(e));
    this._onKey = (e) => {
      if (e.key === "Escape") this.close();
      else if (e.key === "Tab") this._trapFocus(e);
    };
    this._onResize = () => this._render();
    window.addEventListener("keydown", this._onKey);
    window.addEventListener("resize", this._onResize);
  }

  set hass(hass) {
    const old = this._hass;
    this._hass = hass;
    if (this._kind === "schedule") {
      if (!this._edit) this._loadSchedule();
      else if (!this._dirtyDays().length && !this._st.saving) this._syncSchedule();
    }
    const ids = [this._config.entity, ...Object.values(this._ents).filter((v) => typeof v === "string")];
    if (!old || old.themes?.darkMode !== hass.themes?.darkMode || uiLanguage(old) !== uiLanguage(hass)
        || ids.some((id) => old.states[id] !== hass.states[id])) {
      this._render();
    }
  }

  /** Keep Tab / Shift+Tab inside the dialog while it is open. */
  _trapFocus(e) {
    const items = [...this.shadowRoot.querySelectorAll(
      ".panel button:not([disabled]), .panel input:not([disabled]), .panel select:not([disabled]), .panel [tabindex]:not([tabindex='-1'])"
    )];
    if (!items.length) return;
    const first = items[0], last = items[items.length - 1];
    const active = this.shadowRoot.activeElement;
    if (!active || !items.includes(active)) { e.preventDefault(); first.focus(); }
    else if (e.shiftKey && active === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && active === last) { e.preventDefault(); first.focus(); }
  }

  connectedCallback() {
    this._render();
  }

  close(force) {
    // While writing, the dialog stays open: it closes itself when done.
    if (!force && this._st?.saving) return;
    if (!force && this._kind === "schedule" && this._dirtyDays().length && !window.confirm(strings(this._hass).discard)) return;
    window.removeEventListener("keydown", this._onKey);
    window.removeEventListener("resize", this._onResize);
    this.remove();
    this._onClose?.();
  }

  _loadSchedule() {
    const a = this._hass.states[this._config.entity]?.attributes || {};
    const original = {};
    for (const p of [1, 2, 3]) if (a[`schedule_p${p}`]) original[p] = a[`schedule_p${p}`];
    if (!Object.keys(original).length) return;
    this._original = original;
    this._edit = JSON.parse(JSON.stringify(original));
    const active = a.active_program;
    // The running program may be one that could not be read: then the first one.
    this._st.prog = original[active] ? Number(active) : Number(Object.keys(original)[0]);
    const dev = this._deviceNow();
    this._st.day = dev ? DAYS[dev.day] : "mo";
    this._st.copySrc = this._st.day;
  }

  /** Pick up programs changed elsewhere (panel, MyTESY) while nothing is edited. */
  _syncSchedule() {
    const a = this._hass.states[this._config.entity]?.attributes || {};
    const fresh = {};
    for (const p of [1, 2, 3]) if (a[`schedule_p${p}`]) fresh[p] = a[`schedule_p${p}`];
    if (!Object.keys(fresh).length || JSON.stringify(fresh) === JSON.stringify(this._original)) return;
    this._original = fresh;
    this._edit = JSON.parse(JSON.stringify(fresh));
    if (!this._edit[this._st.prog]) this._st.prog = Number(Object.keys(fresh)[0]);
  }

  _deviceNow() {
    return wallClock(this._hass.states[this._ents.clock_problem]?.attributes?.device_time);
  }

  _dirtyDays() {
    if (!this._edit) return [];
    const out = [];
    for (const p of [1, 2, 3]) for (const d of DAYS) {
      if (this._edit[p] && JSON.stringify(this._edit[p][d]) !== JSON.stringify(this._original[p][d])) out.push(p + d);
    }
    return out;
  }

  _portrait() {
    return window.innerWidth < 720;
  }

  _render() {
    if (!this._hass) return;
    const s = strings(this._hass);
    const theme = this._hass.themes?.darkMode === false ? "light" : "dark";
    let body = "", title = "", wide = false;
    if (this._kind === "stats") { title = s.energyTitle; body = this._statsHtml(s); }
    else { title = s.programs; wide = !this._portrait(); body = this._edit ? (wide ? this._gridHtml(s) : this._phoneHtml(s)) : `<p>${esc(s.noSchedule)}</p>`; }

    const keepScroll = this.shadowRoot.querySelector(".panel")?.scrollTop || 0;
    const active = this.shadowRoot.activeElement;
    const focusKey = active
      ? ["action", "day", "hour", "prog", "mode", "input", "set", "step"].map((k) => active.dataset?.[k] ?? "").join("|")
      : null;
    this.shadowRoot.innerHTML = `
      <style>${PALETTE}${DIALOG_CSS}</style>
      <div class="tesy ${theme} backdrop" data-action="backdrop">
        <div class="panel ${wide ? "wide" : ""} ${this._kind} ${this._st.saving ? "busy" : ""}" role="dialog" aria-modal="true" aria-label="${esc(title)}" ${this._st.saving ? 'aria-busy="true"' : ""}>
          <div class="dhead">
            <h2>${esc(title)}</h2>
            ${this._kind === "schedule" && this._edit ? `<span class="pill warm">${esc(s.running)} P${esc(this._hass.states[this._config.entity]?.attributes?.active_program || "—")}</span>` : ""}
            <button type="button" class="x" data-action="close" aria-label="${esc(s.close)}" ${this._st.saving ? "disabled" : ""}>${CLOSE_ICON}</button>
          </div>
          ${body}
        </div>
      </div>`;
    const panel = this.shadowRoot.querySelector(".panel");
    if (panel) panel.scrollTop = keepScroll;
    if (focusKey) {
      const again = [...this.shadowRoot.querySelectorAll("[data-action],[data-input]")].find(
        (el) => ["action", "day", "hour", "prog", "mode", "input", "set", "step"].map((k) => el.dataset[k] ?? "").join("|") === focusKey
      );
      again?.focus();
    } else if (!this._focused && this.isConnected) {
      // Move focus into the dialog once it is on the page.
      this._focused = true;
      this.shadowRoot.querySelector(".x")?.focus();
    }
  }

  // ---- statistics

  _statsHtml(s) {
    const st = (id) => this._hass.states[id];
    const val = (id, digits = 1) => {
      const o = st(id);
      if (!o || o.state === "unavailable" || o.state === "unknown") return "—";
      const n = Number(o.state);
      return Number.isNaN(n) ? o.state : new Intl.NumberFormat(numberLocale(uiLanguage(this._hass)), { maximumFractionDigits: digits }).format(n);
    };
    const err = errorView(st(this._ents.error_status)?.state);
    const errPill = {
      ok: ["ok", `${esc(s.none)} · 00`],
      error: ["warm", `E${esc(err.code)}`],
      unknown: ["neutral", "—"],
    }[err.kind];
    const rssi = Number(st(this._ents.wifi_signal)?.state);
    const upState = st(this._ents.uptime);
    const up = durationSeconds(upState?.state, upState?.attributes?.unit_of_measurement);
    const upText = up === null ? "—" : `${Math.floor(up / 3600)} ${s.h} ${Math.floor((up % 3600) / 60)} ${s.min}`;
    // Energy in the unit the user chose for the sensor (kWh, Wh, MWh…).
    const energyUnit = (id) => {
      const unit = st(id)?.attributes?.unit_of_measurement;
      return !unit || unit === "kWh" ? s.kwh : unit;
    };
    const dev = this._ents.device;
    const clockBad = st(this._ents.clock_problem)?.state === "on";
    return `
      <div class="kpis">
        <div class="kpi"><div class="k">${esc(s.energyTotal)}</div><div class="v num">${val(this._ents.energy_consumed)}<span> ${esc(energyUnit(this._ents.energy_consumed))}</span></div></div>
        <div class="kpi"><div class="k">${esc(s.energyReset)}</div><div class="v num">${val(this._ents.energy_consumed_resettable)}<span> ${esc(energyUnit(this._ents.energy_consumed_resettable))}</span></div></div>
      </div>
      <div class="rows">
        <div class="row"><span>${esc(s.errors)}</span><span class="pill ${errPill[0]}">${errPill[1]}</span></div>
        <div class="row"><span>${esc(s.wifi)}</span><span class="num ${rssi < -67 ? "warmtxt" : ""}">${Number.isNaN(rssi) ? "—" : rssi + " dBm" + (rssi < -67 ? " · " + esc(s.weak) : "")}</span></div>
        <div class="row"><span>${esc(s.uptime)}</span><span class="num">${esc(upText)}</span></div>
        ${this._ents.clock_problem ? `<div class="row"><span>${esc(s.clockRow)}</span><span class="${clockBad ? "warmtxt" : ""}">${esc(clockBad ? s.clockProblem : s.ok)}</span></div>` : ""}
        <div class="row"><span>${esc(s.firmware)}</span><span class="num">${esc([dev?.sw_version && "Wi-Fi " + dev.sw_version, dev?.hw_version].filter(Boolean).join(" · ") || "—")}</span></div>
      </div>
      <div class="k caps">${esc(s.codes)}</div>
      <div class="codes">${["01", "02", "03", "04"].map((c) => `<div><b class="num">E${c}</b> ${esc(s["e" + c])}</div>`).join("")}</div>`;
  }

  // ---- schedule helpers

  _cellHtml(t, h, day, s, extraClass = "") {
    const role = tempRole(t);
    const off = role === "off";
    const label = `${s.days[DAYS.indexOf(day)]} ${String(h).padStart(2, "0")}:00, ${t === null ? s.notSet : off ? s.heatOff : t + " °C"}`;
    return { role, off, label, extraClass };
  }

  _isNow(day, h) {
    const a = this._hass.states[this._config.entity]?.attributes || {};
    const now = this._deviceNow();
    return now && a.active_program === this._st.prog && DAYS[now.day] === day && now.hour === h;
  }

  _brushHtml(s, compact) {
    const st = this._st;
    const isOff = st.brush === OFF_TEMP;
    const level = isOff ? st.lastTemp : st.brush;
    return `
      <div class="brush">
        ${compact ? "" : `<span class="k caps">${esc(s.brush)}</span>`}
        <div class="swatch t-${tempRole(st.brush)} num" aria-hidden="true">${isOff ? esc(s.offShort) : level + "°"}</div>
        ${compact ? "" : `<button type="button" class="sq" data-action="brush-step" data-step="-1" aria-label="${esc(s.colder)}">−</button>`}
        <label class="sr" for="brush">${esc(s.brush)}</label>
        <input id="brush" type="range" min="${MIN_TEMP}" max="${MAX_TEMP}" step="1" value="${level}" data-input="brush" aria-valuetext="${isOff ? esc(s.heatOff) : level + " °C"}">
        ${compact ? "" : `<button type="button" class="sq" data-action="brush-step" data-step="1" aria-label="${esc(s.warmer)}">+</button>`}
        <button type="button" class="offbtn ${isOff ? "on" : ""}" aria-pressed="${isOff}" data-action="brush-off">${SNOW}<span>${esc(s.offShort)}</span></button>
        ${compact ? "" : `<span class="k">${esc(s.step)}</span>`}
      </div>`;
  }

  _tabsHtml() {
    const avail = [1, 2, 3].filter((p) => this._edit[p]);
    return `<div class="tabs" role="group">${avail.map((p) => `<button type="button" class="${this._st.prog === p ? "on" : ""}" aria-pressed="${this._st.prog === p}" data-action="prog" data-prog="${p}">P${p}</button>`).join("")}</div>`;
  }

  _footerHtml(s) {
    const dirty = this._dirtyDays();
    const note = this._st.error ? fmt(s.saveFailed, { e: this._st.error }) : dirty.length ? fmt(s.unsaved, { n: dirty.length }) : s.noChanges;
    const cls = this._st.error ? "errtxt" : dirty.length ? "warmtxt" : "";
    return `
      <div class="foot">
        <div class="note ${cls}" role="status">${esc(note)}</div>
        <button type="button" class="primary" data-action="save" ${this._st.saving ? "disabled" : ""}>${esc(this._st.saving ? s.saving : s.save)}</button>
      </div>`;
  }

  _gridHtml(s) {
    const st = this._st;
    const prog = this._edit[st.prog];
    const hours = Array.from({ length: 24 }, (_, h) => `<div class="hh num">${h}</div>`).join("");
    const rows = DAYS.map((d, i) => `
      <div class="grow">
        <div class="dl">${esc(s.days[i])}</div>
        ${prog[d].map((t, h) => {
          const c = this._cellHtml(t, h, d, s);
          return `<button type="button" class="cell t-${c.role} ${this._isNow(d, h) ? "now" : ""}" data-action="paint" data-day="${d}" data-hour="${h}" aria-label="${esc(c.label)}">${c.off ? SNOW : `<span class="num">${t === null ? "·" : t}</span>`}</button>`;
        }).join("")}
        <button type="button" class="cp ${st.copySrc === d ? "on" : ""}" aria-pressed="${st.copySrc === d}" data-action="copy-src" data-day="${d}" aria-label="${esc(s.copy)} ${esc(s.days[i])}">${COPY_ICON}</button>
      </div>`).join("");
    return `
      <div class="ghead"><p class="k">${esc(s.gridHint)}</p>${this._tabsHtml()}</div>
      <div class="grid"><div class="grow"><div class="dl"></div>${hours}</div>${rows}</div>
      ${this._brushHtml(s, false)}
      ${this._copyHtml(s, st.copySrc, true)}
      ${this._footerHtml(s)}`;
  }

  _copyHtml(s, src, wide) {
    const st = this._st;
    const idx = DAYS.indexOf(src);
    const btns = DAYS.map((d, i) => {
      const isSrc = d === src, on = st.copyDst.includes(d);
      return `<button type="button" class="dd ${on ? "on" : ""}" ${isSrc ? "disabled" : ""} aria-pressed="${on}" data-action="copy-dst" data-day="${d}" aria-label="${esc(isSrc ? s.days[i] + ": " + s.source : s.copy + " → " + s.days[i])}">${esc(s.days[i])}</button>`;
    }).join("");
    const go = `<button type="button" class="go ${st.copyDst.length ? "on" : ""}" data-action="copy-do" ${st.copyDst.length ? "" : "disabled"}>${wide ? esc(st.copyDst.length ? fmt(s.copyN, { n: st.copyDst.length }) : s.pickDays) : "OK"}</button>`;
    if (!wide) {
      return `<div class="copy"><div class="k">${esc(fmt(s.copyTo, { day: s.daysAcc[idx] }))}</div><div class="ddrow">${btns}${go}</div></div>`;
    }
    return `
      <div class="copy wide">
        <span class="k caps">${esc(s.copy)}</span>
        <label class="sr" for="copy-src">${esc(s.source)}</label>
        <select id="copy-src" data-input="copy-src">${DAYS.map((d, i) => `<option value="${d}" ${d === src ? "selected" : ""}>${esc(s.days[i])}</option>`).join("")}</select>
        <span aria-hidden="true">→</span>
        ${btns}
        <button type="button" class="txt" data-action="copy-pick" data-set="weekdays">${esc(s.weekdays)}</button>
        <button type="button" class="txt" data-action="copy-pick" data-set="all">${esc(s.all)}</button>
        ${go}
      </div>`;
  }

  _phoneHtml(s) {
    const st = this._st;
    const prog = this._edit[st.prog];
    const week = DAYS.map((d, i) => `
      <button type="button" class="wk ${st.day === d ? "on" : ""}" aria-pressed="${st.day === d}" data-action="day" data-day="${d}" aria-label="${esc(s.days[i])}">
        <span class="wl">${esc(s.days[i])}</span>${prog[d].map((t) => `<span class="ws t-${tempRole(t)}"></span>`).join("")}
      </button>`).join("");
    const dirty = this._dirtyDays();
    const days = DAYS.map((d, i) => `<button type="button" class="dayb ${st.day === d ? "on" : ""}" aria-pressed="${st.day === d}" data-action="day" data-day="${d}">${esc(s.days[i])}${dirty.includes(st.prog + d) ? "•" : ""}</button>`).join("");
    const cells = prog[st.day].map((t, h) => {
      const c = this._cellHtml(t, h, st.day, s);
      return `<button type="button" class="pcell t-${c.role} ${this._isNow(st.day, h) ? "now" : ""}" data-action="paint" data-day="${st.day}" data-hour="${h}" aria-label="${esc(c.label)}"><span class="num hr">${String(h).padStart(2, "0")}:00</span>${c.off ? SNOW : `<span class="num big">${t === null ? "—" : t + "°"}</span>`}</button>`;
    }).join("");
    return `
      ${this._tabsHtml()}
      <div class="week">${week}</div>
      <div class="days">${days}</div>
      <div class="pgrid">${cells}</div>
      ${this._brushHtml(s, true)}
      ${this._copyHtml(s, st.day, false)}
      ${this._footerHtml(s)}`;
  }

  // ---- events

  _onInput(e) {
    if (this._st.saving) return; // edits made now would not be written
    const el = e.target.closest("[data-input]");
    if (!el) return;
    if (el.dataset.input === "brush") {
      const t = Number(el.value);
      this._st.brush = t; this._st.lastTemp = t;
      if (e.type === "change") this._render();
      else {
        const sw = this.shadowRoot.querySelector(".swatch");
        if (sw) { sw.className = `swatch t-${tempRole(t)} num`; sw.textContent = t + "°"; }
        this.shadowRoot.querySelector(".offbtn")?.classList.remove("on");
      }
    } else if (el.dataset.input === "copy-src" && e.type === "change") {
      this._st.copySrc = el.value;
      this._st.copyDst = this._st.copyDst.filter((d) => d !== el.value);
      this._render();
    }
  }

  _onClick(e) {
    const el = e.target.closest("[data-action]");
    if (!el) return;
    const a = el.dataset.action;
    if (a === "backdrop" && e.target !== el) return;
    const st = this._st;
    if (st.saving) return; // frozen until the write finishes
    switch (a) {
      case "backdrop":
      case "close": this.close(); return;
      case "prog": st.prog = Number(el.dataset.prog); st.copyDst = []; break;
      case "day": st.day = el.dataset.day; st.copyDst = st.copyDst.filter((d) => d !== st.day); break;
      case "paint": this._edit[st.prog][el.dataset.day][Number(el.dataset.hour)] = st.brush; st.error = ""; break;
      case "brush-step": st.brush = Math.min(MAX_TEMP, Math.max(MIN_TEMP, (st.brush === OFF_TEMP ? st.lastTemp : st.brush) + Number(el.dataset.step))); st.lastTemp = st.brush; break;
      case "brush-off": if (st.brush === OFF_TEMP) st.brush = st.lastTemp; else { st.lastTemp = st.brush; st.brush = OFF_TEMP; } break;
      case "copy-src": st.copySrc = el.dataset.day; st.copyDst = st.copyDst.filter((d) => d !== st.copySrc); break;
      case "copy-dst": {
        const d = el.dataset.day;
        st.copyDst = st.copyDst.includes(d) ? st.copyDst.filter((x) => x !== d) : [...st.copyDst, d];
        break;
      }
      case "copy-pick": {
        const src = this._portrait() ? st.day : st.copySrc;
        st.copyDst = (el.dataset.set === "weekdays" ? DAYS.slice(0, 5) : DAYS).filter((d) => d !== src);
        break;
      }
      case "copy-do": {
        const src = this._portrait() ? st.day : st.copySrc;
        for (const d of st.copyDst) this._edit[st.prog][d] = this._edit[st.prog][src].slice();
        st.copyDst = []; st.error = "";
        break;
      }
      case "save": this._save(); return;
      default: return;
    }
    this._render();
  }

  async _save() {
    const calls = scheduleCalls(this._original, this._edit);
    if (!calls.length) { this.close(true); return; }
    this._st.saving = true; this._st.error = ""; this._render();
    try {
      for (const c of calls) {
        await this._hass.callService("tesy", "set_schedule", { entity_id: this._config.entity, ...c });
      }
      this.close(true);
    } catch (err) {
      this._st.saving = false;
      this._st.error = err?.message || String(err);
      this._render();
    }
  }
}

const DIALOG_CSS = `
  .panel.busy > :not(.dhead) { pointer-events: none; opacity: .6; }
  .backdrop { position: fixed; inset: 0; z-index: 9; background: rgba(0,0,0,.55); display: flex; align-items: center; justify-content: center; font-family: var(--paper-font-body1_-_font-family, inherit); }
  .panel { box-sizing: border-box; width: min(460px, 100vw); max-height: 100vh; overflow: auto; padding: 20px 24px 24px; border-radius: 24px; display: flex; flex-direction: column; gap: 16px;
           background: var(--ha-card-background, var(--card-background-color, #171b20)); color: var(--t-text); box-shadow: 0 20px 60px rgba(0,0,0,.4); }
  .panel.wide { width: min(900px, 100vw); }
  @media (max-width: 719px) { .panel { width: 100vw; height: 100vh; max-height: none; border-radius: 0; padding: 12px 16px 20px; } }
  .dhead { display: flex; align-items: center; gap: 10px; }
  h2 { margin: 0; font-size: 19px; font-weight: 600; flex: 1; }
  .x { width: 44px; height: 44px; border-radius: 22px; border: none; background: transparent; display: flex; align-items: center; justify-content: center; margin-right: -8px; }
  .k { font-size: 13px; color: var(--t-muted); margin: 0; }
  .caps { letter-spacing: .04em; text-transform: uppercase; }
  .pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 500; }
  .pill.ok { background: var(--t-ok-bg); color: var(--t-ok-fg); }
  .pill.warm { background: var(--t-warm-bg); color: var(--t-warm-fg); }
  .pill.neutral { background: var(--t-surface-2); color: var(--t-muted); }
  .warmtxt { color: var(--t-warm-fg); } .errtxt { color: var(--error-color, #db4437); }
  /* stats */
  .kpis { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
  .kpi { padding: 14px; border-radius: 16px; background: var(--t-surface); display: flex; flex-direction: column; gap: 6px; }
  .kpi .v { font-size: 24px; font-weight: 600; } .kpi .v span { font-size: 14px; color: var(--t-muted); }
  .rows { border-radius: 16px; background: var(--t-surface); overflow: hidden; }
  .row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 16px; border-bottom: 1px solid var(--t-track); font-size: 15px; }
  .row:last-child { border-bottom: none; } .row > span:last-child { font-size: 14px; text-align: right; }
  .codes { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; font-size: 13px; }
  .codes div { padding: 10px 12px; border-radius: 12px; border: 1px solid var(--t-border); color: var(--t-muted); }
  .codes b { color: var(--t-text); }
  /* schedule shared */
  .tabs { display: flex; gap: 6px; padding: 4px; border-radius: 14px; background: var(--t-surface); }
  .tabs button { flex: 1; min-width: 56px; min-height: 40px; border-radius: 10px; border: none; background: transparent; font-size: 14px; font-weight: 600; }
  .tabs button.on { background: var(--t-accent); color: var(--t-on-accent); }
  .now { outline: 2px solid var(--t-text); outline-offset: 1px; }
  .brush { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  .brush input { flex: 1; min-width: 120px; accent-color: var(--t-accent); }
  .swatch { width: 56px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 600; flex-shrink: 0; }
  .sq { width: 44px; height: 44px; border-radius: 12px; border: 1px solid var(--t-border); background: var(--t-surface-2); font-size: 22px; }
  .offbtn { display: inline-flex; align-items: center; gap: 6px; min-height: 44px; padding: 0 12px; border-radius: 12px; font-size: 14px; font-weight: 500; background: var(--t-off-bg); color: var(--t-off-fg); border: 1px solid var(--t-off-border); }
  .offbtn.on { background: var(--t-off-fg); color: var(--t-on-off); border-color: var(--t-off-fg); }
  .copy { display: flex; flex-direction: column; gap: 8px; padding: 12px; border-radius: 16px; background: var(--t-surface); }
  .copy.wide { flex-direction: row; flex-wrap: wrap; align-items: center; gap: 8px; }
  .ddrow { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)) auto; gap: 4px; }
  .dd { min-width: 40px; min-height: 40px; padding: 0 6px; border-radius: 8px; font-size: 13px; font-weight: 600; background: var(--t-surface-2); border: 1px solid var(--t-border); }
  .dd.on { background: var(--t-inv-bg); color: var(--t-inv-fg); border-color: var(--t-inv-bg); }
  .dd:disabled { background: transparent; color: var(--t-faint); border-style: dashed; }
  .go { min-height: 40px; padding: 0 12px; border-radius: 8px; font-size: 13px; font-weight: 600; background: transparent; border: 1px solid var(--t-border); color: var(--t-faint); }
  .copy.wide .go { margin-left: auto; }
  .go.on { background: var(--t-inv-bg); color: var(--t-inv-fg); border-color: var(--t-inv-bg); }
  .txt { min-height: 40px; padding: 0 8px; border: none; background: transparent; color: var(--t-accent); font-size: 13px; font-weight: 500; }
  select { min-height: 40px; padding: 0 10px; border-radius: 10px; border: 1px solid var(--t-border); background: var(--t-surface-2); color: var(--t-text); font: inherit; font-weight: 600; }
  .foot { display: flex; align-items: center; gap: 12px; padding-top: 16px; border-top: 1px solid var(--t-track); }
  .note { flex: 1; font-size: 13px; color: var(--t-muted); }
  .primary { min-height: 48px; padding: 0 20px; border-radius: 12px; border: 1px solid var(--t-accent); background: var(--t-accent); color: var(--t-on-accent); font-size: 15px; font-weight: 600; }
  /* landscape grid */
  .ghead { display: flex; align-items: center; gap: 16px; } .ghead p { flex: 1; } .ghead .tabs { flex: 0 0 auto; }
  .grid { display: flex; flex-direction: column; gap: 3px; overflow-x: auto; }
  .grow { display: flex; align-items: center; gap: 3px; }
  .dl { width: 36px; flex-shrink: 0; font-size: 13px; font-weight: 500; }
  .hh { width: 28px; flex-shrink: 0; text-align: center; font-size: 11px; color: var(--t-muted); }
  .cell { width: 28px; height: 40px; flex-shrink: 0; padding: 0; border-radius: 6px; font-size: 11px; font-weight: 600; display: flex; align-items: center; justify-content: center; }
  .cell svg { width: 14px; height: 14px; }
  .cp { width: 32px; height: 40px; margin-left: 6px; flex-shrink: 0; padding: 0; border-radius: 8px; display: flex; align-items: center; justify-content: center; background: transparent; color: var(--t-muted); border: 1px solid var(--t-border); }
  .cp.on { background: var(--t-accent); color: var(--t-on-accent); border-color: var(--t-accent); }
  /* portrait */
  .week { display: flex; flex-direction: column; gap: 3px; }
  .wk { display: flex; align-items: center; gap: 1px; height: 16px; padding: 0 4px; border-radius: 4px; border: none; background: transparent; color: var(--t-muted); }
  .wk.on { color: var(--t-text); outline: 1px solid var(--t-muted); outline-offset: 1px; }
  .wl { width: 22px; flex-shrink: 0; font-size: 11px; font-weight: 600; text-align: left; }
  .ws { flex: 1 1 0; height: 10px; border-radius: 2px; border: none !important; }
  .ws.t-empty { background: var(--t-track); }
  .days { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 6px; }
  .dayb { min-height: 44px; padding: 0; border-radius: 10px; font-size: 13px; font-weight: 600; background: var(--t-surface-2); border: 1px solid var(--t-border); }
  .dayb.on { background: var(--t-inv-bg); color: var(--t-inv-fg); border-color: var(--t-inv-bg); }
  .pgrid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
  .pcell { min-height: 56px; padding: 6px 8px; border-radius: 10px; display: flex; flex-direction: column; align-items: flex-start; justify-content: space-between; text-align: left; }
  .pcell .hr { font-size: 11px; opacity: .8; } .pcell .big { font-size: 18px; font-weight: 600; line-height: 1; }
  .panel.schedule:not(.wide) .foot { flex-direction: column; align-items: stretch; text-align: center; border-top: none; padding-top: 0; }
  .panel.schedule:not(.wide) .primary { min-height: 52px; }
  button:disabled { opacity: .55; }
`;

export { TesyBoilerCard, TesyBoilerDialog };

if (typeof customElements !== "undefined") {
  if (!customElements.get("tesy-boiler-card")) customElements.define("tesy-boiler-card", TesyBoilerCard);
  if (!customElements.get("tesy-boiler-dialog")) customElements.define("tesy-boiler-dialog", TesyBoilerDialog);
  window.customCards = window.customCards || [];
  if (!window.customCards.some((c) => c.type === "tesy-boiler-card")) {
    window.customCards.push({
      type: "tesy-boiler-card",
      name: "Tesy boiler",
      description: "Thermostat card for Tesy water heaters: setpoint dial, modes, Boost, weekly programs and diagnostics.",
      preview: true,
      documentationURL: "https://github.com/krasnoukhov/homeassistant-tesy",
    });
  }
  console.info(`%c TESY-BOILER-CARD %c ${CARD_VERSION} `, "background:#f2a541;color:#1b1206;font-weight:600", "background:#171b20;color:#e8ecef");
}
