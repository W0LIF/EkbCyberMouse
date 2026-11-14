import type { RiskItem } from "../types/domain";

export const risks: RiskItem[] = [
  {
    id: "ORD00144",
    address: "ул. Татищева, 90",
    slot: "14:00–16:00",
    person: "Волкова М. С.",
    description: "Плановое прибытие 16:05 — позже слота на 5 мин",
  },
  {
    id: "ORD00158",
    address: "ул. Академическая, 24",
    slot: "15:00–17:00",
    person: "Смирнова А. В.",
    description: "Задержка на предыдущем объекте +30 мин",
  },
  {
    id: "ORD00163",
    address: "ул. Белинского, 108",
    slot: "16:00–18:00",
    person: "Петров А. Н.",
    description: "Пробка на маршруте увеличила путь на 24 мин",
  },
];

export const looseOrders: RiskItem[] = [
  {
    id: "ORD00145",
    address: "ул. Щорса, 39",
    slot: "",
    person: "",
    description: "Нет сотрудника с допуском к работам на высоте",
  },
  {
    id: "ORD00161",
    address: "ул. Бакинских комиссаров, 58",
    slot: "",
    person: "",
    description: "Не хватает времени смены",
  },
  {
    id: "ORD00170",
    address: "ул. Крауля, 63",
    slot: "",
    person: "",
    description: "Нет АО в рюкзаке",
  },
  {
    id: "ORD00174",
    address: "ул. Сулимова, 42",
    slot: "",
    person: "",
    description: "Нет сотрудника с технологией DOCSIS",
  },
];
