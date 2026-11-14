import { AlertCircle, AlertTriangle, Clock3, Info, RefreshCw } from "lucide-react";
import type { ModalType } from "../shared/types/domain";
import { risks, looseOrders } from "../shared/mock/risks";
import { Button } from "../shared/ui/Button";
import { Tooltip } from "../shared/ui/Tooltip";
import { PageIntro } from "../shared/ui/PageIntro";

interface RisksPageProps {
  setModal: (m: ModalType) => void;
}

export default function RisksPage({ setModal }: RisksPageProps) {
  return (
    <div className="screen">
      <PageIntro
        eyebrow="ТРЕБУЮТ ВНИМАНИЯ"
        eyebrowTone="warn"
        title="Риски и нераспределённые"
        subtitle="12 нераспределённых · 8 рисков"
        actions={
          <Button variant="secondary" icon={<RefreshCw size={16} />}>
            Пересчитать план
          </Button>
        }
      />
      <div className="two-cols">
        <section className="card issue-column">
          <div className="column-title">
            <span className="risk-icon">
              <Clock3 size={19} />
            </span>
            <div>
              <h2>Риски опоздания</h2>
              <p>8 нарядов могут выйти за слот</p>
            </div>
            <b>8</b>
          </div>
          {risks.map((x) => (
            <article className="issue risk" key={x.id}>
              <div className="issue-top">
                <code>{x.id}</code>
                <span>{x.slot}</span>
              </div>
              <h3>{x.address}</h3>
              <small>{x.person}</small>
              <p>
                <AlertTriangle size={15} />
                {x.description}
              </p>
              <div>
                <Tooltip text="Система подберёт ближайшего подходящего сотрудника">
                  <Button onClick={() => setModal("reassign")}>Передать другому</Button>
                </Tooltip>
                <Tooltip text="Перенос доступен не позднее, чем за 30 минут до слота">
                  <Button variant="secondary">Перенести</Button>
                </Tooltip>
              </div>
            </article>
          ))}
        </section>
        <section className="card issue-column">
          <div className="column-title">
            <span className="loose-icon">
              <AlertCircle size={19} />
            </span>
            <div>
              <h2>Нераспределённые</h2>
              <p>Нужна помощь диспетчера</p>
            </div>
            <b>12</b>
          </div>
          {looseOrders.map((x) => (
            <article className="issue loose" key={x.id}>
              <div className="issue-top">
                <code>{x.id}</code>
                <span>Сегодня</span>
              </div>
              <h3>{x.address}</h3>
              <p>
                <Info size={15} />
                {x.description}
              </p>
              <div>
                <Button onClick={() => setModal("reassign")}>Найти сотрудника</Button>
                <Button variant="secondary">На завтра</Button>
              </div>
            </article>
          ))}
        </section>
      </div>
    </div>
  );
}
