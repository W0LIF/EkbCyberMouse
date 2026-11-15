import { BarChart3, Info, Route } from "lucide-react";
import { Tooltip } from "./Tooltip";
import type { ApiPlan } from "../api";

const items = [
  ["В слот", "94%", "+2.1%", "spark"],
  ["В контрольный срок", "91%", "+1.4%", "spark"],
  ["Суммарный пробег", "428 км", "−18 км", "route"],
  ["Коэф. вариации", "0.12", "Оптимально", "bars"],
];

export function KPIs({ plan }: { plan: ApiPlan | null }) {
  const total = plan?.summary?.orders_total ?? 0;
  const assigned = plan?.summary?.visits_planned ?? 0;
  const unassigned = plan?.summary?.unassigned ?? plan?.unassigned.length ?? 0;
  const travelKm = Math.round((plan?.summary?.travel_sec_total ?? 0) / 60);
  const items = [
    ["Нарядов", total ? String(total) : "—", "в плане", "spark"],
    ["Распределено", total ? `${Math.round((assigned / total) * 100)}%` : "—", `${assigned} визитов`, "spark"],
    ["Не распределено", String(unassigned), "требуют внимания", "route"],
    ["Время в пути", `${travelKm} мин`, "по маршрутам", "bars"],
  ];

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
