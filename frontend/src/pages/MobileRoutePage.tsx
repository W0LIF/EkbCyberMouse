import { useState } from "react";
import { ChevronRight, ListTodo, LogOut, MapPin, Phone, Route, UserRound } from "lucide-react";
import { Logo } from "../shared/ui/Logo";
import { Status } from "../shared/ui/Status";
import { Button } from "../shared/ui/Button";

interface MobileRoutePageProps {
  logout: () => void;
}

export default function MobileRoutePage({ logout }: MobileRoutePageProps) {
  const [done, setDone] = useState(5);

  return (
    <div className="mobile-app">
      <header>
        <Logo />
        <button onClick={logout}>
          <LogOut size={19} />
        </button>
      </header>
      <main>
        <div className="mobile-greeting">
          <span>СУББОТА, 14 НОЯБРЯ</span>
          <h1>Мой маршрут</h1>
          <p>Доброе утро, Илья</p>
        </div>
        <div className="mobile-progress">
          <div>
            <b>
              {done} из 9 выполнено
            </b>
            <span>{Math.round((done / 9) * 100)}%</span>
          </div>
          <i>
            <span style={{ width: `${(done / 9) * 100}%` }} />
          </i>
          <small>До конца смены 4 ч 28 мин</small>
        </div>
        <div className="next-label">СЛЕДУЮЩИЙ ВИЗИТ</div>
        <article className="mobile-visit next">
          <div className="visit-time">
            <b>13:00</b>
            <span>– 15:00</span>
          </div>
          <div className="mobile-address">
            <Status>В работе</Status>
            <h2>ул. Малышева, 51</h2>
            <p>кв. 142 · Диагностика PON</p>
            <small>
              <MapPin size={13} /> 2.3 км · 8 минут
            </small>
          </div>
          <div className="call-alert">
            <Phone size={16} />
            <span>
              <b>Позвоните абоненту</b>
              <small>До начала слота 42 минуты</small>
            </span>
          </div>
          <div className="mobile-actions">
            <a href="tel:+70000000000">
              <Phone size={17} />
              Позвонить
            </a>
            <a href="https://yandex.ru/maps" target="_blank">
              <Route size={17} />
              Навигация
            </a>
          </div>
          <Button onClick={() => setDone(Math.min(9, done + 1))}>Прибыл на объект</Button>
        </article>
        <div className="next-label">ДАЛЕЕ ПО МАРШРУТУ</div>
        {[
          ["15:00", "ул. Белинского, 108", "Инсталляция"],
          ["17:00", "ул. Щорса, 39", "Диагностика 3ЛТП"],
        ].map((v, i) => (
          <article className="mobile-visit compact" key={v[1]}>
            <div className="visit-time">
              <b>{v[0]}</b>
              <span>– {i ? "19:00" : "17:00"}</span>
            </div>
            <div className="mobile-address">
              <h2>{v[1]}</h2>
              <p>{v[2]}</p>
            </div>
            <ChevronRight size={18} />
          </article>
        ))}
      </main>
      <nav>
        <button className="active">
          <Route size={20} />
          Маршрут
        </button>
        <button>
          <ListTodo size={20} />
          Наряды
        </button>
        <button>
          <UserRound size={20} />
          Профиль
        </button>
      </nav>
    </div>
  );
}
