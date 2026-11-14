/* ===== Domain Types — Rostelecom Dispatcher ===== */

export type Screen =
  | "map"
  | "plan"
  | "orders"
  | "risks"
  | "pgp"
  | "people"
  | "centers"
  | "settings"
  | "help"
  | "library";

export type ModalType = "order" | "explain" | "scenario" | "reassign" | null;

export type NavTone = "red" | "yellow" | "purple" | null;

/* --- Employee --- */
export interface Employee {
  name: string;
  initials: string;
  center: string;
  shift: string;
  visits: string;
  load: number;
  color: string;
  tableNumber: number;
  profile: "3ЛТП" | "Инсталляция";
  technologies: string[];
  online: boolean;
}

/* --- Order --- */
export interface Order {
  id: string;
  type: string;
  address: string;
  slot: string;
  person: string;
  center: string;
  status:
    | "В работе"
    | "Запланирован"
    | "Риск"
    | "Не распределён"
    | "ПГП"
    | "Выполнен"
    | "Отменён";
}

/* --- Risk --- */
export interface RiskItem {
  id: string;
  address: string;
  slot: string;
  person: string;
  description: string;
}

/* --- Pgp Group --- */
export interface PgpGroup {
  nodeId: string;
  description: string;
  address: string;
  district: string;
  orders: PgpOrder[];
}

export interface PgpOrder {
  id: string;
  address: string;
  registration: string;
}

/* --- Center --- */
export interface Center {
  name: string;
  address: string;
  employees: string;
  ordersToday: string;
  inSlotPct: string;
  color: string;
  stockItems: { name: string; count: number }[];
  stockNote: string;
}

/* --- Nav Item --- */
export interface NavItem {
  id: Screen;
  label: string;
  icon: string;
  badge?: string;
  tone?: NavTone;
}

/* --- FAQ --- */
export interface FaqItem {
  question: string;
  answer: string;
}

/* --- Help Category --- */
export interface HelpCategory {
  icon: string;
  title: string;
  count: string;
}

/* --- Kpi Item --- */
export interface KpiItem {
  name: string;
  value: string;
  delta: string;
  kind: "spark" | "route" | "bars";
}

/* --- Staff Mini Kpi --- */
export interface StaffMiniKpi {
  count: string;
  label: string;
  icon: string;
  tone: "green" | "purple" | "blue" | "yellow";
}

/* --- Setting Row --- */
export interface SettingRow {
  title: string;
  description: string;
}

/* --- Shortcut --- */
export interface ShortcutItem {
  key: string;
  label: string;
}

/* --- Candidate --- */
export interface Candidate {
  name: string;
  initials: string;
  center: string;
  distance: number;
  technologies: string[];
}

/* --- Tour Step --- */
export interface TourStep {
  title: string;
  description: string;
}

/* --- Mobile Visit --- */
export interface MobileVisit {
  time: string;
  address: string;
  workType: string;
  isNext?: boolean;
}
