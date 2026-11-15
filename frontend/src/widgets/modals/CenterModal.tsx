import { useState } from "react";
import { AlertTriangle, Check, Sparkles, X } from "lucide-react";
import type { ModalType } from "../../shared/types/domain";
import { employees } from "../../shared/mock/employees";
import { dispatchApi, type ApiScenarioResult } from "../../shared/api";
import { useDispatchData } from "../../features/dispatch/DispatchDataContext";
import { Button } from "../../shared/ui/Button";
import { Chips } from "../../shared/ui/Chips";

interface CenterModalProps {
  type: Exclude<ModalType, "order" | null>;
  orderId: string | null;
  close: () => void;
}

export function CenterModal({ type, orderId, close }: CenterModalProps) {
  const { date, staff: staffMembers, plan, orders } = useDispatchData();
  const [staffReduction, setStaffReduction] = useState(3);
  const maxStaffReduction = Math.max(0, staffMembers.length - 1);
  const selectedStaffReduction = Math.min(staffReduction, maxStaffReduction);
  const [extraEquipment, setExtraEquipment] = useState({
    ONT: 0,
    ROUTER: 0,
    STB: 0,
  });
  const [scenario, setScenario] = useState<ApiScenarioResult | null>(null);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [scenarioError, setScenarioError] = useState<string | null>(null);

  async function analyzeScenario() {
    setScenarioLoading(true);
    setScenarioError(null);
    try {
      setScenario(
        await dispatchApi.analyzeScenario(date, {
          staff_reduction: selectedStaffReduction,
          extra_equipment_capacity: extraEquipment,
        }),
      );
    } catch (cause) {
      setScenarioError(
        cause instanceof Error ? cause.message : "Не удалось рассчитать сценарий",
      );
      setScenario(null);
    } finally {
      setScenarioLoading(false);
    }
  }

  if (type === "scenario")
    return (
      <>
        <div className="overlay" onClick={close} />
        <div className="modal scenario">
          <div className="modal-head">
            <div>
              <span>СЦЕНАРНЫЙ АНАЛИЗ</span>
              <h2>Вариант изменения ресурсов</h2>
            </div>
            <button onClick={close}>
              <X size={20} />
            </button>
          </div>
          <p>Сравните новый расчёт с текущим планом. Сценарий не меняет опубликованные данные.</p>
          <div className="slider-label">
            <span>Исключить сотрудников</span>
            <b>{selectedStaffReduction} из {staffMembers.length}</b>
          </div>
          <input
            className="slider"
            type="range"
            min="0"
            max={maxStaffReduction}
            value={selectedStaffReduction}
            onChange={(e) => {
              setStaffReduction(+e.target.value);
              setScenario(null);
            }}
          />
          <div className="scenario-stock-inputs">
            {(["ONT", "ROUTER", "STB"] as const).map((equipment) => (
              <label key={equipment}>
                Доп. {equipment}
                <input
                  type="number"
                  min="0"
                  value={extraEquipment[equipment]}
                  onChange={(event) => {
                    setExtraEquipment({
                      ...extraEquipment,
                      [equipment]: Math.max(0, Number(event.target.value)),
                    });
                    setScenario(null);
                  }}
                />
              </label>
            ))}
          </div>
          {scenarioError && <p className="scenario-error" role="alert">{scenarioError}</p>}
          {scenario ? (
            <div className="scenario-kpis">
              <div>
                <span>В слот</span>
                <b>{scenario.scenario.in_slot_percent}%</b>
                <small>Было {scenario.baseline.in_slot_percent}%</small>
              </div>
              <div>
                <span>Пробег</span>
                <b>{scenario.scenario.travel_km} км</b>
                <small>Было {scenario.baseline.travel_km} км</small>
              </div>
              <div>
                <span>Наряды с риском</span>
                <b>{scenario.scenario.risk_orders}</b>
                <small>Было {scenario.baseline.risk_orders}</small>
              </div>
              <div>
                <span>Не распределено</span>
                <b>{scenario.scenario.unassigned}</b>
                <small>Было {scenario.baseline.unassigned}</small>
              </div>
            </div>
          ) : (
            <div className="impact">
              <AlertTriangle size={18} />
              <span>
                <b>Расчёт будет выполнен на сервере</b>
                <small>Текущий план не изменится</small>
              </span>
            </div>
          )}
          {scenario?.unassigned_order_ids.length ? (
            <p className="scenario-unassigned">
              Не распределены: {scenario.unassigned_order_ids.join(", ")}
            </p>
          ) : null}
          <div className="modal-actions">
            <Button variant="secondary" onClick={close}>
              Закрыть
            </Button>
            <Button
              onClick={() => void analyzeScenario()}
              disabled={scenarioLoading || staffMembers.length === 0}
            >
              {scenarioLoading ? "Рассчитываем…" : "Рассчитать сценарий"}
            </Button>
          </div>
        </div>
      </>
    );

  if (type === "reassign")
    return (
      <>
        <div className="overlay" onClick={close} />
        <div className="modal reassign">
          <div className="modal-head">
            <div>
              <span>ПЕРЕНАЗНАЧЕНИЕ</span>
              <h2>Подходящие сотрудники</h2>
            </div>
            <button onClick={close}>
              <X size={20} />
            </button>
          </div>
          <Chips items={["Все", "PON", "Допуск к высоте", "Ближе 5 км"]} selected="Все" />
          {employees.slice(1, 4).map((e, i) => (
            <div className="candidate" key={e.name}>
              <span className="avatar">{e.initials}</span>
              <div>
                <b>{e.name}</b>
                <small>
                  {e.center} · {2 + i * 1.4} км
                </small>
                <p>
                  <span>
                    <Check size={11} />
                    PON
                  </span>
                  <span>
                    <Check size={11} />
                    Есть окно
                  </span>
                  <span>
                    <Check size={11} />
                    АО в наличии
                  </span>
                </p>
              </div>
              <Button onClick={close}>Выбрать</Button>
            </div>
          ))}
        </div>
      </>
    );

  const order = orders.find((item) => item.order_id === orderId);
  const route = plan?.routes.find((item) =>
    item.stops.some((stop) => stop.type === "VISIT" && stop.order_id === orderId),
  );
  const visit = route?.stops.find(
    (stop) => stop.type === "VISIT" && stop.order_id === orderId,
  );
  const assignedStaff = route
    ? staffMembers.find((person) => person.staff_id === route.staff_id)
    : undefined;

  return (
    <>
      <div className="overlay" onClick={close} />
      <div className="modal explain">
        <div className="modal-head">
          <div>
            <span>ОБЪЯСНИМОСТЬ НАЗНАЧЕНИЯ</span>
            <h2>Почему назначен {order?.order_id ?? "наряд"}</h2>
          </div>
          <button onClick={close}>
            <X size={20} />
          </button>
        </div>
        <p>
          {route
            ? `Сотрудник: ${assignedStaff?.display_name ?? route.staff_id}.`
            : "Наряд не назначен в текущем плане."}
        </p>
        <div className="match-score">
          <span>
            <Sparkles size={20} />
          </span>
          <div>
            <b>{order?.address ?? "Нет данных о наряде"}</b>
            <small>Обоснование текущего назначения</small>
          </div>
        </div>
        <div className="reasons">
          {visit?.explanation ? (
            <p>{visit.explanation}</p>
          ) : (
            <p>Обоснование отсутствует: наряд не назначен или план был построен старой версией алгоритма.</p>
          )}
        </div>
        <div className="modal-actions">
          <Button onClick={close}>Понятно</Button>
        </div>
      </div>
    </>
  );
}
