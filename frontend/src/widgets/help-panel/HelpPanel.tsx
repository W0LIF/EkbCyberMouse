import { CircleHelp, Search, X } from "lucide-react";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../../shared/ui/Button";
import type { ShortcutItem } from "../../shared/types/domain";

interface HelpPanelProps {
  close: () => void;
  startTour: () => void;
}

const shortcuts: ShortcutItem[] = [
  { key: "Ctrl + K", label: "Глобальный поиск" },
  { key: "Esc", label: "Закрыть панель" },
  { key: "G", label: "Карта маршрутов" },
  { key: "P", label: "План и загрузка" },
];

export function HelpPanel({ close, startTour }: HelpPanelProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  function searchHelp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    close();
    const term = query.trim();
    navigate(term ? `/help?q=${encodeURIComponent(term)}` : "/help");
  }

  return (
    <>
      <div className="overlay" onClick={close} />
      <aside className="help-panel">
        <div className="drawer-head">
          <div>
            <span>СПРАВОЧНЫЙ ЦЕНТР</span>
            <h2>Помощь</h2>
          </div>
          <button onClick={close}>
            <X size={20} />
          </button>
        </div>
        <form className="help-search" onSubmit={searchHelp}>
          <Search size={17} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Найти ответ…"
            aria-label="Поиск по справке"
          />
          <button type="submit" aria-label="Найти ответ">
            <Search size={16} />
          </button>
        </form>
        <h3>Горячие клавиши</h3>
        {shortcuts.map((x) => (
          <div className="shortcut" key={x.key}>
            <kbd>{x.key}</kbd>
            <span>{x.label}</span>
          </div>
        ))}
        <div className="help-box">
          <CircleHelp size={22} />
          <b>Не нашли ответ?</b>
          <p>В справке собраны инструкции и ответы по работе с диспетчерской.</p>
          <Button
            variant="secondary"
            onClick={() => {
              close();
              navigate("/help");
            }}
          >
            Документация
          </Button>
          <Button variant="ghost" onClick={startTour}>
            Показать обзор
          </Button>
        </div>
      </aside>
    </>
  );
}
