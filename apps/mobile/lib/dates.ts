import type { Locale } from "./i18n";

const MONTHS: Record<Locale, string[]> = {
  sv: [
    "januari", "februari", "mars", "april", "maj", "juni",
    "juli", "augusti", "september", "oktober", "november", "december",
  ],
  en: [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ],
};

const WEEKDAYS: Record<Locale, string[]> = {
  sv: ["mån", "tis", "ons", "tor", "fre", "lör", "sön"],
  en: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
};

export type DateRange = { from: Date; to: Date };

export function startOfDay(d: Date): Date {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x;
}

export function endOfDay(d: Date): Date {
  const x = new Date(d);
  x.setHours(23, 59, 59, 999);
  return x;
}

export function startOfMonth(year: number, month: number): Date {
  return startOfDay(new Date(year, month, 1));
}

export function endOfMonth(year: number, month: number): Date {
  return endOfDay(new Date(year, month + 1, 0));
}

export function currentYearRange(): DateRange {
  const now = new Date();
  return { from: startOfMonth(now.getFullYear(), 0), to: endOfMonth(now.getFullYear(), 11) };
}

export function currentMonthRange(): DateRange {
  const now = new Date();
  return {
    from: startOfMonth(now.getFullYear(), now.getMonth()),
    to: endOfMonth(now.getFullYear(), now.getMonth()),
  };
}

export function sameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

export function isInRange(day: Date, range: DateRange): boolean {
  const t = startOfDay(day).getTime();
  return t >= startOfDay(range.from).getTime() && t <= startOfDay(range.to).getTime();
}

export function isFullYearRange(range: DateRange): boolean {
  const year = range.from.getFullYear();
  return (
    range.from.getMonth() === 0 &&
    range.from.getDate() === 1 &&
    range.to.getFullYear() === year &&
    range.to.getMonth() === 11 &&
    range.to.getDate() === 31
  );
}

export function isFullMonthRange(range: DateRange, year: number, month: number): boolean {
  return (
    sameDay(range.from, startOfMonth(year, month)) &&
    sameDay(range.to, endOfMonth(year, month))
  );
}

export function monthNames(locale: Locale): string[] {
  return MONTHS[locale];
}

export function weekdayNames(locale: Locale): string[] {
  return WEEKDAYS[locale];
}

export function formatMonthYear(locale: Locale, year: number, month: number): string {
  return `${MONTHS[locale][month]} ${year}`;
}

export function formatRangeLabel(locale: Locale, range: DateRange): string {
  const months = MONTHS[locale];
  const f = range.from;
  const t = range.to;
  if (sameDay(f, t)) return `${f.getDate()} ${months[f.getMonth()]} ${f.getFullYear()}`;
  if (f.getMonth() === t.getMonth() && f.getFullYear() === t.getFullYear()) {
    return `${f.getDate()}–${t.getDate()} ${months[f.getMonth()]} ${f.getFullYear()}`;
  }
  if (isFullYearRange(range)) {
    return locale === "sv" ? `Hela ${f.getFullYear()}` : `Whole year ${f.getFullYear()}`;
  }
  return `${f.getDate()} ${months[f.getMonth()]} – ${t.getDate()} ${months[t.getMonth()]} ${t.getFullYear()}`;
}

export function buildCalendarDays(viewYear: number, viewMonth: number): (Date | null)[] {
  const first = new Date(viewYear, viewMonth, 1);
  const startPad = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
  const cells: (Date | null)[] = [];
  for (let i = 0; i < startPad; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(new Date(viewYear, viewMonth, d));
  return cells;
}

export function countLoppisOnDay(day: Date, loppis: { start_at: string }[]): number {
  return loppis.filter((l) => sameDay(new Date(l.start_at), day)).length;
}

export function countLoppisInMonth(year: number, month: number, loppis: { start_at: string }[]): number {
  return loppis.filter((l) => {
    const d = new Date(l.start_at);
    return d.getFullYear() === year && d.getMonth() === month;
  }).length;
}
