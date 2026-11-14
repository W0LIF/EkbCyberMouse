import { BarChart3, Info, Route } from "lucide-react";
import { Tooltip } from "./Tooltip";

const items = [
  ["В слот", "94%", "+2.1%", "spark"],
  ["В контрольный срок", "91%", "+1.4%", "spark"],
  ["Суммарный пробег", "428 км", "−18 км", "route"],
  ["Коэф. вариации", "0.12", "Оптимально", "bars"],
];

export function KPIs() {
  return (
    <div className="kpi-grid">
      {items.map(([name, value, delta, kind]) => (
        <div className="kpi-card" key={name}>
          <div>
            <span>
              {name}{" "}
              <Tooltip text="Доля визитов, начатых внутри 2-часового слота. Вес повторных обращений ×2.">
                <Info size={13} />
              </Tooltip>
            </span>
            <strong>{value}</strong>
            <small>{delta}</small>
          </div>
          {kind === "spark" ? (
            <svg viewBox="0 0 80 35">
              <path d="M2 29 C14 25,18 27,28 20 S42 25,52 14 S68 16,78 5" />
            </svg>
          ) : kind === "route" ? (
            <Route size={26} />
          ) : (
            <BarChart3 size={26} />
          )}
        </div>
      ))}
    </div>
  );
}
