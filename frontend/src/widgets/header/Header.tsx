import { Bell, CalendarDays, ChevronDown, ChevronRight, HelpCircle, Search } from "lucide-react";
import { useLocation } from "react-router-dom";
import { screenTitles } from "../../shared/config/nav";
import { Tooltip } from "../../shared/ui/Tooltip";

interface HeaderProps {
  onHelp: () => void;
}

export function Header({ onHelp }: HeaderProps) {
  const location = useLocation();
  const screenKey = location.pathname.replace("/", "") as keyof typeof screenTitles;
  const title = screenTitles[screenKey] || "Ростелеком Диспетчер";

  return (
    <header className="header">
      <div className="crumb">
        Главная <ChevronRight size={14} /> <b>{title}</b>
      </div>
      <div className="global-search">
        <Search size={18} />
        <input placeholder="Поиск по наряду, адресу, сотруднику…" />
        <kbd>Ctrl + K</kbd>
      </div>
      <div className="header-actions">
        <button className="date-button">
          <CalendarDays size={17} />
          <span>Сегодня, 14 ноября</span>
          <ChevronDown size={14} />
        </button>
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
