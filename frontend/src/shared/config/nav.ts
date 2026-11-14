import type { NavItem, Screen } from "../types/domain";

export const navItems: NavItem[] = [
  { id: "map", label: "Карта маршрутов", icon: "Map" },
  { id: "plan", label: "План и загрузка", icon: "BarChart3" },
  { id: "orders", label: "Наряды", icon: "ListTodo" },
  { id: "risks", label: "Риски", icon: "TriangleAlert", badge: "8", tone: "red" },
  { id: "risks", label: "Нераспределённые", icon: "AlertCircle", badge: "12", tone: "yellow" },
  { id: "pgp", label: "ПГП", icon: "ToolCase", badge: "3", tone: "purple" },
  { id: "people", label: "Сотрудники", icon: "Users" },
  { id: "centers", label: "Сервисные центры", icon: "Building2" },
  { id: "settings", label: "Настройки", icon: "Settings" },
  { id: "help", label: "Помощь", icon: "CircleHelp" },
  { id: "library", label: "Компоненты", icon: "Layers3" },
];

export const screenTitles: Record<Screen, string> = {
  map: "Карта маршрутов",
  plan: "План и загрузка",
  orders: "Наряды",
  risks: "Риски и нераспределённые",
  pgp: "Проактивное групповое повреждение",
  people: "Сотрудники",
  centers: "Сервисные центры",
  settings: "Настройки",
  help: "Помощь",
  library: "Компоненты",
};
