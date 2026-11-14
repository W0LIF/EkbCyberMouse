import type { Center } from "../types/domain";

export const centers: Center[] = [
  {
    name: "СЦ Северный",
    address: "ул. Бакинских комиссаров, 95",
    employees: "12 сотрудников",
    ordersToday: "31 наряд",
    inSlotPct: "94%",
    color: "#7C3AED",
    stockItems: [
      { name: "ONT", count: 18 },
      { name: "Роутеры", count: 12 },
      { name: "Кабель", count: 74 },
    ],
    stockNote: "Достаточно на 2–3 дня",
  },
  {
    name: "СЦ Центральный",
    address: "ул. Луначарского, 134",
    employees: "11 сотрудников",
    ordersToday: "28 нарядов",
    inSlotPct: "96%",
    color: "#2563EB",
    stockItems: [
      { name: "ONT", count: 16 },
      { name: "Роутеры", count: 11 },
      { name: "Кабель", count: 66 },
    ],
    stockNote: "Достаточно на 2–3 дня",
  },
  {
    name: "СЦ Южный",
    address: "ул. Щорса, 7",
    employees: "9 сотрудников",
    ordersToday: "24 наряда",
    inSlotPct: "91%",
    color: "#7C3AED",
    stockItems: [
      { name: "ONT", count: 14 },
      { name: "Роутеры", count: 10 },
      { name: "Кабель", count: 58 },
    ],
    stockNote: "Достаточно на 2–3 дня",
  },
  {
    name: "СЦ Западный",
    address: "ул. Крауля, 9А",
    employees: "8 сотрудников",
    ordersToday: "23 наряда",
    inSlotPct: "89%",
    color: "#FF6B00",
    stockItems: [
      { name: "ONT", count: 12 },
      { name: "Роутеры", count: 9 },
      { name: "Кабель", count: 50 },
    ],
    stockNote: "Требует пополнения",
  },
  {
    name: "СЦ Восточный",
    address: "ул. Сыромолотова, 14",
    employees: "8 сотрудников",
    ordersToday: "21 наряд",
    inSlotPct: "93%",
    color: "#DC2626",
    stockItems: [
      { name: "ONT", count: 10 },
      { name: "Роутеры", count: 8 },
      { name: "Кабель", count: 42 },
    ],
    stockNote: "Достаточно на 2–3 дня",
  },
];
