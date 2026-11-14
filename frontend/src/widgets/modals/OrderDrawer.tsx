import { MapPin, Package, Phone, Sparkles, X } from "lucide-react";
import type { ModalType } from "../../shared/types/domain";
import { Button } from "../../shared/ui/Button";
import { Status } from "../../shared/ui/Status";

interface OrderDrawerProps {
  close: () => void;
  setModal: (m: ModalType) => void;
}

export function OrderDrawer({ close, setModal }: OrderDrawerProps) {
  return (
    <>
      <div className="overlay" onClick={close} />
      <aside className="drawer">
        <div className="drawer-head">
          <div>
            <span>ДЕТАЛИ НАРЯДА</span>
            <h2>ORD00142</h2>
          </div>
          <button onClick={close}>
            <X size={21} />
          </button>
        </div>
        <Status>В работе</Status>
        <div className="drawer-section">
          <h3>Клиент</h3>
          <p>
            <MapPin size={16} />
            <span>
              <b>ул. Малышева, 51, кв. 142</b>
              <small>Екатеринбург, Ленинский район</small>
            </span>
          </p>
          <p>
            <Phone size={16} />
            <b>+7 (•••) •••-42-18</b>
          </p>
        </div>
        <div className="drawer-grid">
          <div>
            <span>Тип работ</span>
            <b>Диагностика 3ЛТП</b>
          </div>
          <div>
            <span>Технология</span>
            <b>PON</b>
          </div>
          <div>
            <span>Слот</span>
            <b>12:00–14:00</b>
          </div>
          <div>
            <span>Норматив</span>
            <b>45 минут</b>
          </div>
        </div>
        <div className="drawer-section">
          <h3>Оборудование</h3>
          <div className="equipment">
            <Package size={17} />
            <span>ONT ×2</span>
            <span>Роутер ×1</span>
          </div>
        </div>
        <div className="assignment">
          <div>
            <span className="avatar">ИИ</span>
            <span>
              <small>Назначен</small>
              <b>Иванов Илья Игоревич</b>
            </span>
          </div>
          <Button variant="secondary" onClick={() => setModal("explain")} icon={<Sparkles size={15} />}>
            Почему он?
          </Button>
        </div>
        <div className="drawer-section history">
          <h3>История</h3>
          {[
            ["11:34", "Сотрудник прибыл на объект"],
            ["10:58", "Наряд принят в работу"],
            ["09:02", "Назначен Иванову И. И."],
            ["08:47", "Наряд создан"],
          ].map((x, i) => (
            <div key={x[0]}>
              <i className={i === 0 ? "current" : ""} />
              <time>{x[0]}</time>
              <span>{x[1]}</span>
            </div>
          ))}
        </div>
        <div className="drawer-actions">
          <Button variant="secondary">Перенести</Button>
          <Button onClick={() => setModal("reassign")}>Переназначить</Button>
        </div>
      </aside>
    </>
  );
}
