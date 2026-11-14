import { ChevronDown, ChevronRight, SlidersHorizontal } from "lucide-react";
import type { ModalType } from "../shared/types/domain";
import { employees } from "../shared/mock/employees";
import { Button } from "../shared/ui/Button";
import { Tooltip } from "../shared/ui/Tooltip";
import { PageIntro } from "../shared/ui/PageIntro";
import { Chips } from "../shared/ui/Chips";
import { KPIs } from "../shared/ui/KPIs";

interface PlanPageProps {
  setModal: (m: ModalType) => void;
}

export default function PlanPage({ setModal }: PlanPageProps) {
  return (
    <div className="screen">
      <PageIntro
        eyebrow="ПЛАН НА 14 НОЯБРЯ"
        title="План и загрузка"
        subtitle="Распределение работ и контроль временных слотов"
        actions={
          <Button
            variant="secondary"
            icon={<SlidersHorizontal size={16} />}
            onClick={() => setModal("scenario")}
          >
            Сценарный анализ
          </Button>
        }
      />
      <KPIs />
      <div className="section-toolbar">
        <Chips items={["Все", "3ЛТП", "Инсталляция", "Высокий риск"]} />
        <span>Оптимизировано в 09:02</span>
      </div>
      <div className="gantt card">
        <div className="gantt-head">
          <div>Сотрудник / СЦ</div>
          {["08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21"].map(
            (h) => (
              <span key={h}>{h}:00</span>
            ),
          )}
        </div>
        <div className="group-row">
          <ChevronDown size={15} /> 3ЛТП <span>28 сотрудников</span>
        </div>
        {employees.slice(0, 4).map((e, i) => (
          <div className="gantt-row" key={e.name}>
            <div className="gantt-person">
              <span className="avatar">{e.initials}</span>
              <span>
                <b>{e.name}</b>
                <small>{e.center.replace("СЦ ", "")}</small>
              </span>
            </div>
            <div className="timeline">
              <div className="now-line" />
              <Tooltip text="ул. Малышева, 51 · Диагностика PON · 45 мин">
                <button
                  onClick={() => setModal("order")}
                  className="bar green"
                  style={{ left: `${7 + i * 2}%`, width: "12%" }}
                >
                  Малышева, 51
                </button>
              </Tooltip>
              <Tooltip text="Пополнение АО — 15 мин">
                <span className="bar blue" style={{ left: `${23 + i * 3}%`, width: "7%" }} />
              </Tooltip>
              <span className="bar gray" style={{ left: "38%", width: "8%" }}>
                Обед
              </span>
              <Tooltip
                text={i === 3 ? "Риск опоздания: задержка 22 мин" : "Запланированный визит"}
              >
                <button
                  onClick={() => setModal("order")}
                  className={`bar ${i === 3 ? "yellow" : "green"}`}
                  style={{ left: `${52 + i * 4}%`, width: "14%" }}
                >
                  {i === 3 ? "Риск +22" : "Визит"}
                </button>
              </Tooltip>
            </div>
          </div>
        ))}
        <div className="group-row">
          <ChevronRight size={15} /> Инсталляторы <span>12 сотрудников</span>
        </div>
      </div>
    </div>
  );
}
