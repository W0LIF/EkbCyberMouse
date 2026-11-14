import { useState } from "react";
import {
  AlertTriangle,
  Building2,
  ChevronDown,
  ChevronRight,
  Clock3,
  Layers3,
  Plus,
  RefreshCw,
} from "lucide-react";
import type { ModalType } from "../shared/types/domain";
import { employees } from "../shared/mock/employees";
import { centers } from "../shared/mock/centers";
import { Button } from "../shared/ui/Button";
import { Tooltip } from "../shared/ui/Tooltip";
import { PageIntro } from "../shared/ui/PageIntro";
import { Chips } from "../shared/ui/Chips";
import { useToast } from "../features/toast/ToastProvider";

interface MapPageProps {
  setModal: (m: ModalType) => void;
}

export default function MapPage({ setModal }: MapPageProps) {
  const [active, setActive] = useState(0);
  const [filter, setFilter] = useState("Все");
  const [refreshing, setRefreshing] = useState(false);
  const { toast } = useToast();

  function refresh() {
    setRefreshing(true);
    setTimeout(() => {
      setRefreshing(false);
      toast("План обновлён: изменения не требуются");
    }, 800);
  }

  return (
    <div className="screen map-screen">
      <PageIntro
        eyebrow="ОПЕРАТИВНЫЙ КОНТРОЛЬ"
        title="Карта маршрутов"
        subtitle="40 сотрудников на линии · 127 визитов сегодня"
        live
      />
      <div className="map-layout">
        <div className="map-canvas">
          <div className="map-toolbar">
            <Button variant="secondary" icon={<Layers3 size={16} />}>
              Показать все
            </Button>
            <Button variant="ghost">Скрыть выполненные</Button>
            <Button variant="ghost" icon={<AlertTriangle size={15} />}>
              Только риски
            </Button>
            <span className="toolbar-divider" />
            <Button
              variant="ghost"
              onClick={refresh}
              icon={<RefreshCw className={refreshing ? "spin" : ""} size={16} />}
            >
              обновлено 3 сек назад
            </Button>
          </div>
          <div className="district d1">ВЕРХ-ИСЕТСКИЙ</div>
          <div className="district d2">ЖЕЛЕЗНОДОРОЖНЫЙ</div>
          <div className="district d3">КИРОВСКИЙ</div>
          <div className="district d4">ЛЕНИНСКИЙ</div>
          <div className="district d5">ОКТЯБРЬСКИЙ</div>
          <div className="district d6">ЧКАЛОВСКИЙ</div>
          <div className="district d7">ОРДЖОНИКИДЗЕВСКИЙ</div>
          <svg className="roads" viewBox="0 0 900 600" preserveAspectRatio="none">
            <g className="road-lines">
              <path d="M-20 160 C160 120 230 310 420 270 S700 100 920 160" />
              <path d="M80 -20 C130 180 310 160 330 620" />
              <path d="M520 -20 C460 160 640 260 590 620" />
              <path d="M-20 450 C200 390 360 510 920 410" />
              <path d="M210 -20 C250 90 190 210 50 340" />
            </g>
            <g className="routes">
              <path
                className={active === 0 ? "route active" : "route"}
                stroke={employees[0]?.color ?? "#7C3AED"}
                d="M105 130 C190 185 235 250 340 320 S420 410 520 360"
              />
              <path
                className={active === 1 ? "route active" : "route"}
                stroke={employees[1]?.color ?? "#2563EB"}
                d="M430 120 C490 190 450 270 570 300 S700 400 790 360"
              />
              <path
                className={active === 2 ? "route active" : "route"}
                stroke={employees[2]?.color ?? "#7C3AED"}
                d="M170 480 C240 400 350 450 420 360 S560 200 670 175"
              />
              <path
                className={active === 3 ? "route active" : "route"}
                stroke={employees[3]?.color ?? "#FF6B00"}
                d="M720 520 C680 430 590 420 570 300 S490 190 430 120"
              />
            </g>
          </svg>
          {[
            ["18%", "23%", "1", employees[0]?.color ?? "#7C3AED"],
            ["30%", "37%", "2", employees[0]?.color ?? "#7C3AED"],
            ["44%", "52%", "3", employees[0]?.color ?? "#7C3AED"],
            ["55%", "39%", "1", employees[1]?.color ?? "#2563EB"],
            ["67%", "49%", "2", employees[1]?.color ?? "#2563EB"],
            ["74%", "65%", "3", employees[1]?.color ?? "#2563EB"],
            ["27%", "76%", "1", employees[2]?.color ?? "#7C3AED"],
            ["42%", "64%", "2", employees[2]?.color ?? "#7C3AED"],
            ["70%", "25%", "3", employees[2]?.color ?? "#7C3AED"],
          ].map((p, i) => (
            <button
              key={i}
              className="visit"
              style={{ left: p[0], top: p[1], background: p[3] }}
              onClick={() => setModal("order")}
            >
              {p[2]}
            </button>
          ))}
          {centers.map((c, i) => (
            <div
              key={i}
              className="center-marker"
              style={{
                left: ["15%", "48%", "78%", "25%", "53%"][i],
                top: ["18%", "18%", "60%", "76%", "82%"][i],
              }}
            >
              <span>
                <Building2 size={15} />
              </span>
              <b>{c.name.replace("СЦ ", "")}</b>
            </div>
          ))}
          <div className="risk-marker" style={{ left: "62%", top: "37%" }}>
            <Clock3 size={15} />
          </div>
          <div className="pgp-marker" style={{ left: "38%", top: "58%" }}>
            <AlertTriangle size={15} />
          </div>
          <div className="map-zoom">
            <button>+</button>
            <button>−</button>
          </div>
          <Tooltip text="Создать наряд вручную">
            <button className="fab" onClick={() => setModal("order")}>
              <Plus size={24} />
            </button>
          </Tooltip>
        </div>
        <aside className="route-panel">
          <Chips
            items={["Все", "3ЛТП", "Инсталляция", "Высокий риск", "ПГП"]}
            selected={filter}
            onSelect={setFilter}
          />
          <div className="panel-heading">
            <b>Маршруты сотрудников</b>
            <span>40 на линии</span>
          </div>
          <div className="employee-list">
            {employees.map((e, i) => (
              <button
                className={`employee-card ${active === i ? "active" : ""}`}
                key={e.name}
                onClick={() => setActive(i)}
              >
                <span
                  className="avatar"
                  style={{ background: `${e.color}18`, color: e.color }}
                >
                  {e.initials}
                </span>
                <span className="employee-info">
                  <b>{e.name}</b>
                  <small>
                    {e.center} · {e.shift}
                  </small>
                  <span className="progress">
                    <i
                      style={{
                        width: `${e.load}%`,
                        background: e.load > 85 ? "#FFB800" : e.color,
                      }}
                    />
                  </span>
                </span>
                <span className="visits">
                  <b>{e.visits}</b>
                  <small>визитов</small>
                </span>
                <ChevronRight size={16} />
              </button>
            ))}
          </div>
          <details className="legend">
            <summary>
              Условные обозначения <ChevronDown size={15} />
            </summary>
            <div>
              <span>
                <i className="green-dot" />
                Сотрудник
              </span>
              <span>
                <i className="yellow-dot" />
                Риск
              </span>
              <span>
                <i className="purple-dot" />
                ПГП
              </span>
              <span>
                <i className="square-dot" />
                СЦ
              </span>
            </div>
          </details>
        </aside>
      </div>
    </div>
  );
}
