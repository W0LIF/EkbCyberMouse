const API_BASE = "/api/v1";

export interface ApiStop {
  seq: number;
  type: "DEPOT_START" | "VISIT" | "BREAK" | "RESTOCK" | "DEPOT_END";
  location_id: string;
  order_id?: string | null;
  arrival: string;
  start: string;
  end: string;
  travel_sec?: number | null;
  distance_m?: number | null;
  status?: "PLANNED" | "IN_PROGRESS" | "DONE";
  equipment_after?: { ONT: number; ROUTER: number; STB: number } | null;
  explanation?: string | null;
}

export interface ApiRoute {
  staff_id: string;
  team_staff_ids?: string[];
  service_center_id: string;
  status: "ACTIVE" | "UNAVAILABLE";
  stops: ApiStop[];
  totals?: { visits?: number; travel_sec?: number; distance_m?: number };
  unavailable_from?: string | null;
  unavailable_until?: string | null;
}

export interface ApiAlert {
  alert_id: string;
  type: "LATE_RISK" | "PGP_DETECTED" | "UNASSIGNED";
  status: "ACTIVE" | "RESOLVED";
  order_id?: string | null;
  group_id?: string | null;
  staff_id?: string | null;
  forecast_start?: string | null;
  lateness_min?: number | null;
  suggested_action: "REASSIGN" | "RESCHEDULE" | "TRANSFER_TO_STATION" | "NONE";
  message: string;
}

export interface ApiPgpGroup {
  group_id: string;
  access_node_id: string;
  order_ids: string[];
  detected_at: string;
  action: "TRANSFER_TO_STATION";
  comment?: string | null;
}

export interface ApiPlan {
  date: string;
  plan_version: number;
  as_of: string;
  based_on_event_id?: string | null;
  routes: ApiRoute[];
  unassigned: { order_id: string; reason_text: string }[];
  pgp_groups: ApiPgpGroup[];
  cancelled: { order_id: string }[];
  alerts: ApiAlert[];
  summary?: {
    orders_total?: number;
    visits_planned?: number;
    unassigned?: number;
    travel_sec_total?: number;
  } | null;
}

export interface ApiOrder {
  order_id: string;
  work_type_code: string;
  technology: string;
  building_id: string;
  address: string;
  lat: number;
  lon: number;
  building_type?: "MKD" | "PRIVATE";
  requires_height?: boolean;
  access_node_id?: string;
  registered_at?: string;
  latest_start?: string;
  deadline?: string;
  slot: { start: string; end: string };
  required_equipment: { ONT: number; ROUTER: number; STB: number };
  status: string;
  assigned_staff_id: string | null;
}

export interface ApiStaff {
  staff_id: string;
  display_name?: string | null;
  service_center_id: string;
  profiles: string[];
  technologies: string[];
  shift: {
    start: string;
    end: string;
    break_duration_min?: number;
    break_window?: { from: string; to: string };
  };
  height_permit: boolean;
  equipment_start?: { ONT: number; ROUTER: number; STB: number };
  equipment_capacity?: { ONT: number; ROUTER: number; STB: number };
}

export interface ApiServiceCenter {
  service_center_id: string;
  name: string;
  address: string;
  lat: number;
  lon: number;
  opening_hours?: { open: string; close: string };
  restock_duration_min?: number;
}

export interface ApiEventResult {
  event_id: string;
  accepted: boolean;
  duplicate: boolean;
  plan_version: number;
  as_of: string;
  processing_ms?: number | null;
  message?: string | null;
}

export interface ApiDemoDayResult {
  status: "ready";
  date: string;
  generated: boolean;
  counts: { orders: number };
}

export interface ApiScenarioMetrics {
  orders_total: number;
  visits_planned: number;
  unassigned: number;
  in_slot_percent: number;
  travel_km: number;
  restock_stops: number;
  risk_orders: number;
}

export interface ApiScenarioResult {
  date: string;
  removed_staff_ids: string[];
  baseline: ApiScenarioMetrics;
  scenario: ApiScenarioMetrics;
  unassigned_order_ids: string[];
}

export interface ApiTimeTickEvent {
  event_id: string;
  type: "TIME_TICK";
  timestamp: string;
}

export interface ApiNewOrder {
  order_id: string;
  work_type_code: string;
  technology: string;
  building_id: string;
  address: string;
  lat: number;
  lon: number;
  building_type: "MKD" | "PRIVATE";
  requires_height: boolean;
  access_node_id: string;
  registered_at: string;
  slot: { start: string; end: string };
  latest_start: string;
  deadline: string;
  required_equipment: { ONT: number; ROUTER: number; STB: number };
  is_repeat: boolean;
  previous_order_id?: string | null;
}

export interface ApiNewOrderEvent {
  event_id: string;
  type: "NEW_ORDER";
  timestamp: string;
  order: ApiNewOrder;
}

export type ApiEvent = ApiTimeTickEvent | ApiNewOrderEvent;

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let message = `Ошибка API (${response.status})`;
    try {
      const body = await response.json();
      message =
        body.error?.message ?? body.detail ?? body.message ?? message;
    } catch {
      // Keep the HTTP status message when the server does not return JSON.
    }
    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<T>;
}

export const dispatchApi = {
  getPlan: (date: string) =>
    request<ApiPlan>(`/days/${encodeURIComponent(date)}/plan`),
  getOrders: (date: string) =>
    request<ApiOrder[]>(`/days/${encodeURIComponent(date)}/orders`),
  prepareDemoDay: (date: string) =>
    request<ApiDemoDayResult>(`/demo/days/${encodeURIComponent(date)}`, {
      method: "POST",
    }),
  getStaff: () => request<ApiStaff[]>("/reference/staff"),
  getServiceCenters: () =>
    request<ApiServiceCenter[]>("/reference/service-centers"),
  buildPlan: (date: string, timeLimitSec = 30) =>
    request<ApiPlan>(`/days/${encodeURIComponent(date)}/plan`, {
      method: "POST",
      body: JSON.stringify({ time_limit_sec: timeLimitSec }),
    }),
  analyzeScenario: (
    date: string,
    input: {
      staff_reduction: number;
      extra_equipment_capacity: { ONT: number; ROUTER: number; STB: number };
      time_limit_sec?: number;
    },
  ) =>
    request<ApiScenarioResult>(
      `/days/${encodeURIComponent(date)}/scenarios`,
      {
        method: "POST",
        body: JSON.stringify(input),
      },
    ),
  postEvent: (date: string, event: ApiEvent) =>
    request<ApiEventResult>(`/days/${encodeURIComponent(date)}/events`, {
      method: "POST",
      body: JSON.stringify(event),
    }),
};
