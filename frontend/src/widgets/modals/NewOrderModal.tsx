import { useMemo, useState, type FormEvent } from "react";
import { X } from "lucide-react";
import { useDispatchData } from "../../features/dispatch/DispatchDataContext";
import { useToast } from "../../features/toast/ToastProvider";
import { dispatchApi, type ApiNewOrder } from "../../shared/api";
import { Button } from "../../shared/ui/Button";

interface NewOrderModalProps {
  close: () => void;
}

export function NewOrderModal({ close }: NewOrderModalProps) {
  const { date, plan, orders, refresh } = useDispatchData();
  const { toast } = useToast();
  const defaultTemplate = orders.find(
    (order) => plan && Date.parse(order.slot.start) > Date.parse(plan.as_of),
  ) ?? orders[0];
  const [templateId, setTemplateId] = useState(defaultTemplate?.order_id ?? "");
  const [slotStart, setSlotStart] = useState(defaultTemplate?.slot.start.slice(11, 16) ?? "");
  const [slotEnd, setSlotEnd] = useState(defaultTemplate?.slot.end.slice(11, 16) ?? "");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const template = orders.find((order) => order.order_id === templateId);

  const orderId = useMemo(() => {
    const prefix = `ORD-${date.replace(/-/g, "")}-`;
    const usedSequences = new Set(orders.flatMap((order) => {
      if (!order.order_id.startsWith(prefix)) return [];
      const sequence = Number(order.order_id.slice(prefix.length));
      return Number.isInteger(sequence) ? [sequence] : [];
    }));
    for (let sequence = 1; sequence <= 9999; sequence += 1) {
      if (!usedSequences.has(sequence)) {
        return `${prefix}${String(sequence).padStart(4, "0")}`;
      }
    }
    return null;
  }, [date, orders]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!template || !plan || !orderId) {
      setError("Недостаточно данных для создания наряда.");
      return;
    }
    if (!template.building_type || !template.access_node_id) {
      setError("В справочных данных выбранного объекта отсутствуют обязательные поля.");
      return;
    }
    const timestamp = new Date(Date.parse(plan.as_of) + 1000).toISOString();
    const slotStartAt = new Date(`${date}T${slotStart}:00+05:00`);
    const slotEndAt = new Date(`${date}T${slotEnd}:00+05:00`);
    if (
      Number.isNaN(slotStartAt.getTime()) ||
      Number.isNaN(slotEndAt.getTime()) ||
      slotEndAt <= slotStartAt ||
      slotStartAt.getTime() < Date.parse(timestamp)
    ) {
      setError("Укажите корректный слот после времени плана.");
      return;
    }

    const order: ApiNewOrder = {
      order_id: orderId,
      work_type_code: template.work_type_code,
      technology: template.technology,
      building_id: template.building_id,
      address: template.address,
      lat: template.lat,
      lon: template.lon,
      building_type: template.building_type,
      requires_height: template.requires_height ?? false,
      access_node_id: template.access_node_id,
      registered_at: timestamp,
      slot: {
        start: `${date}T${slotStart}:00+05:00`,
        end: `${date}T${slotEnd}:00+05:00`,
      },
      latest_start: `${date}T${slotEnd}:00+05:00`,
      deadline: new Date(Date.parse(timestamp) + 24 * 60 * 60 * 1000).toISOString(),
      required_equipment: template.required_equipment,
      is_repeat: false,
      previous_order_id: null,
    };

    setSaving(true);
    setError(null);
    try {
      const result = await dispatchApi.postEvent(date, {
        event_id: `EV-UI-${crypto.randomUUID()}`,
        type: "NEW_ORDER",
        timestamp,
        order,
      });
      if (!result.accepted) throw new Error(result.message ?? "API не принял новый наряд.");
      const refreshed = await refresh();
      if (!refreshed) {
        toast(`Наряд ${orderId} создан, но данные интерфейса не удалось обновить`);
      } else {
        toast(`Наряд ${orderId} создан и добавлен в план`);
      }
      close();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось создать наряд");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div className="overlay" onClick={close} />
      <aside className="drawer">
        <div className="drawer-head">
          <div>
            <span>НОВЫЙ НАРЯД</span>
            <h2>{orderId ?? "Лимит ID исчерпан"}</h2>
          </div>
          <button onClick={close} aria-label="Закрыть">
            <X size={21} />
          </button>
        </div>
        {error && <div className="card" role="alert">{error}</div>}
        <form
          className="drawer-section new-order-form"
          onSubmit={(event) => void submit(event)}
        >
          <label>
            Объект и шаблон работ
            <select
              value={templateId}
              onChange={(event) => {
                const nextTemplate = orders.find(
                  (order) => order.order_id === event.target.value,
                );
                setTemplateId(event.target.value);
                if (nextTemplate) {
                  setSlotStart(nextTemplate.slot.start.slice(11, 16));
                  setSlotEnd(nextTemplate.slot.end.slice(11, 16));
                }
              }}
              required
            >
              {orders.map((order) => (
                <option key={order.order_id} value={order.order_id}>
                  {order.address} · {order.work_type_code}
                </option>
              ))}
            </select>
          </label>
          {template && (
            <p>{template.technology} · {template.building_id}</p>
          )}
          <label>
            Начало слота
            <input
              type="time"
              value={slotStart}
              onChange={(event) => setSlotStart(event.target.value)}
              required
            />
          </label>
          <label>
            Конец слота
            <input
              type="time"
              value={slotEnd}
              onChange={(event) => setSlotEnd(event.target.value)}
              required
            />
          </label>
          <small>Новый наряд будет создан на основе выбранного объекта и типа работ.</small>
          <div className="drawer-actions">
            <Button variant="secondary" onClick={close}>Отмена</Button>
            <Button type="submit" disabled={saving || !template || !orderId}>
              {saving ? "Создаём…" : "Создать и перестроить"}
            </Button>
          </div>
        </form>
      </aside>
    </>
  );
}
