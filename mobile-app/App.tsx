import { StatusBar } from "expo-status-bar";
import DateTimePicker, {
  DateTimePickerEvent,
} from "@react-native-community/datetimepicker";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Linking,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import {
  getAssignedRoute,
  getStaff,
  RouteVisit,
  StaffMember,
  submitVisitAction,
  VisitAction,
  VisitStatus,
} from "./src/api";

const COLORS = {
  ink: "#142536",
  muted: "#6A7B89",
  line: "#E0E7EC",
  background: "#F3F6F8",
  white: "#FFFFFF",
  blue: "#1769AA",
  blueLight: "#E8F2FA",
  green: "#1A8055",
  greenLight: "#E7F5EE",
  amber: "#9B6300",
  amberLight: "#FFF4D8",
  red: "#B43A3A",
  redLight: "#FCECEC",
};

function dateToIso(date: Date): string {
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return localDate.toISOString().slice(0, 10);
}

function isoToDate(value: string): Date {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function shiftDateByDays(value: string, days: number): string {
  const shifted = isoToDate(value);
  shifted.setDate(shifted.getDate() + days);
  return dateToIso(shifted);
}

function formatTime(value?: string): string | undefined {
  if (!value) return undefined;
  const parsed = new Date(value);
  if (!Number.isNaN(parsed.getTime()) && value.includes("T")) {
    return parsed.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  const match = value.match(/(?:T|\s)?(\d{2}:\d{2})/);
  return match?.[1] ?? value;
}

function statusLabel(status?: VisitStatus): string {
  switch (status) {
    case "IN_PROGRESS":
      return "В работе";
    case "DONE":
      return "Завершён";
    case "PLANNED":
      return "Запланирован";
    default:
      return "Статус не указан";
  }
}

function statusColors(status?: VisitStatus) {
  switch (status) {
    case "IN_PROGRESS":
      return { backgroundColor: COLORS.amberLight, color: COLORS.amber };
    case "DONE":
      return { backgroundColor: COLORS.greenLight, color: COLORS.green };
    case "PLANNED":
      return { backgroundColor: COLORS.blueLight, color: COLORS.blue };
    default:
      return { backgroundColor: COLORS.background, color: COLORS.muted };
  }
}

function VisitTime({ visit }: { visit: RouteVisit }) {
  const arrival = formatTime(visit.arrival);
  const start = formatTime(visit.start);
  const end = formatTime(visit.end);
  const timeText =
    start && end
      ? `${start}–${end}`
      : arrival
        ? `Прибытие ${arrival}`
        : start || end;

  if (!timeText) return <Text style={styles.timeText}>Время не указано</Text>;
  return <Text style={styles.timeText}>{timeText}</Text>;
}

export default function App() {
  const [date, setDate] = useState(() => dateToIso(new Date()));
  const [pendingDate, setPendingDate] = useState(() => isoToDate(dateToIso(new Date())));
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showStaffPicker, setShowStaffPicker] = useState(false);
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [selectedStaffId, setSelectedStaffId] = useState("");
  const [staffLoading, setStaffLoading] = useState(true);
  const [staffError, setStaffError] = useState("");
  const [staffRetry, setStaffRetry] = useState(0);
  const [visits, setVisits] = useState<RouteVisit[]>([]);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeError, setRouteError] = useState("");
  const [routeRetry, setRouteRetry] = useState(0);
  const [busyAction, setBusyAction] = useState("");
  const [actionError, setActionError] = useState("");
  const [actionFeedback, setActionFeedback] = useState("");
  const [mapError, setMapError] = useState("");
  const today = dateToIso(new Date());
  const minRouteDate = shiftDateByDays(today, -7);
  const maxRouteDate = shiftDateByDays(today, 7);
  const previousDay = shiftDateByDays(date, -1);
  const nextDay = shiftDateByDays(date, 1);

  const selectedStaff = useMemo(
    () => staff.find((member) => member.staff_id === selectedStaffId),
    [staff, selectedStaffId],
  );

  useEffect(() => {
    const controller = new AbortController();
    setStaffLoading(true);
    setStaffError("");
    getStaff(controller.signal)
      .then((members) => {
        setStaff(members);
        setSelectedStaffId((current) =>
          members.some((member) => member.staff_id === current)
            ? current
            : (members[0]?.staff_id ?? ""),
        );
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setStaffError(
            error instanceof Error ? error.message : "Не удалось загрузить список сотрудников.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setStaffLoading(false);
      });

    return () => controller.abort();
  }, [staffRetry]);

  useEffect(() => {
    if (!selectedStaffId || staffLoading || staffError) {
      setVisits([]);
      setRouteLoading(false);
      setRouteError("");
      return;
    }

    const controller = new AbortController();
    setRouteLoading(true);
    setRouteError("");
    setActionError("");
    getAssignedRoute(date, selectedStaffId, controller.signal)
      .then((routeVisits) => setVisits(routeVisits))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setVisits([]);
          setRouteError(
            error instanceof Error ? error.message : "Не удалось загрузить маршрут.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setRouteLoading(false);
      });

    return () => controller.abort();
  }, [date, selectedStaffId, staffLoading, staffError, routeRetry]);

  const retryRoute = useCallback(() => setRouteRetry((attempt) => attempt + 1), []);

  const performAction = useCallback(
    async (visit: RouteVisit, action: VisitAction) => {
      const requestKey = `${visit.orderId}:${action}`;
      setBusyAction(requestKey);
      setActionError("");
      setActionFeedback("");
      try {
        await submitVisitAction(date, selectedStaffId, visit.orderId, action);
        setActionFeedback(`${actionLabel(action)} сохранено для наряда ${visit.orderId}.`);
        setRouteRetry((attempt) => attempt + 1);
      } catch (error) {
        setActionError(error instanceof Error ? error.message : "Не удалось отправить действие.");
      } finally {
        setBusyAction("");
      }
    },
    [date, selectedStaffId],
  );

  const openNavigation = useCallback(async (visit: RouteVisit) => {
    setMapError("");
    const query =
      visit.latitude !== undefined && visit.longitude !== undefined
        ? `${visit.latitude},${visit.longitude}`
        : visit.address === "Адрес не указан"
          ? ""
          : visit.address;
    if (!query) {
      setMapError("Для этого визита сервер не передал адрес или координаты.");
      return;
    }

    const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
    try {
      await Linking.openURL(url);
    } catch {
      setMapError("Не удалось открыть приложение карт на устройстве.");
    }
  }, []);

  const onDatePickerChange = useCallback(
    (_event: DateTimePickerEvent, chosenDate?: Date) => {
      if (chosenDate) {
        if (Platform.OS === "ios") setPendingDate(chosenDate);
        else setDate(dateToIso(chosenDate));
      }
      if (Platform.OS !== "ios") setShowDatePicker(false);
    },
    [],
  );

  const chooseDate = useCallback(() => {
    setDate(dateToIso(pendingDate));
    setShowDatePicker(false);
  }, [pendingDate]);

  return (
    <SafeAreaProvider>
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="dark" />
      <ScrollView contentContainerStyle={styles.screen} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <View style={styles.brandMark}>
            <Text style={styles.brandMarkText}>М</Text>
          </View>
          <View style={styles.headerCopy}>
            <Text style={styles.eyebrow}>РАБОЧИЙ ДЕНЬ</Text>
            <Text style={styles.title}>Мой маршрут</Text>
          </View>
        </View>

        <View style={styles.filtersCard}>
          <Text style={styles.sectionLabel}>Сотрудник</Text>
          {staffLoading ? (
            <View style={styles.inlineLoading}>
              <ActivityIndicator color={COLORS.blue} />
              <Text style={styles.mutedText}>Загружаем сотрудников…</Text>
            </View>
          ) : staffError ? (
            <View style={styles.inlineError}>
              <Text style={styles.errorText}>{staffError}</Text>
              <Pressable
                accessibilityRole="button"
                onPress={() => setStaffRetry((attempt) => attempt + 1)}
                style={styles.textButton}
              >
                <Text style={styles.textButtonLabel}>Повторить</Text>
              </Pressable>
            </View>
          ) : staff.length === 0 ? (
            <Text style={styles.mutedText}>Список сотрудников пуст.</Text>
          ) : (
            <>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Выбрать сотрудника"
                onPress={() => setShowStaffPicker(true)}
                style={styles.selectButton}
              >
                <View>
                  <Text style={styles.selectValue}>
                    {selectedStaff?.display_name || selectedStaff?.staff_id}
                  </Text>
                  <Text style={styles.selectDetail}>{selectedStaff?.staff_id}</Text>
                </View>
                <Text style={styles.chevron}>⌄</Text>
              </Pressable>
              <View style={styles.separator} />
              <Text style={styles.sectionLabel}>Дата маршрута</Text>
              <View style={styles.dateNavigator}>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Предыдущий день"
                  accessibilityState={{ disabled: previousDay < minRouteDate }}
                  disabled={previousDay < minRouteDate}
                  onPress={() => setDate(previousDay)}
                  style={[
                    styles.dateStepButton,
                    previousDay < minRouteDate && styles.buttonDisabled,
                  ]}
                >
                  <Text style={styles.dateStepLabel}>‹</Text>
                </Pressable>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Выбрать дату"
                  onPress={() => {
                    setPendingDate(isoToDate(date));
                    setShowDatePicker(true);
                  }}
                  style={styles.dateButton}
                >
                  <Text style={styles.calendarIcon}>▦</Text>
                  <Text style={styles.selectValue}>{date}</Text>
                  <Text style={styles.changeLabel}>Изменить</Text>
                </Pressable>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Следующий день"
                  accessibilityState={{ disabled: nextDay > maxRouteDate }}
                  disabled={nextDay > maxRouteDate}
                  onPress={() => setDate(nextDay)}
                  style={[
                    styles.dateStepButton,
                    nextDay > maxRouteDate && styles.buttonDisabled,
                  ]}
                >
                  <Text style={styles.dateStepLabel}>›</Text>
                </Pressable>
              </View>
            </>
          )}
        </View>

        {staffError ? null : !selectedStaffId && !staffLoading ? (
          <StateCard
            title="Выберите сотрудника"
            message="Чтобы загрузить назначенный маршрут, выберите сотрудника из справочника."
          />
        ) : routeLoading ? (
          <StateCard
            title="Загружаем маршрут"
            message={`${date} · ${selectedStaff?.display_name || selectedStaffId}`}
            loading
          />
        ) : routeError ? (
          <StateCard
            title="Маршрут недоступен"
            message={routeError}
            actionLabel="Повторить загрузку"
            onAction={retryRoute}
            error
          />
        ) : visits.length === 0 ? (
          <StateCard
            title="На эту дату визитов нет"
            message="Сервер не назначил сотруднику визиты на выбранный день."
          />
        ) : (
          <>
            <View style={styles.routeSummary}>
              <View>
                <Text style={styles.sectionLabel}>ПЛАН НА ДЕНЬ</Text>
                <Text style={styles.summaryTitle}>
                  {visits.length} {visits.length === 1 ? "визит" : "визитов"}
                </Text>
              </View>
              <View style={styles.summaryPill}>
                <Text style={styles.summaryPillText}>
                  {visits.filter((visit) => visit.status === "DONE").length} выполнено
                </Text>
              </View>
            </View>

            {actionFeedback ? (
              <View style={styles.successBanner}>
                <Text style={styles.successText}>{actionFeedback}</Text>
              </View>
            ) : null}
            {actionError ? (
              <View style={styles.errorBanner}>
                <Text style={styles.errorText}>{actionError}</Text>
              </View>
            ) : null}
            {mapError ? (
              <View style={styles.errorBanner}>
                <Text style={styles.errorText}>{mapError}</Text>
              </View>
            ) : null}

            <View style={styles.visitList}>
              {visits.map((visit, index) => (
                <VisitCard
                  key={visit.orderId}
                  visit={visit}
                  index={index}
                  busyAction={busyAction}
                  onAction={performAction}
                  onNavigate={openNavigation}
                />
              ))}
            </View>
          </>
        )}
        <Text style={styles.footer}>Данные загружаются из рабочего API</Text>
      </ScrollView>

      <Modal
        animationType="slide"
        transparent
        visible={showStaffPicker}
        onRequestClose={() => setShowStaffPicker(false)}
      >
        <Pressable style={styles.modalScrim} onPress={() => setShowStaffPicker(false)}>
          <Pressable style={styles.staffSheet} onPress={(event) => event.stopPropagation()}>
            <View style={styles.sheetHandle} />
            <Text style={styles.sheetTitle}>Выберите сотрудника</Text>
            <FlatList
              data={staff}
              keyExtractor={(member) => member.staff_id}
              renderItem={({ item }) => {
                const isSelected = item.staff_id === selectedStaffId;
                return (
                  <Pressable
                    accessibilityRole="button"
                    onPress={() => {
                      setSelectedStaffId(item.staff_id);
                      setShowStaffPicker(false);
                    }}
                    style={[styles.staffOption, isSelected && styles.staffOptionSelected]}
                  >
                    <View style={styles.staffAvatar}>
                      <Text style={styles.staffAvatarText}>
                        {(item.display_name || item.staff_id).slice(0, 1).toUpperCase()}
                      </Text>
                    </View>
                    <View style={styles.staffOptionCopy}>
                      <Text style={styles.staffName}>
                        {item.display_name || item.staff_id}
                      </Text>
                      <Text style={styles.staffId}>{item.staff_id}</Text>
                    </View>
                    {isSelected ? <Text style={styles.selectedCheck}>✓</Text> : null}
                  </Pressable>
                );
              }}
            />
          </Pressable>
        </Pressable>
      </Modal>

      {showDatePicker && Platform.OS === "ios" ? (
        <Modal
          animationType="slide"
          transparent
          visible
          onRequestClose={() => setShowDatePicker(false)}
        >
          <View style={styles.modalScrim}>
            <View style={styles.dateSheet}>
              <View style={styles.sheetHandle} />
              <Text style={styles.sheetTitle}>Выберите дату</Text>
              <DateTimePicker
                value={pendingDate}
                mode="date"
                display="spinner"
                onChange={onDatePickerChange}
                minimumDate={isoToDate(minRouteDate)}
                maximumDate={isoToDate(maxRouteDate)}
              />
              <View style={styles.dateSheetActions}>
                <Pressable
                  accessibilityRole="button"
                  onPress={() => setShowDatePicker(false)}
                  style={styles.cancelButton}
                >
                  <Text style={styles.cancelButtonLabel}>Отмена</Text>
                </Pressable>
                <Pressable
                  accessibilityRole="button"
                  onPress={chooseDate}
                  style={styles.primaryButton}
                >
                  <Text style={styles.primaryButtonLabel}>Готово</Text>
                </Pressable>
              </View>
            </View>
          </View>
        </Modal>
      ) : null}
      {showDatePicker && Platform.OS !== "ios" ? (
        <DateTimePicker
          value={isoToDate(date)}
          mode="date"
          display="default"
          onChange={onDatePickerChange}
          minimumDate={isoToDate(minRouteDate)}
          maximumDate={isoToDate(maxRouteDate)}
        />
      ) : null}
    </SafeAreaView>
    </SafeAreaProvider>
  );
}

