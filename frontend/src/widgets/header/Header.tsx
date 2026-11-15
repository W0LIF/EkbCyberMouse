import {
  AlertCircle,
  AlertTriangle,
  Bell,
  CalendarDays,
  ChevronDown,
  ChevronRight,
  HelpCircle,
  Search,
  ToolCase,
  X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { screenTitles } from "../../shared/config/nav";
import { useDispatchData } from "../../features/dispatch/DispatchDataContext";

const MIN_PLAN_DATE = "1900-01-01";
const MAX_PLAN_DATE = "2100-12-31";

interface HeaderProps {
  onHelp: () => void;
  onOpenOrder: (orderId: string) => void;
}

export function Header({ onHelp, onOpenOrder }: HeaderProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { date, selectDate, plan } = useDispatchData();
  const [query, setQuery] = useState("");
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const notificationsRef = useRef<HTMLDivElement | null>(null);
  const screenKey = location.pathname.replace("/", "") as keyof typeof screenTitles;
  const title = screenTitles[screenKey] || "Ростелеком Диспетчер";
  const notifications = useMemo(() => {
    const activeAlerts = (plan?.alerts ?? []).filter(
      (alert) => alert.status === "ACTIVE",
    );
    const alertOrderIds = new Set(
      activeAlerts
        .filter((alert) => alert.type === "UNASSIGNED" && alert.order_id)
        .map((alert) => alert.order_id),
    );
    return [
      ...activeAlerts.map((alert) => ({
        key: alert.alert_id,
        title:
          alert.type === "LATE_RISK"
            ? "Риск опоздания"
            : alert.type === "PGP_DETECTED"
              ? "Обнаружена группа ПГП"
              : "Нераспределённый наряд",
        message: alert.message,
        orderId: alert.order_id,
        path:
          alert.type === "PGP_DETECTED"
            ? "/pgp"
            : alert.type === "UNASSIGNED"
              ? "/unassigned"
              : "/risks",
        icon:
          alert.type === "LATE_RISK"
            ? AlertTriangle
            : alert.type === "PGP_DETECTED"
              ? ToolCase
              : AlertCircle,
      })),
      ...(plan?.unassigned ?? [])
        .filter((item) => !alertOrderIds.has(item.order_id))
        .map((item) => ({
          key: `unassigned-${item.order_id}`,
          title: "Нераспределённый наряд",
          message: `${item.order_id}: ${item.reason_text}`,
          orderId: item.order_id,
          path: "/unassigned",
          icon: AlertCircle,
        })),
    ];
  }, [plan]);
  const dateLabel = new Date(`${date}T12:00:00Z`).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    timeZone: "UTC",
  });

  useEffect(() => {
    if (!notificationsOpen) return;
    function handleOutsideClick(event: PointerEvent) {
      if (!notificationsRef.current?.contains(event.target as Node)) {
        setNotificationsOpen(false);
      }
    }
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setNotificationsOpen(false);
    }
    document.addEventListener("pointerdown", handleOutsideClick);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("pointerdown", handleOutsideClick);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [notificationsOpen]);

  return (
    <header className="header">
      <div className="crumb">
        Главная <ChevronRight size={14} /> <b>{title}</b>
      </div>
      <div className="global-search">
        <Search size={18} />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && query.trim()) {
              navigate(`/orders?q=${encodeURIComponent(query.trim())}`);
            }
          }}
          placeholder="Поиск по наряду, адресу, сотруднику…"
        />
        <kbd>Ctrl + K</kbd>
      </div>
      <div className="header-actions">
        <label className="date-button">
          <CalendarDays size={17} />
          <span>{dateLabel}</span>
          <ChevronDown size={14} />
          <input
            type="date"
            aria-label="Выбрать дату плана"
            min={MIN_PLAN_DATE}
            max={MAX_PLAN_DATE}
            value={date}
            onChange={(event) => {
              if (event.target.value) selectDate(event.target.value);
            }}
          />
        </label>
        <div className="notification-anchor" ref={notificationsRef}>
          <button
            className={`icon-button${notifications.length ? " unread" : ""}`}
            aria-label={`Уведомления: ${notifications.length}`}
            aria-expanded={notificationsOpen}
            aria-haspopup="dialog"
            onClick={() => setNotificationsOpen((open) => !open)}
          >
            <Bell size={19} />
          </button>
          {notificationsOpen && (
            <section
              className="notification-panel"
              role="dialog"
              aria-label="Уведомления плана"
            >
              <div className="notification-panel-head">
                <div>
                  <b>Уведомления</b>
                  <small>{notifications.length} требуют внимания</small>
                </div>
                <button
                  className="icon-button"
                  aria-label="Закрыть уведомления"
                  onClick={() => setNotificationsOpen(false)}
                >
                  <X size={16} />
                </button>
              </div>
              {notifications.length ? (
                <div className="notification-list">
                  {notifications.map((item) => {
                    const Icon = item.icon;
                    return (
                      <button
                        className="notification-item"
                        key={item.key}
                        onClick={() => {
                          setNotificationsOpen(false);
                          if (item.orderId) onOpenOrder(item.orderId);
                          else navigate(item.path);
                        }}
                      >
                        <Icon size={17} />
                        <span>
                          <b>{item.title}</b>
                          <small>{item.message}</small>
                        </span>
                        <ChevronRight size={15} />
                      </button>
                    );
                  })}
                </div>
              ) : (
                <p className="notification-empty">Активных уведомлений нет.</p>
              )}
              <button
                className="notification-footer"
                onClick={() => {
                  setNotificationsOpen(false);
                  navigate("/risks");
                }}
              >
                Открыть все риски
                <ChevronRight size={15} />
              </button>
            </section>
          )}
        </div>
        <button className="icon-button" onClick={onHelp} aria-label="Помощь">
          <HelpCircle size={19} />
        </button>
      </div>
    </header>
  );
}
