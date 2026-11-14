import type { PgpGroup } from "../types/domain";

export const pgpGroups: PgpGroup[] = [
  {
    nodeId: "AN0042",
    description: "4 обращения за 2 часа",
    address: "ул. Малышева, 128",
    district: "Кировский",
    orders: [
      { id: "ORD00184", address: "ул. Малышева, 128", registration: "11:12" },
      { id: "ORD00185", address: "ул. Первомайская, 39", registration: "11:21" },
      { id: "ORD00186", address: "ул. Первомайская, 47", registration: "11:30" },
      { id: "ORD00187", address: "ул. Первомайская, 55", registration: "11:39" },
    ],
  },
  {
    nodeId: "AN0178",
    description: "3 обращения за 47 минут",
    address: "ул. Щорса, 54",
    district: "Чкаловский",
    orders: [
      { id: "ORD00191", address: "ул. Щорса, 54", registration: "10:58" },
      { id: "ORD00192", address: "ул. Первомайская, 47", registration: "11:07" },
      { id: "ORD00193", address: "ул. Первомайская, 55", registration: "11:16" },
    ],
  },
];
