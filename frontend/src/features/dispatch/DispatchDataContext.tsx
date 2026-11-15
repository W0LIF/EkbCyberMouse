import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  ApiError,
  dispatchApi,
  type ApiOrder,
  type ApiPlan,
  type ApiServiceCenter,
  type ApiStaff,
} from "../../shared/api";

const DISPATCH_DATE = "2026-11-14";

interface DispatchData {
  date: string;
  selectDate: (date: string) => void;
  plan: ApiPlan | null;
  orders: ApiOrder[];
  staff: ApiStaff[];
  centers: ApiServiceCenter[];
  loading: boolean;
  replanning: boolean;
  error: string | null;
  refresh: () => Promise<boolean>;
  rebuildPlan: () => Promise<void>;
}

const DispatchDataContext = createContext<DispatchData | null>(null);

export function DispatchDataProvider({ children }: { children: ReactNode }) {
  const [plan, setPlan] = useState<ApiPlan | null>(null);
  const [orders, setOrders] = useState<ApiOrder[]>([]);
  const [staff, setStaff] = useState<ApiStaff[]>([]);
  const [centers, setCenters] = useState<ApiServiceCenter[]>([]);
  const [loading, setLoading] = useState(true);
  const [replanning, setReplanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [date, setDate] = useState(DISPATCH_DATE);
  const lastLoadDate = useRef<string | null>(null);
  const loadSequence = useRef(0);

  const selectDate = useCallback((nextDate: string) => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(nextDate)) return;
    loadSequence.current += 1;
    setPlan(null);
    setOrders([]);
    setStaff([]);
    setCenters([]);
    setError(null);
    setDate(nextDate);
  }, []);

  const refresh = useCallback(async () => {
    const requestId = ++loadSequence.current;
    setLoading(true);
    setError(null);
    try {
      let nextOrders: ApiOrder[];
      try {
        nextOrders = await dispatchApi.getOrders(date);
      } catch (cause) {
        if (!(cause instanceof ApiError) || cause.status !== 404) throw cause;
        await dispatchApi.prepareDemoDay(date);
        nextOrders = await dispatchApi.getOrders(date);
      }

      const [nextStaff, nextCenters] = await Promise.all([
        dispatchApi.getStaff(),
        dispatchApi.getServiceCenters(),
      ]);

      let nextPlan: ApiPlan | null;
      try {
        nextPlan = await dispatchApi.getPlan(date);
      } catch (cause) {
        if (!(cause instanceof ApiError) || cause.status !== 404) throw cause;
        nextPlan = await dispatchApi.buildPlan(date);
      }

      if (loadSequence.current === requestId) {
        setOrders(nextOrders);
        setStaff(nextStaff);
        setCenters(nextCenters);
        setPlan(nextPlan);
      }
      return true;
    } catch (cause) {
      if (loadSequence.current === requestId) {
        setError(cause instanceof Error ? cause.message : "Не удалось загрузить данные");
      }
      return false;
    } finally {
      if (loadSequence.current === requestId) setLoading(false);
    }
  }, [date]);

  const rebuildPlan = useCallback(async () => {
    setReplanning(true);
    setError(null);
    try {
      const currentPlan = plan ?? await dispatchApi.getPlan(date);
      const nextPlan = currentPlan.based_on_event_id
        ? await (async () => {
            const timestamp = new Date(
              Date.parse(currentPlan.as_of) + 1000,
            ).toISOString();
            await dispatchApi.postEvent(date, {
              event_id: `EV-${crypto.randomUUID()}`,
              type: "TIME_TICK",
              timestamp,
            });
            return dispatchApi.getPlan(date);
          })()
        : await dispatchApi.buildPlan(date);
      setPlan(nextPlan);
      setOrders(await dispatchApi.getOrders(date));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось перестроить план");
    } finally {
      setReplanning(false);
    }
  }, [date, plan]);

  useEffect(() => {
    if (lastLoadDate.current === date) return;
    lastLoadDate.current = date;
    void refresh();
  }, [date, refresh]);

  return (
    <DispatchDataContext.Provider
      value={{
        date,
        selectDate,
        plan,
        orders,
        staff,
        centers,
        loading,
        replanning,
        error,
        refresh,
        rebuildPlan,
      }}
    >
      {children}
    </DispatchDataContext.Provider>
  );
}

export function useDispatchData() {
  const context = useContext(DispatchDataContext);
  if (!context) {
    throw new Error("useDispatchData must be used inside DispatchDataProvider");
  }
  return context;
}
