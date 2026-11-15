import { useMemo, useState } from "react";
import { Building2, Clock3, RefreshCw, Search, ToolCase, Users, Zap } from "lucide-react";
import { useDispatchData } from "../features/dispatch/DispatchDataContext";
import { Button } from "../shared/ui/Button";
import { Chips } from "../shared/ui/Chips";
import { PageIntro } from "../shared/ui/PageIntro";

const colors = ["#7C3AED", "#2563EB", "#FF6B00", "#DC2626", "#0891B2", "#16A34A"];

function minutesBetween(start: string, end: string) {
  const [startHour, startMinute] = start.split(":").map(Number);
  const [endHour, endMinute] = end.split(":").map(Number);
  return Math.max(0, endHour * 60 + endMinute - startHour * 60 - startMinute);
}

export default function PeoplePage() {
  const [profile, setProfile] = useState("Все");
  const [query, setQuery] = useState("");
  const { staff, centers, plan, loading, error, refresh } = useDispatchData();
  const centerById = useMemo(
    () => new Map(centers.map((center) => [center.service_center_id, center])),
    [centers],
  );
  const routeByStaffId = useMemo(
    () => new Map((plan?.routes ?? []).map((route) => [route.staff_id, route])),
    [plan],
  );
  const onLine = staff.filter(
    (person) => routeByStaffId.get(person.staff_id)?.status === "ACTIVE",
  ).length;
  const installationCount = staff.filter((person) => person.profiles.includes("INSTALL")).length;
  const ltpCount = staff.filter((person) => person.profiles.includes("LTP3")).length;
  const visibleStaff = useMemo(() => {
    const term = query.trim().toLocaleLowerCase("ru");
    return staff.filter((person) => {
      const route = routeByStaffId.get(person.staff_id);
      const matchesProfile =
        profile === "Все" ||
        (profile === "3ЛТП" && person.profiles.includes("LTP3")) ||
        (profile === "Инсталляция" && person.profiles.includes("INSTALL")) ||
        (profile === "Допуск к высоте" && person.height_permit) ||
        (profile === "Не на линии" && route?.status !== "ACTIVE");
      const matchesQuery =
        !term ||
        `${person.display_name ?? ""} ${person.staff_id} ${person.service_center_id}`
          .toLocaleLowerCase("ru")
          .includes(term);
      return matchesProfile && matchesQuery;
    });
  }, [staff, profile, query, routeByStaffId]);

  return (
    <div className="screen">
      <PageIntro
        eyebrow={`${onLine} НА ЛИНИИ ИЗ ${staff.length}`}
        title="Сотрудники"
        subtitle="Справочник API, квалификации и загрузка из текущего плана"
        actions={
          <Button
            variant="secondary"
            icon={<RefreshCw size={16} />}
            disabled={loading}
            onClick={() => void refresh()}
          >
            Обновить
          </Button>
        }
      />
      {error && <div className="card" role="alert">{error}</div>}
      {loading && <div className="card" role="status">Загружаем сотрудников…</div>}
      <div className="mini-kpis">
        <div className="card">
          <span className="stat-icon green"><Users size={18} /></span>
          <div><b>{onLine}</b><small>На линии по плану</small></div>
        </div>
        <div className="card">
          <span className="stat-icon purple"><ToolCase size={18} /></span>
          <div><b>{ltpCount}</b><small>Профиль 3ЛТП</small></div>
        </div>
        <div className="card">
          <span className="stat-icon blue"><Zap size={18} /></span>
          <div><b>{installationCount}</b><small>Инсталляторы</small></div>
        </div>
        <div className="card">
          <span className="stat-icon yellow"><Clock3 size={18} /></span>
          <div><b>{staff.length - onLine}</b><small>Без активного маршрута</small></div>
        </div>
      </div>
      <div className="directory-toolbar card">
        <div className="search-small">
          <Search size={16} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="ФИО или табельный номер…"
          />
        </div>
        <Chips
          items={["Все", "3ЛТП", "Инсталляция", "Допуск к высоте", "Не на линии"]}
          selected={profile}
          onSelect={setProfile}
        />
      </div>
      <div className="staff-grid">
        {visibleStaff.map((person, index) => {
          const route = routeByStaffId.get(person.staff_id);
          const visits = route?.stops.filter((stop) => stop.type === "VISIT").length ?? 0;
          const workMinutes = route?.stops.reduce((total, stop) => {
            const duration = minutesBetween(stop.start.slice(11, 16), stop.end.slice(11, 16));
            return total + (stop.type === "VISIT" ? duration : 0) + (stop.travel_sec ?? 0) / 60;
          }, 0) ?? 0;
          const shiftMinutes = minutesBetween(person.shift.start, person.shift.end);
          const load = shiftMinutes ? Math.min(100, Math.round((workMinutes / shiftMinutes) * 100)) : 0;
          const color = colors[index % colors.length];
          return (
            <article className="staff-card card" key={person.staff_id}>
              <div className="staff-card-head">
                <span className="avatar large" style={{ background: `${color}18`, color }}>
                  {(person.display_name ?? person.staff_id).slice(0, 2)}
                </span>
                <div>
                  <h2>{person.display_name ?? person.staff_id}</h2>
                  <p>{person.staff_id}</p>
                </div>
              </div>
              <div className="staff-tags">
                {person.profiles.map((item) => <span key={item}>{item === "LTP3" ? "3ЛТП" : item}</span>)}
                {person.technologies.map((technology) => <span key={technology}>{technology}</span>)}
                {person.height_permit && <span>Допуск к высоте</span>}
              </div>
              <div className="staff-meta">
                <p>
                  <Building2 size={14} />
                  {centerById.get(person.service_center_id)?.name ?? person.service_center_id}
                </p>
                <p><Clock3 size={14} />{person.shift.start}–{person.shift.end}</p>
              </div>
              <div className="staff-load">
                <span><b>Загрузка по маршруту</b><small>{load}%</small></span>
                <i><span style={{ width: `${load}%`, background: color }} /></i>
              </div>
              <div className="staff-footer">
                <span className={route?.status === "ACTIVE" ? "online-state" : "offline-state"}>
                  <i /> {route?.status === "ACTIVE" ? "На линии" : "Нет активного маршрута"}
                </span>
                <b>{visits} визитов</b>
              </div>
            </article>
          );
        })}
        {!loading && visibleStaff.length === 0 && (
          <div className="card">Сотрудники по заданным условиям не найдены.</div>
        )}
      </div>
    </div>
  );
}
