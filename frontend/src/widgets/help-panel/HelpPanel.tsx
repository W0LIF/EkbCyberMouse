import { CircleHelp, Search, X } from "lucide-react";
import { Button } from "../../shared/ui/Button";
import type { ShortcutItem } from "../../shared/types/domain";

interface HelpPanelProps {
  close: () => void;
}

const shortcuts: ShortcutItem[] = [
  { key: "⌘ K", label: "Глобальный поиск" },
  { key: "R", label: "Обновить план" },
  { key: "Esc", label: "Закрыть панель" },
  { key: "G", label: "Карта маршрутов" },
  { key: "P", label: "План и загрузка" },
];

export function HelpPanel({ close }: HelpPanelProps) {
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
        <div className="help-search">
          <Search size={17} />
          <input placeholder="Найти ответ…" />
        </div>
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
          <p>Откройте документацию или создайте тикет в IT-поддержку.</p>
          <Button variant="secondary">Документация</Button>
        </div>
      </aside>
    </>
  );
}
