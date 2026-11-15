import { useState } from "react";
import { AlertTriangle, Check, Sparkles, X } from "lucide-react";
import type { ModalType } from "../../shared/types/domain";
import { dispatchApi, type ApiScenarioResult } from "../../shared/api";
import { useDispatchData } from "../../features/dispatch/DispatchDataContext";
import { useToast } from "../../features/toast/ToastProvider";
import { Button } from "../../shared/ui/Button";

interface CenterModalProps {
  type: Exclude<ModalType, "order" | null>;
  orderId: string | null;
  close: () => void;
}

export function CenterModal({ type, orderId, close }: CenterModalProps) {
  const { date, staff: staffMembers, centers, plan, orders, refresh } =
    useDispatchData();
  const { toast } = useToast();
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
  const [assignmentError, setAssignmentError] = useState<string | null>(null);
  const [assigningStaffId, setAssigningStaffId] = useState<string | null>(null);
  const assignmentOrder = orders.find((order) => order.order_id === orderId);

  async function assignOrder(staffId: string) {
    if (!assignmentOrder || !plan) {
      setAssignmentError("Нет данных наряда или актуального плана.");
      return;
    }

    setAssigningStaffId(staffId);
    setAssignmentError(null);
    try {
      const result = await dispatchApi.postEvent(date, {
        event_id: `EV-UI-${crypto.randomUUID()}`,
        type: "ORDER_ASSIGNED",
        timestamp: new Date(Date.parse(plan.as_of) + 1000).toISOString(),
        order_id: assignmentOrder.order_id,
        staff_id: staffId,
      });
      if (!result.accepted) {
        throw new Error(result.message ?? "Сервер не принял назначение.");
      }

      const refreshed = await refresh();
      toast(
        refreshed
          ? `Наряд ${assignmentOrder.order_id} назначен сотруднику`
          : "Наряд назначен, но план не удалось обновить",
      );
      close();
    } catch (cause) {
      setAssignmentError(
        cause instanceof Error ? cause.message : "Не удалось назначить наряд",
      );
    } finally {
      setAssigningStaffId(null);
    }
  }

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
              <span>НАЗНАЧЕНИЕ НАРЯДА</span>
              <h2>{assignmentOrder?.order_id ?? "Наряд не выбран"}</h2>
            </div>
            <button onClick={close}>
              <X size={20} />
            </button>
          </div>
          {assignmentOrder && (
            <p>
              {assignmentOrder.address} · {assignmentOrder.technology} ·{" "}
              {assignmentOrder.slot.start.slice(11, 16)}–{assignmentOrder.slot.end.slice(11, 16)}
            </p>
          )}
          {assignmentError && (
            <p className="scenario-error" role="alert">{assignmentError}</p>
          )}
          {staffMembers.map((person) => {
            const center = centers.find(
              (item) => item.service_center_id === person.service_center_id,
            );
            const technologyMatches =
              person.technologies.includes(assignmentOrder?.technology ?? "");
            const heightMatches =
              !assignmentOrder?.requires_height || person.height_permit;

            return (
            <div className="candidate" key={person.staff_id}>
              <span className="avatar">
                {(person.display_name ?? person.staff_id).slice(0, 2)}
              </span>
              <div>
                <b>{person.display_name ?? person.staff_id}</b>
                <small>{center?.name ?? person.service_center_id} · {person.technologies.join(", ")}</small>
                <p>
                  <span>
                    {technologyMatches && <Check size={11} />}
                    {technologyMatches ? "Технология подходит" : "Технология не совпадает"}
                  </span>
                  <span>
                    {heightMatches && <Check size={11} />}
                    {heightMatches ? "Допуск по высоте подходит" : "Нет допуска к высоте"}
                  </span>
                </p>
              </div>
              <Button
                onClick={() => void assignOrder(person.staff_id)}
                disabled={
                  !assignmentOrder ||
                  !plan ||
                  assigningStaffId !== null ||
                  !technologyMatches ||
                  !heightMatches
                }
              >
                {assigningStaffId === person.staff_id ? "Назначаем…" : "Назначить"}
              </Button>
            </div>
            );
          })}
          {staffMembers.length === 0 && (
            <p className="empty-state">Список сотрудников не загружен.</p>
          )}
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
