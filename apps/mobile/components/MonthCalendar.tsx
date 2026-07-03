import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import type { LoppisSummary } from "@loppis/shared";
import { useI18n } from "@/lib/I18nProvider";
import { useTheme } from "@/lib/ThemeProvider";
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
  const { c } = useTheme();
  const now = new Date();
  const [viewYear, setViewYear] = useState(range.from.getFullYear());
  const [viewMonth, setViewMonth] = useState(range.from.getMonth());
  const [selectingEnd, setSelectingEnd] = useState(false);
  const [view, setView] = useState<CalendarView>(() => (isFullYearRange(range) ? "year" : "month"));

  useEffect(() => {
    if (isFullYearRange(range)) {
      setView("year");
      setViewYear(range.from.getFullYear());
    }
  }, [range]);

  const months = monthNames(locale);
  const weekdays = weekdayNames(locale);
  const days = buildCalendarDays(viewYear, viewMonth);

  const shiftMonth = (delta: number) => {
    const d = new Date(viewYear, viewMonth + delta, 1);
    setViewYear(d.getFullYear());
    setViewMonth(d.getMonth());
    setView("month");
  };

  const shiftYear = (delta: number) => setViewYear((y) => y + delta);

  const handleDayClick = (day: Date) => {
    if (!selectingEnd) {
      onRangeChange({ from: startOfDay(day), to: endOfDay(day) });
      setSelectingEnd(true);
    } else {
      const from = startOfDay(range.from);
      const to = startOfDay(day);
      onRangeChange(
        to.getTime() < from.getTime()
          ? { from: startOfDay(day), to: endOfDay(range.from) }
          : { from, to: endOfDay(day) }
      );
      setSelectingEnd(false);
    }
    setView("month");
  };

  const selectFullMonth = () => {
    onRangeChange({ from: startOfMonth(viewYear, viewMonth), to: endOfMonth(viewYear, viewMonth) });
    setSelectingEnd(false);
    setView("month");
  };

  const selectFullYear = () => {
    onRangeChange({ from: startOfMonth(viewYear, 0), to: endOfMonth(viewYear, 11) });
    setSelectingEnd(false);
    setView("year");
  };

  const selectCurrentMonth = () => {
    onRangeChange(currentMonthRange());
    setViewYear(now.getFullYear());
    setViewMonth(now.getMonth());
    setSelectingEnd(false);
    setView("month");
  };

  const openMonth = (month: number) => {
    onRangeChange({ from: startOfMonth(viewYear, month), to: endOfMonth(viewYear, month) });
    setViewMonth(month);
    setView("month");
  };

  const monthInRange = (month: number) => {
    if (isFullYearRange(range) && range.from.getFullYear() === viewYear) return true;
    return isFullMonthRange(range, viewYear, month);
  };

  return (
    <View style={[styles.panel, { backgroundColor: c.surfaceMuted, borderColor: c.border }]}>
      <View style={styles.nav}>
        <Pressable style={[styles.navBtn, { borderColor: c.border, backgroundColor: c.surface }]} onPress={() => (view === "year" ? shiftYear(-1) : shiftMonth(-1))}>
          <Text style={{ color: c.text }}>←</Text>
        </Pressable>
        <Text style={[styles.title, { color: c.text }]}>
          {view === "year" ? String(viewYear) : formatMonthYear(locale, viewYear, viewMonth)}
        </Text>
        <Pressable style={[styles.navBtn, { borderColor: c.border, backgroundColor: c.surface }]} onPress={() => (view === "year" ? shiftYear(1) : shiftMonth(1))}>
          <Text style={{ color: c.text }}>→</Text>
        </Pressable>
      </View>

      <Text style={[styles.rangeLabel, { color: c.textMuted }]}>
        {formatRangeLabel(locale, range)}
        {selectingEnd ? t("selectEndDate") : ""}
      </Text>

      <View style={styles.toolbar}>
        {view === "year" ? (
          <Pressable style={[styles.toolBtn, { borderColor: c.border, backgroundColor: c.surface }]} onPress={() => setView("month")}>
            <Text style={[styles.toolText, { color: c.text }]}>{t("monthView")}</Text>
          </Pressable>
        ) : (
          <Pressable style={[styles.toolBtn, { borderColor: c.border, backgroundColor: c.surface }]} onPress={selectFullMonth}>
            <Text style={[styles.toolText, { color: c.text }]}>{t("wholeMonth")}</Text>
          </Pressable>
        )}
        <Pressable style={[styles.toolBtn, { borderColor: c.border, backgroundColor: c.surface }]} onPress={selectFullYear}>
          <Text style={[styles.toolText, { color: c.text }]}>{t("wholeYear")}</Text>
        </Pressable>
        <Pressable style={[styles.toolBtn, { borderColor: c.currentMonth, backgroundColor: c.currentMonthSoft }]} onPress={selectCurrentMonth}>
          <Text style={[styles.toolText, { color: c.text, fontWeight: "700" }]}>{t("currentMonth")}</Text>
        </Pressable>
      </View>

      {view === "year" ? (
        <View style={styles.monthGrid}>
          {months.map((name, monthIndex) => {
            const count = countLoppisInMonth(viewYear, monthIndex, loppis);
            const isNow = viewYear === now.getFullYear() && monthIndex === now.getMonth();
            const inRange = monthInRange(monthIndex);
            return (
              <Pressable
                key={name}
                style={[
                  styles.monthTile,
                  { borderColor: c.border, backgroundColor: inRange ? c.primarySoft : c.surface },
                  isNow && { borderColor: c.currentMonth, borderWidth: 2, backgroundColor: c.currentMonthSoft },
                ]}
                onPress={() => openMonth(monthIndex)}
              >
                <Text style={[styles.monthName, { color: c.text }]}>{name}</Text>
                <Text style={[styles.monthCount, { color: c.primary }]}>{t("loppisCount", { count })}</Text>
              </Pressable>
            );
          })}
        </View>
      ) : (
        <View>
          <View style={styles.dayHeader}>
            {weekdays.map((w) => (
              <Text key={w} style={[styles.weekday, { color: c.textSubtle }]}>
                {w}
              </Text>
            ))}
          </View>
          <View style={styles.dayGrid}>
            {days.map((day, i) => {
              if (!day) return <View key={`e-${i}`} style={styles.dayCell} />;
              const inRange = isInRange(day, range);
              const isStart = sameDay(day, range.from);
              const isEnd = sameDay(day, range.to);
              const count = countLoppisOnDay(day, loppis);
              const isToday = sameDay(day, now);
              const endpoint = isStart || isEnd;
              return (
                <Pressable
                  key={day.toISOString()}
                  style={[
                    styles.dayCell,
                    styles.dayBtn,
                    { backgroundColor: endpoint ? c.primary : inRange ? c.primarySoft : c.surface },
                    isToday && !endpoint && { borderColor: c.primary, borderWidth: 2 },
                  ]}
                  onPress={() => handleDayClick(day)}
                >
                  <Text style={{ color: endpoint ? c.primaryText : c.text, fontSize: 11 }}>{day.getDate()}</Text>
                  {count > 0 && (
                    <Text style={{ color: endpoint ? c.primaryText : c.primary, fontSize: 9, fontWeight: "700" }}>
                      {count}
                    </Text>
                  )}
                </Pressable>
              );
            })}
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  panel: { padding: 12, borderBottomWidth: 1 },
  nav: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 6 },
  navBtn: { borderWidth: 1, borderRadius: 6, paddingHorizontal: 12, paddingVertical: 4 },
  title: { fontSize: 14, fontWeight: "600", textTransform: "capitalize" },
  rangeLabel: { fontSize: 11, marginBottom: 8 },
  toolbar: { flexDirection: "row", gap: 6, marginBottom: 8, flexWrap: "wrap" },
  toolBtn: { flex: 1, minWidth: 90, borderWidth: 1, borderRadius: 6, paddingVertical: 6, alignItems: "center" },
  toolText: { fontSize: 11 },
  monthGrid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  monthTile: {
    width: "30%",
    flexGrow: 1,
    borderWidth: 1,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: "center",
    gap: 4,
  },
  monthName: { fontSize: 12, fontWeight: "600", textTransform: "capitalize" },
  monthCount: { fontSize: 10, fontWeight: "700" },
  dayHeader: { flexDirection: "row" },
  weekday: { flex: 1, textAlign: "center", fontSize: 10, fontWeight: "600", paddingVertical: 2 },
  dayGrid: { flexDirection: "row", flexWrap: "wrap" },
  dayCell: { width: `${100 / 7}%`, aspectRatio: 1, padding: 1 },
  dayBtn: { borderRadius: 6, alignItems: "center", justifyContent: "center" },
});
