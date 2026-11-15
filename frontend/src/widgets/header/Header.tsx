import { Bell, CalendarDays, ChevronDown, ChevronRight, HelpCircle, Search } from "lucide-react";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { screenTitles } from "../../shared/config/nav";
import { Tooltip } from "../../shared/ui/Tooltip";
import { useDispatchData } from "../../features/dispatch/DispatchDataContext";

const MIN_PLAN_DATE = "1900-01-01";
const MAX_PLAN_DATE = "2100-12-31";

interface HeaderProps {
  onHelp: () => void;
}

export function Header({ onHelp }: HeaderProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { date, selectDate } = useDispatchData();
  const [query, setQuery] = useState("");
  const screenKey = location.pathname.replace("/", "") as keyof typeof screenTitles;
  const title = screenTitles[screenKey] || "Ростелеком Диспетчер";
  const dateLabel = new Date(`${date}T12:00:00Z`).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    timeZone: "UTC",
  });

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
        <Tooltip text="3 новых события">
          <button className="icon-button unread">
            <Bell size={19} />
          </button>
        </Tooltip>
        <Tooltip text="Помощь">
          <button className="icon-button" onClick={onHelp}>
            <HelpCircle size={19} />
          </button>
        </Tooltip>
      </div>
    </header>
  );
}