function StateCard({
  title,
  message,
  loading,
  error,
  actionLabel,
  onAction,
}: {
  title: string;
  message: string;
  loading?: boolean;
  error?: boolean;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <View style={[styles.stateCard, error && styles.stateCardError]}>
      {loading ? <ActivityIndicator color={COLORS.blue} style={styles.stateSpinner} /> : null}
      <Text style={styles.stateTitle}>{title}</Text>
      <Text style={styles.stateMessage}>{message}</Text>
      {actionLabel && onAction ? (
        <Pressable accessibilityRole="button" onPress={onAction} style={styles.primaryButton}>
          <Text style={styles.primaryButtonLabel}>{actionLabel}</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

function VisitCard({
  visit,
  index,
  busyAction,
  onAction,
  onNavigate,
}: {
  visit: RouteVisit;
  index: number;
  busyAction: string;
  onAction: (visit: RouteVisit, action: VisitAction) => Promise<void>;
  onNavigate: (visit: RouteVisit) => Promise<void>;
}) {
  const badgeColors = statusColors(visit.status);
  const isDone = visit.status === "DONE";
  const isInProgress = visit.status === "IN_PROGRESS";
  return (
    <View style={[styles.visitCard, isDone && styles.visitCardDone]}>
      <View style={styles.visitTopRow}>
        <View style={styles.sequenceBadge}>
          <Text style={styles.sequenceText}>{String(index + 1).padStart(2, "0")}</Text>
        </View>
        <View style={styles.visitTitleColumn}>
          <Text style={styles.visitLabel}>ВИЗИТ</Text>
          <Text style={styles.orderId}>{visit.orderId}</Text>
        </View>
        <View style={[styles.statusBadge, { backgroundColor: badgeColors.backgroundColor }]}>
          <Text style={[styles.statusText, { color: badgeColors.color }]}>
            {statusLabel(visit.status)}
          </Text>
        </View>
      </View>

      <View style={styles.visitDetails}>
        <Text style={styles.addressIcon}>⌖</Text>
        <Text style={styles.addressText}>{visit.address}</Text>
      </View>
      <View style={styles.visitDetails}>
        <Text style={styles.clockIcon}>◷</Text>
        <VisitTime visit={visit} />
      </View>

      <View style={styles.visitActions}>
        <Pressable
          accessibilityRole="button"
          disabled={busyAction !== ""}
          onPress={() => onNavigate(visit)}
          style={({ pressed }) => [
            styles.navigationButton,
            pressed && styles.buttonPressed,
            busyAction !== "" && styles.buttonDisabled,
          ]}
        >
          <Text style={styles.navigationButtonText}>Маршрут</Text>
        </Pressable>
        {!isDone ? (
          <Pressable
            accessibilityRole="button"
            disabled={busyAction !== ""}
            onPress={() => onAction(visit, "CALL_CUSTOMER")}
            style={({ pressed }) => [
              styles.secondaryButton,
              pressed && styles.buttonPressed,
              busyAction !== "" && styles.buttonDisabled,
            ]}
          >
            {busyAction === `${visit.orderId}:CALL_CUSTOMER` ? (
              <ActivityIndicator color={COLORS.blue} size="small" />
            ) : (
            <Text style={styles.secondaryButtonLabel}>Зафиксировать звонок</Text>
            )}
          </Pressable>
        ) : null}
      </View>
      {!isDone ? (
        <View style={styles.progressActions}>
          {!isInProgress ? (
            <ActionButton
              label="Отметить прибытие"
              action="ARRIVED"
              visit={visit}
              busyAction={busyAction}
              onAction={onAction}
            />
          ) : (
            <ActionButton
              label="Завершить визит"
              action="COMPLETED"
              visit={visit}
              busyAction={busyAction}
              onAction={onAction}
              primary
            />
          )}
        </View>
      ) : null}
    </View>
  );
}

function ActionButton({
  label,
  action,
  visit,
  busyAction,
  onAction,
  primary,
}: {
  label: string;
  action: VisitAction;
  visit: RouteVisit;
  busyAction: string;
  onAction: (visit: RouteVisit, action: VisitAction) => Promise<void>;
  primary?: boolean;
}) {
  const busy = busyAction === `${visit.orderId}:${action}`;
  return (
    <Pressable
      accessibilityRole="button"
      disabled={busyAction !== ""}
      onPress={() => onAction(visit, action)}
      style={({ pressed }) => [
        primary ? styles.primaryActionButton : styles.arrivalButton,
        pressed && styles.buttonPressed,
        busyAction !== "" && styles.buttonDisabled,
      ]}
    >
      {busy ? (
        <ActivityIndicator color={primary ? COLORS.white : COLORS.blue} size="small" />
      ) : (
        <Text style={primary ? styles.primaryButtonLabel : styles.arrivalButtonLabel}>{label}</Text>
      )}
    </Pressable>
  );
}

function actionLabel(action: VisitAction): string {
  switch (action) {
    case "CALL_CUSTOMER":
      return "Звонок";
    case "ARRIVED":
      return "Прибытие";
    case "COMPLETED":
      return "Завершение";
  }
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  screen: {
    flexGrow: 1,
    paddingHorizontal: 18,
    paddingTop: 16,
    paddingBottom: 28,
    maxWidth: 720,
    width: "100%",
    alignSelf: "center",
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 20,
  },
  brandMark: {
    width: 46,
    height: 46,
    borderRadius: 15,
    backgroundColor: COLORS.blue,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  brandMarkText: {
    color: COLORS.white,
    fontSize: 23,
    fontWeight: "800",
  },
  headerCopy: { flex: 1 },
  eyebrow: {
    color: COLORS.muted,
    fontSize: 10,
    fontWeight: "800",
    letterSpacing: 1.4,
    marginBottom: 3,
  },
  title: {
    color: COLORS.ink,
    fontSize: 24,
    fontWeight: "800",
    letterSpacing: -0.5,
  },
  filtersCard: {
    backgroundColor: COLORS.white,
    borderRadius: 18,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: COLORS.line,
  },
  sectionLabel: {
    color: COLORS.muted,
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.8,
    marginBottom: 9,
  },
  inlineLoading: {
    minHeight: 50,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  inlineError: { gap: 10 },
  mutedText: {
    color: COLORS.muted,
    fontSize: 14,
    lineHeight: 20,
  },
  errorText: {
    color: COLORS.red,
    fontSize: 13,
    lineHeight: 19,
  },
  textButton: { alignSelf: "flex-start", paddingVertical: 4 },
  textButtonLabel: { color: COLORS.blue, fontSize: 14, fontWeight: "700" },
  selectButton: {
    minHeight: 55,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderWidth: 1,
    borderColor: COLORS.line,
    borderRadius: 12,
    paddingHorizontal: 13,
  },
  selectValue: {
    color: COLORS.ink,
    fontSize: 15,
    fontWeight: "700",
  },
  selectDetail: {
    color: COLORS.muted,
    fontSize: 12,
    marginTop: 2,
  },
  chevron: { color: COLORS.muted, fontSize: 22, marginTop: -7 },
  separator: { height: 1, backgroundColor: COLORS.line, marginVertical: 16 },
  dateNavigator: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  dateButton: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    minHeight: 48,
    paddingHorizontal: 12,
    backgroundColor: COLORS.background,
    borderRadius: 12,
  },
  dateStepButton: {
    width: 42,
    height: 48,
    borderWidth: 1,
    borderColor: COLORS.line,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: COLORS.white,
  },
  dateStepLabel: {
    color: COLORS.blue,
    fontSize: 28,
    lineHeight: 32,
  },
  calendarIcon: {
    color: COLORS.blue,
    fontSize: 19,
    marginRight: 10,
  },
  changeLabel: {
    color: COLORS.blue,
    fontSize: 13,
    fontWeight: "700",
    marginLeft: "auto",
  },
  routeSummary: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
    paddingHorizontal: 2,
  },
  summaryTitle: {
    color: COLORS.ink,
    fontSize: 19,
    fontWeight: "800",
  },
  summaryPill: {
    borderRadius: 20,
    paddingVertical: 7,
    paddingHorizontal: 11,
    backgroundColor: COLORS.greenLight,
  },
  summaryPillText: { color: COLORS.green, fontWeight: "700", fontSize: 12 },
  visitList: { gap: 12 },
  visitCard: {
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: COLORS.line,
    borderRadius: 18,
    padding: 15,
  },
  visitCardDone: { backgroundColor: "#FBFDFC" },
  visitTopRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 14,
  },
  sequenceBadge: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: COLORS.blueLight,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 10,
  },
  sequenceText: { color: COLORS.blue, fontWeight: "800", fontSize: 13 },
  visitTitleColumn: { flex: 1 },
  visitLabel: {
    color: COLORS.muted,
    fontSize: 9,
    fontWeight: "800",
    letterSpacing: 1,
  },
  orderId: { color: COLORS.ink, fontSize: 13, fontWeight: "700", marginTop: 2 },
  statusBadge: { borderRadius: 20, paddingHorizontal: 9, paddingVertical: 6 },
  statusText: { fontSize: 10, fontWeight: "800" },
  visitDetails: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: 9,
  },
  addressIcon: { color: COLORS.blue, width: 24, fontSize: 19, lineHeight: 21 },
  clockIcon: { color: COLORS.muted, width: 24, fontSize: 18, lineHeight: 20 },
  addressText: { flex: 1, color: COLORS.ink, fontSize: 14, lineHeight: 20 },
  timeText: { flex: 1, color: COLORS.muted, fontSize: 13, lineHeight: 20 },
  visitActions: {
    flexDirection: "row",
    gap: 9,
    marginTop: 6,
  },
  navigationButton: {
    minHeight: 42,
    flex: 1,
    borderRadius: 11,
    borderColor: COLORS.line,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  navigationButtonText: { color: COLORS.ink, fontSize: 13, fontWeight: "700" },
  secondaryButton: {
    minHeight: 42,
    flex: 1,
    borderRadius: 11,
    backgroundColor: COLORS.blueLight,
    alignItems: "center",
    justifyContent: "center",
  },
  secondaryButtonLabel: { color: COLORS.blue, fontSize: 13, fontWeight: "700" },
  buttonPressed: { opacity: 0.74 },
  buttonDisabled: { opacity: 0.55 },
  progressActions: { marginTop: 9 },
  arrivalButton: {
    height: 45,
    borderRadius: 11,
    borderColor: COLORS.blue,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  arrivalButtonLabel: { color: COLORS.blue, fontSize: 13, fontWeight: "800" },
  primaryActionButton: {
    height: 45,
    borderRadius: 11,
    backgroundColor: COLORS.blue,
    alignItems: "center",
    justifyContent: "center",
  },
  stateCard: {
    backgroundColor: COLORS.white,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: COLORS.line,
    alignItems: "center",
    padding: 24,
    marginTop: 3,
  },
  stateCardError: { borderColor: "#F2C9C9" },
  stateSpinner: { marginBottom: 13 },
  stateTitle: {
    color: COLORS.ink,
    fontSize: 17,
    fontWeight: "800",
    textAlign: "center",
  },
  stateMessage: {
    color: COLORS.muted,
    fontSize: 13,
    lineHeight: 20,
    textAlign: "center",
    marginTop: 7,
    marginBottom: 5,
  },
  primaryButton: {
    backgroundColor: COLORS.blue,
    borderRadius: 11,
    paddingHorizontal: 16,
    minHeight: 43,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 10,
  },
  primaryButtonLabel: { color: COLORS.white, fontSize: 13, fontWeight: "800" },
  successBanner: {
    padding: 12,
    borderRadius: 12,
    backgroundColor: COLORS.greenLight,
    marginBottom: 12,
  },
  successText: { color: COLORS.green, fontSize: 13, lineHeight: 19, fontWeight: "600" },
  errorBanner: {
    padding: 12,
    borderRadius: 12,
    backgroundColor: COLORS.redLight,
    marginBottom: 12,
  },
  footer: {
    color: COLORS.muted,
    textAlign: "center",
    fontSize: 11,
    marginTop: 20,
  },
  modalScrim: {
    flex: 1,
    justifyContent: "flex-end",
    backgroundColor: "rgba(12, 27, 40, 0.42)",
  },
  staffSheet: {
    maxHeight: "78%",
    backgroundColor: COLORS.white,
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    paddingHorizontal: 18,
    paddingTop: 11,
    paddingBottom: 24,
  },
  sheetHandle: {
    width: 38,
    height: 4,
    borderRadius: 4,
    backgroundColor: "#CCD5DC",
    alignSelf: "center",
    marginBottom: 18,
  },
  sheetTitle: {
    color: COLORS.ink,
    fontSize: 18,
    fontWeight: "800",
    marginBottom: 12,
  },
  staffOption: {
    minHeight: 63,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 9,
    borderRadius: 12,
  },
  staffOptionSelected: { backgroundColor: COLORS.blueLight },
  staffAvatar: {
    width: 38,
    height: 38,
    borderRadius: 13,
    backgroundColor: "#EEF1F4",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 11,
  },
  staffAvatarText: { color: COLORS.ink, fontWeight: "800" },
  staffOptionCopy: { flex: 1 },
  staffName: { color: COLORS.ink, fontSize: 14, fontWeight: "700" },
  staffId: { color: COLORS.muted, fontSize: 12, marginTop: 3 },
  selectedCheck: { color: COLORS.blue, fontWeight: "800", fontSize: 18 },
  dateSheet: {
    backgroundColor: COLORS.white,
    borderTopLeftRadius: 22,
    borderTopRightRadius: 22,
    paddingTop: 11,
    paddingBottom: 28,
    paddingHorizontal: 18,
  },
  dateSheetActions: { flexDirection: "row", gap: 10, marginTop: 4 },
  cancelButton: {
    flex: 1,
    minHeight: 45,
    borderRadius: 11,
    borderWidth: 1,
    borderColor: COLORS.line,
    alignItems: "center",
    justifyContent: "center",
  },
  cancelButtonLabel: { color: COLORS.ink, fontSize: 13, fontWeight: "700" },
});
