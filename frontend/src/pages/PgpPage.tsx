import { Gauge, Zap } from "lucide-react";
import { pgpGroups } from "../shared/mock/pgp";
import { Button } from "../shared/ui/Button";
import { Status } from "../shared/ui/Status";
import { Tooltip } from "../shared/ui/Tooltip";
import { PageIntro } from "../shared/ui/PageIntro";
import { useToast } from "../features/toast/ToastProvider";

export default function PgpPage() {
  const { toast } = useToast();

  return (
    <div className="screen">
      <PageIntro
        eyebrow="3 ГРУППОВЫХ СОБЫТИЯ"
        eyebrowTone="purple"
        title="Проактивные групповые повреждения"
        subtitle="Обращения, объединённые по сетевому узлу"
        actions={
          <Button variant="secondary">
            <Gauge size={17} /> Правила выявления
          </Button>
        }
      />
      <div className="pgp-grid">
        {pgpGroups.map((g) => (
          <article className="pgp-card card" key={g.nodeId}>
            <div className="pgp-accent" />
            <div className="pgp-info">
              <div className="pgp-title">
                <span>
                  <Zap size={18} />
                </span>
                <div>
                  <h2>Узел {g.nodeId}</h2>
                  <p>{g.description}</p>
                </div>
                <Status>ПГП</Status>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Адрес</th>
                    <th>Регистрация</th>
                  </tr>
                </thead>
                <tbody>
                  {g.orders.map((o) => (
                    <tr key={o.id}>
                      <td>
                        <code>{o.id}</code>
                      </td>
                      <td>{o.address}</td>
                      <td>{o.registration}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <Tooltip text="Наряды будут сняты с выездных бригад и переданы в профильное подразделение без выполнения работ на месте">
                <Button
                  variant="purple"
                  onClick={() => toast(`Группа ${g.nodeId} передана в станционное подразделение`)}
                >
                  Передать в станционное подразделение
                </Button>
              </Tooltip>
            </div>
            <div className="mini-map">
              <div className="mini-roads" />
              <span className="radius" />
              <span className="node">
                <Zap size={16} />
              </span>
              <b>{g.district} район</b>
              <small>Радиус влияния 500 м</small>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
