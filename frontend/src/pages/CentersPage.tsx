import { Building2, Info, MapPin, MoreHorizontal, Plus } from "lucide-react";
import { centers } from "../shared/mock/centers";
import { Button } from "../shared/ui/Button";
import { PageIntro } from "../shared/ui/PageIntro";

export default function CentersPage() {
  return (
    <div className="screen">
      <PageIntro
        eyebrow="5 СЕРВИСНЫХ ЦЕНТРОВ"
        title="Сервисные центры"
        subtitle="Зоны ответственности, сотрудники и остатки оборудования"
        actions={<Button icon={<Plus size={17} />}>Добавить центр</Button>}
      />
      <div className="centers-layout">
        <div className="centers-list">
          {centers.map((center) => (
            <article className="center-card card" key={center.name}>
              <div className="center-card-title">
                <span style={{ background: center.color }}>
                  <Building2 size={20} />
                </span>
                <div>
                  <h2>{center.name}</h2>
                  <p>
                    <MapPin size={12} /> {center.address}
                  </p>
                </div>
                <button>
                  <MoreHorizontal size={18} />
                </button>
              </div>
              <div className="center-metrics">
                <div>
                  <span>Сотрудники</span>
                  <b>{center.employees}</b>
                </div>
                <div>
                  <span>Наряды сегодня</span>
                  <b>{center.ordersToday}</b>
                </div>
                <div>
                  <span>В слот</span>
                  <b className="positive">{center.inSlotPct}</b>
                </div>
              </div>
              <div className="stock">
                <div>
                  <span>Остатки АО</span>
                  <small>{center.stockNote}</small>
                </div>
                {center.stockItems.map((stock) => (
                  <span key={stock.name}>
                    {stock.name} <b>{stock.count}</b>
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
        <div className="coverage-map card">
          <div className="coverage-roads" />
          <div className="coverage-head">
            <b>Зоны ответственности</b>
            <span>Екатеринбург</span>
          </div>
          {centers.map((center, index) => (
            <div
              className={`coverage-zone zone-${index + 1}`}
              key={center.name}
              style={{ borderColor: center.color, background: `${center.color}18` }}
            >
              <span style={{ background: center.color }}>
                <Building2 size={14} />
              </span>
              <b>{center.name.replace("СЦ ", "")}</b>
            </div>
          ))}
          <div className="coverage-legend">
            <Info size={14} />
            Границы рассчитаны по времени в пути
          </div>
        </div>
      </div>
    </div>
  );
}
