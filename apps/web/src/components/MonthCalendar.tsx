"use client";

import { useEffect, useState } from "react";
import type { LoppisSummary } from "@loppis/shared";
import { useI18n } from "@/lib/i18n/context";
import {
  type DateRange,
  buildCalendarDays,
  countLoppisInMonth,
  countLoppisOnDay,
  currentMonthRange,
  endOfDay,
  endOfMonth,
  formatMonthYear,
  formatRangeLabel,
  isFullMonthRange,
  isFullYearRange,
  isInRange,
  monthNames,
  sameDay,
  startOfDay,
  startOfMonth,
  weekdayNames,
} from "@/lib/dates";

type CalendarView = "month" | "year";

interface Props {
  range: DateRange;
  onRangeChange: (range: DateRange) => void;
  loppis: LoppisSummary[];
}

export function MonthCalendar({ range, onRangeChange, loppis }: Props) {
  const { locale, t } = useI18n();
  const now = new Date();
  const [viewYear, setViewYear] = useState(range.from.getFullYear());
  const [viewMonth, setViewMonth] = useState(range.from.getMonth());
  const [selectingEnd, setSelectingEnd] = useState(false);
  const [view, setView] = useState<CalendarView>(() =>
    isFullYearRange(range) ? "year" : "month"
  );

  useEffect(() => {
    if (isFullYearRange(range)) {
      setView("year");
      setViewYear(range.from.getFullYear());
    }
  }, [range]);

  const months = monthNames(locale);
  const weekdays = weekdayNames(locale);
  const days = buildCalendarDays(viewYear, viewMonth);
  const isCurrentMonth =
    viewYear === now.getFullYear() && viewMonth === now.getMonth();

  const shiftMonth = (delta: number) => {
    const d = new Date(viewYear, viewMonth + delta, 1);
    setViewYear(d.getFullYear());
    setViewMonth(d.getMonth());
    setView("month");
  };

  const shiftYear = (delta: number) => {
    setViewYear((y) => y + delta);
  };

  const handleDayClick = (day: Date) => {
    if (!selectingEnd) {
      onRangeChange({ from: startOfDay(day), to: endOfDay(day) });
      setSelectingEnd(true);
    } else {
      const from = startOfDay(range.from);
      const to = startOfDay(day);
      if (to.getTime() < from.getTime()) {
        onRangeChange({ from: startOfDay(day), to: endOfDay(range.from) });
      } else {
        onRangeChange({ from, to: endOfDay(day) });
      }
      setSelectingEnd(false);
    }
    setView("month");
  };

  const selectFullMonth = () => {
    onRangeChange({
      from: startOfMonth(viewYear, viewMonth),
      to: endOfMonth(viewYear, viewMonth),
    });
    setSelectingEnd(false);
    setView("month");
  };

  const selectFullYear = () => {
    onRangeChange({
      from: startOfMonth(viewYear, 0),
      to: endOfMonth(viewYear, 11),
    });
    setSelectingEnd(false);
    setView("year");
  };

  const selectCurrentMonth = () => {
    const monthRange = currentMonthRange();
    onRangeChange(monthRange);
    setViewYear(now.getFullYear());
    setViewMonth(now.getMonth());
    setSelectingEnd(false);
    setView("month");
  };

  const openMonth = (month: number) => {
    onRangeChange({
      from: startOfMonth(viewYear, month),
      to: endOfMonth(viewYear, month),
    });
    setViewMonth(month);
    setSelectingEnd(false);
    setView("month");
  };

  const monthInSelectedRange = (month: number) => {
    if (isFullYearRange(range) && range.from.getFullYear() === viewYear) return true;
    return isFullMonthRange(range, viewYear, month);
  };

  return (
    <div className="calendar-panel">
      <div className="calendar-nav">
        <button
          type="button"
          className="btn-secondary"
          onClick={() => (view === "year" ? shiftYear(-1) : shiftMonth(-1))}
        >
          ←
        </button>
        <strong className="calendar-title">
          {view === "year"
            ? String(viewYear)
            : formatMonthYear(locale, viewYear, viewMonth)}
        </strong>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => (view === "year" ? shiftYear(1) : shiftMonth(1))}
        >
          →
        </button>
      </div>

      <p className="calendar-range-label">
        {formatRangeLabel(locale, range)}
        {selectingEnd && t("selectEndDate")}
      </p>

      <div className="calendar-toolbar">
        {view === "year" ? (
          <button type="button" className="btn-secondary" onClick={() => setView("month")}>
            {t("monthView")}
          </button>
        ) : (
          <button type="button" className="btn-secondary" onClick={selectFullMonth}>
            {t("wholeMonth")}
          </button>
        )}
        <button type="button" className="btn-secondary" onClick={selectFullYear}>
          {t("wholeYear")}
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={selectCurrentMonth}
          style={
            isCurrentMonth && view === "month"
              ? { borderColor: "var(--color-current-month)", fontWeight: 600 }
              : undefined
          }
        >
          {t("currentMonth")}
        </button>
      </div>

      {view === "year" ? (
        <div className="calendar-month-grid">
          {months.map((name, monthIndex) => {
            const count = countLoppisInMonth(viewYear, monthIndex, loppis);
            const isNow =
              viewYear === now.getFullYear() && monthIndex === now.getMonth();
            const inRange = monthInSelectedRange(monthIndex);
            const classes = ["calendar-month-tile"];
            if (inRange) classes.push("in-range");
            if (isNow) classes.push("current-month");

            return (
              <button
                key={name}
                type="button"
                className={classes.join(" ")}
                onClick={() => openMonth(monthIndex)}
              >
                <span className="calendar-month-name">{name}</span>
                <span className="calendar-month-count">
                  {t("loppisCount", { count })}
                </span>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="calendar-day-grid">
          {weekdays.map((w) => (
            <div key={w} className="calendar-weekday">
              {w}
            </div>
          ))}
          {days.map((day, i) => {
            if (!day) return <div key={`empty-${i}`} />;
            const inRange = isInRange(day, range);
            const isStart = sameDay(day, range.from);
            const isEnd = sameDay(day, range.to);
            const count = countLoppisOnDay(day, loppis);
            const isToday = sameDay(day, now);
            const classes = ["calendar-day"];
            if (isToday) classes.push("today");
            if (inRange) classes.push("in-range");
            if (isStart || isEnd) classes.push("range-endpoint");

            return (
              <button
                key={day.toISOString()}
                type="button"
                className={classes.join(" ")}
                onClick={() => handleDayClick(day)}
              >
                <span>{day.getDate()}</span>
                {count > 0 && <span className="calendar-day-count">{count}</span>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
