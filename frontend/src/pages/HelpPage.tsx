import { useState } from "react";
import {
  BarChart3,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  ListTodo,
  Map,
  Search,
  Smartphone,
} from "lucide-react";
import { Button } from "../shared/ui/Button";

export default function HelpPage() {
  const [open, setOpen] = useState(0);
  const faq = [
    [
      "Как пересчитать план?",
      "Откройте карту или Gantt и нажмите «Обновить». Система сохранит ручные назначения.",
    ],
    [
      "Почему наряд не распределён?",
      "Откройте карточку наряда: система покажет недостающий допуск, технологию, время или АО.",
    ],
    [
      "Как передать группу ПГП?",
      "В разделе ПГП выберите группу и подтвердите передачу в станционное подразделение.",
    ],
    [
      "Как изменить границы смены?",
      "Откройте профиль сотрудника и измените график. Новый график учтётся при пересчёте.",
    ],
  ];

  return (
    <div className="screen">
      <div className="help-hero">
        <div className="eyebrow">СПРАВОЧНЫЙ ЦЕНТР</div>
        <h1>Чем можем помочь?</h1>
        <p>Инструкции по работе с планом, нарядами и мобильным приложением</p>
        <div className="help-hero-search">
          <Search size={19} />
          <input placeholder="Введите вопрос или название функции…" />
          <kbd>Ctrl + K</kbd>
        </div>
      </div>
      <div className="help-categories">
        {[
          [Map, "Карта и маршруты", "7 статей"],
          [BarChart3, "Планирование", "12 статей"],
          [ListTodo, "Работа с нарядами", "9 статей"],
          [Smartphone, "Мобильное приложение", "6 статей"],
        ].map(([Icon, title, count]) => {
          const CategoryIcon = Icon as typeof Map;
          return (
            <button className="help-category card" key={title as string}>
              <span>
                <CategoryIcon size={21} />
              </span>
              <b>{title as string}</b>
              <small>{count as string}</small>
              <ChevronRight size={16} />
            </button>
          );
        })}
      </div>
      <div className="help-content-grid">
        <section className="card faq">
          <h2>Частые вопросы</h2>
          {faq.map((item, index) => (
            <button key={item[0]} onClick={() => setOpen(open === index ? -1 : index)}>
              <span>
                <b>{item[0]}</b>
                {open === index && <p>{item[1]}</p>}
              </span>
              <ChevronDown className={open === index ? "rotated" : ""} size={17} />
            </button>
          ))}
        </section>
        <aside className="support-card card">
          <span>
            <CircleHelp size={27} />
          </span>
          <h2>Нужна помощь специалиста?</h2>
          <p>Создайте тикет. Среднее время ответа IT-поддержки — 12 минут.</p>
          <Button>Создать тикет</Button>
          <Button variant="secondary">Открыть документацию</Button>
          <div>
            <i />
            Поддержка работает круглосуточно
          </div>
        </aside>
      </div>
    </div>
  );
}
