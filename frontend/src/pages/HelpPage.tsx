import { useMemo, useState, type FormEvent } from "react";
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
import { useSearchParams } from "react-router-dom";
import { Button } from "../shared/ui/Button";

const categories = [
  { id: "map", title: "Карта и маршруты", Icon: Map },
  { id: "planning", title: "Планирование", Icon: BarChart3 },
  { id: "orders", title: "Работа с нарядами", Icon: ListTodo },
  { id: "mobile", title: "Мобильное приложение", Icon: Smartphone },
] as const;

type HelpCategory = (typeof categories)[number]["id"];

const articles: {
  question: string;
  answer: string;
  category: HelpCategory;
}[] = [
  {
    question: "Как посмотреть маршруты сотрудников?",
    answer:
      "Откройте «Карту маршрутов». Выберите сотрудника в списке справа, чтобы выделить его маршрут. Нажмите на точку наряда или сервисного центра, чтобы увидеть подробности.",
    category: "map",
  },
  {
    question: "Как пересчитать план?",
    answer:
      "На странице карты или плана нажмите «Пересчитать план». Backend заново рассчитает маршруты для выбранной даты; начатые и выполненные остановки сохраняются согласно статусам плана.",
    category: "planning",
  },
  {
    question: "Что показывает сценарный анализ?",
    answer:
      "Он сравнивает текущий план с вариантом при сокращении числа сотрудников и/или увеличении запаса оборудования. Результат сценария не публикуется и не изменяет текущий план.",
    category: "planning",
  },
  {
    question: "Почему наряд не распределён?",
    answer:
      "Откройте раздел «Нераспределённые»: рядом с нарядом указана причина. В карточке наряда можно проверить слот, тип работ и другие переданные данные.",
    category: "orders",
  },
  {
    question: "Как создать новый наряд?",
    answer:
      "На карте нажмите кнопку создания наряда, выберите существующий наряд как шаблон и задайте слот. После отправки backend попробует включить новый наряд в план; если подходящего маршрута нет, он останется нераспределённым.",
    category: "orders",
  },
  {
    question: "Как пользоваться приложением сотрудника?",
    answer:
      "В отдельном приложении выберите сотрудника и дату, откройте маршрут и отмечайте звонок абоненту, прибытие и завершение визита. Завершение доступно после отметки прибытия.",
    category: "mobile",
  },
];

export default function HelpPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(() => searchParams.get("q") ?? "");
  const [selectedCategory, setSelectedCategory] =
    useState<HelpCategory | null>(null);
  const [openQuestion, setOpenQuestion] = useState<string | null>(null);
  const term = query.trim().toLocaleLowerCase("ru");
  const visibleArticles = useMemo(
    () =>
      articles.filter((article) => {
        const matchesCategory =
          selectedCategory === null || article.category === selectedCategory;
        const matchesSearch =
          !term ||
          `${article.question} ${article.answer}`
            .toLocaleLowerCase("ru")
            .includes(term);
        return matchesCategory && matchesSearch;
      }),
    [selectedCategory, term],
  );

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = query.trim();
    setSearchParams(value ? { q: value } : {});
    setSelectedCategory(null);
    setOpenQuestion(null);
  }

  function selectCategory(category: HelpCategory) {
    setSelectedCategory((current) => (current === category ? null : category));
    setOpenQuestion(null);
    document
      .getElementById("help-articles")
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function showArticles() {
    document
      .getElementById("help-articles")
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <div className="screen">
      <div className="help-hero">
        <div className="eyebrow">СПРАВОЧНЫЙ ЦЕНТР</div>
        <h1>Чем можем помочь?</h1>
        <p>Инструкции по работе с планом, нарядами и мобильным приложением</p>
        <form className="help-hero-search" onSubmit={submitSearch}>
          <Search size={19} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Введите вопрос или название функции…"
            aria-label="Поиск по инструкциям"
          />
          <button type="submit">Найти</button>
        </form>
      </div>
      <div className="help-categories">
        {categories.map(({ id, title, Icon }) => {
          const count = articles.filter((article) => article.category === id).length;
          return (
            <button
              className={`help-category card${selectedCategory === id ? " active" : ""}`}
              key={id}
              aria-pressed={selectedCategory === id}
              onClick={() => selectCategory(id)}
            >
              <span>
                <Icon size={21} />
              </span>
              <b>{title}</b>
              <small>{count} {count === 1 ? "инструкция" : "инструкции"}</small>
              <ChevronRight size={16} />
            </button>
          );
        })}
      </div>
      <div className="help-content-grid">
        <section className="card faq" id="help-articles">
          <h2>
            {selectedCategory
              ? categories.find((item) => item.id === selectedCategory)?.title
              : "Частые вопросы"}
          </h2>
          {visibleArticles.map((article) => (
            <button
              key={article.question}
              aria-expanded={openQuestion === article.question}
              onClick={() =>
                setOpenQuestion((current) =>
                  current === article.question ? null : article.question,
                )
              }
            >
              <span>
                <b>{article.question}</b>
                {openQuestion === article.question && <p>{article.answer}</p>}
              </span>
              <ChevronDown
                className={openQuestion === article.question ? "rotated" : ""}
                size={17}
              />
            </button>
          ))}
          {visibleArticles.length === 0 && (
            <p className="help-no-results">
              По запросу «{query}» ничего не найдено. Попробуйте изменить запрос.
            </p>
          )}
        </section>
        <aside className="support-card card">
          <span>
            <CircleHelp size={27} />
          </span>
          <h2>Нужна помощь специалиста?</h2>
          <p>
            Создание обращений в IT Service Desk пока не подключено. По вопросам
            доступа обратитесь к администратору сервисного центра.
          </p>
          <Button onClick={showArticles}>Открыть инструкции</Button>
          <div className="support-unavailable">
            <i />
            IT Service Desk не подключён
          </div>
        </aside>
      </div>
    </div>
  );
}
