import { useState } from "react";
import { Building2, Clock3, Filter, MoreHorizontal, Plus, Search, ToolCase, Users, Zap } from "lucide-react";
import { employees } from "../shared/mock/employees";
import { Button } from "../shared/ui/Button";
import { Chips } from "../shared/ui/Chips";
import { PageIntro } from "../shared/ui/PageIntro";

export default function PeoplePage() {
  const [profile, setProfile] = useState("Все");

  return (
    <div className="screen">
      <PageIntro
        eyebrow="40 НА ЛИНИИ ИЗ 52"
        title="Сотрудники"
        subtitle="Профили, допуски, смены и текущая загрузка бригад"
        actions={<Button icon={<Plus size={17} />}>Добавить сотрудника</Button>}
      />
      <div className="mini-kpis">
        <div className="card">
          <span className="stat-icon green">
            <Users size={18} />
          </span>
          <div>
            <b>40</b>
            <small>На линии</small>
          </div>
        </div>
        <div className="card">
          <span className="stat-icon purple">
            <ToolCase size={18} />
          </span>
          <div>
            <b>28</b>
            <small>Профиль 3ЛТП</small>
          </div>
        </div>
        <div className="card">
          <span className="stat-icon blue">
            <Zap size={18} />
          </span>
          <div>
            <b>12</b>
            <small>Инсталляторы</small>
          </div>
        </div>
        <div className="card">
          <span className="stat-icon yellow">
            <Clock3 size={18} />
          </span>
          <div>
            <b>4</b>
            <small>Скоро завершат смену</small>
          </div>
        </div>
      </div>
      <div className="directory-toolbar card">
        <div className="search-small">
          <Search size={16} />
          <input placeholder="ФИО или табельный номер…" />
        </div>
        <Chips
          items={["Все", "3ЛТП", "Инсталляция", "Допуск к высоте", "Не на линии"]}
          selected={profile}
          onSelect={setProfile}
        />
        <Button variant="secondary" icon={<Filter size={15} />}>
          Фильтры
        </Button>
      </div>
      <div className="staff-grid">
        {employees.map((person) => (
          <article className="staff-card card" key={person.name}>
            <div className="staff-card-head">
              <span
                className="avatar large"
                style={{ background: `${person.color}18`, color: person.color }}
              >
                {person.initials}
              </span>
              <div>
                <h2>{person.name}</h2>
                <p>Таб. № {person.tableNumber}</p>
              </div>
              <button>
                <MoreHorizontal size={18} />
              </button>
            </div>
            <div className="staff-tags">
              <span>{person.profile}</span>
              {person.technologies.map((t) => (
                <span key={t}>{t}</span>
              ))}
            </div>
            <div className="staff-meta">
              <p>
                <Building2 size={14} />
                {person.center}
              </p>
              <p>
                <Clock3 size={14} />
                {person.shift}
              </p>
            </div>
            <div className="staff-load">
              <span>
                <b>Загрузка</b>
                <small>{person.load}%</small>
              </span>
              <i>
                <span
                  style={{
                    width: `${person.load}%`,
                    background: person.load > 85 ? "#FFB800" : person.color,
                  }}
                />
              </i>
            </div>
            <div className="staff-footer">
              <span className={person.online ? "online-state" : "offline-state"}>
                <i /> {person.online ? "На линии" : "Не на смене"}
              </span>
              <b>{person.visits} визитов</b>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
