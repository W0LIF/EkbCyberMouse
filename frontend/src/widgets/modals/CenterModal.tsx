import { useState } from "react";
import { AlertTriangle, Check, CheckCircle2, Sparkles, X } from "lucide-react";
import type { ModalType } from "../../shared/types/domain";
import { employees } from "../../shared/mock/employees";
import { Button } from "../../shared/ui/Button";
import { Chips } from "../../shared/ui/Chips";

interface CenterModalProps {
  type: Exclude<ModalType, "order" | null>;
  close: () => void;
  setModal: (m: ModalType) => void;
}

export function CenterModal({ type, close, setModal }: CenterModalProps) {
  const [staff, setStaff] = useState(3);

  if (type === "scenario")
    return (
      <>
        <div className="overlay" onClick={close} />
        <div className="modal scenario">
          <div className="modal-head">
            <div>
              <span>СЦЕНАРНЫЙ АНАЛИЗ</span>
              <h2>Что если −{staff} сотрудника?</h2>
            </div>
            <button onClick={close}>
              <X size={20} />
            </button>
          </div>
          <p>Посмотрите, как изменение числа сотрудников повлияет на план до его публикации.</p>
          <div className="slider-label">
            <span>Сотрудников на линии</span>
            <b>{40 - staff} из 40</b>
          </div>
          <input
            className="slider"
            type="range"
            min="0"
            max="10"
            value={staff}
            onChange={(e) => setStaff(+e.target.value)}
          />
          <div className="scenario-kpis">
            <div>
              <span>В слот</span>
              <b>{94 - staff * 2}%</b>
              <small>−{staff * 2}.0%</small>
            </div>
            <div>
              <span>Пробег</span>
              <b>{428 + staff * 18} км</b>
              <small>+{staff * 18} км</small>
            </div>
            <div>
              <span>Наряды с риском</span>
              <b>{8 + staff * 3}</b>
              <small>+{staff * 3}</small>
            </div>
          </div>
          <div className="impact">
            <AlertTriangle size={18} />
            <span>
              <b>Высокое влияние на план</b>
              <small>{staff + 4} нарядов потребуют переноса на следующий день</small>
            </span>
          </div>
          <div className="modal-actions">
            <Button variant="secondary" onClick={close}>
              Закрыть
            </Button>
            <Button>Сохранить сценарий</Button>
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

  /* explain */
  return (
    <>
      <div className="overlay" onClick={close} />
      <div className="modal explain">
        <div className="modal-head">
          <div>
            <span>ОБЪЯСНИМОСТЬ НАЗНАЧЕНИЯ</span>
            <h2>Почему наряд ORD00142 назначен Иванову И. И.</h2>
          </div>
          <button onClick={close}>
            <X size={20} />
          </button>
        </div>
        <p>Алгоритм сравнил 18 доступных сотрудников по 12 параметрам.</p>
        <div className="match-score">
          <span>
            <Sparkles size={20} />
          </span>
          <div>
            <b>Совпадение 96%</b>
            <small>Лучший кандидат на момент назначения</small>
          </div>
        </div>
        <div className="reasons">
          {[
            "Профиль: 3ЛТП",
            "Технология: PON",
            "Ближайший к адресу (2.3 км от предыдущей точки)",
            "Окно в слоте: 47 минут свободно",
            "В рюкзаке: ONT ×2, роутер ×1",
          ].map((x) => (
            <div key={x}>
              <CheckCircle2 size={19} />
              <span>{x}</span>
            </div>
          ))}
          <div className="warning">
            <AlertTriangle size={19} />
            <span>Не нужен допуск к высоте</span>
          </div>
        </div>
        <div className="modal-actions">
          <Button variant="secondary" onClick={() => setModal("reassign")}>
            Выбрать другого
          </Button>
          <Button onClick={close}>Понятно</Button>
        </div>
      </div>
    </>
  );
}
