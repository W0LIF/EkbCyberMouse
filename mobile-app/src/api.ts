export type VisitAction = "CALL_CUSTOMER" | "ARRIVED" | "COMPLETED";
export type VisitStatus = "PLANNED" | "IN_PROGRESS" | "DONE";

export interface StaffMember {
  staff_id: string;
  display_name?: string | null;
}

export interface RouteVisit {
  orderId: string;
  address: string;
  status?: VisitStatus;
  arrival?: string;
  start?: string;
  end?: string;
  sequence: number;
  latitude?: number;
  longitude?: number;
}

interface ApiErrorBody {
  error?: { message?: string };
  detail?: string;
  message?: string;
}

interface RawVisit {
  type?: string;
  seq?: number;
  sequence?: number;
  order_id?: string | null;
  orderId?: string;
  status?: string | null;
  arrival?: string | null;
  start?: string | null;
  end?: string | null;
  time?: string | null;
  scheduled_at?: string | null;
  address?: string | null;
  location_id?: string | null;
  lat?: number | null;
  lon?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  order?: {
    order_id?: string;
    address?: string;
    lat?: number;
    lon?: number;
  } | null;
}

interface RawRouteResponse {
  visits?: RawVisit[];
  stops?: RawVisit[];
  route?: {
    visits?: RawVisit[];
    stops?: RawVisit[];
  };
}

const API_BASE_URL = (
  process.env.EXPO_PUBLIC_API_BASE_URL?.trim() ||
  "http://localhost:8080/api/v1"
).replace(/\/+$/, "");

async function request(path: string, init?: RequestInit): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
  } catch {
    throw new Error(
      `Не удалось связаться с сервером ${API_BASE_URL}. Проверьте адрес API и подключение к сети.`,
    );
  }

  if (!response.ok) {
    let message = `Ошибка API (${response.status})`;
    try {
      const body = (await response.json()) as ApiErrorBody;
      message = body.error?.message ?? body.detail ?? body.message ?? message;
    } catch {
      // The response may be empty or non-JSON; retain its HTTP status instead.
    }
    throw new Error(message);
  }
  return response;
}

export async function getStaff(signal?: AbortSignal): Promise<StaffMember[]> {
  const response = await request("/reference/staff", { signal });
  const data: unknown = await response.json();
  if (
    !Array.isArray(data) ||
    data.some(
      (staff) =>
        typeof staff !== "object" ||
        staff === null ||
        typeof (staff as StaffMember).staff_id !== "string",
    )
  ) {
    throw new Error("Сервер вернул некорректный список сотрудников.");
  }

  return data as StaffMember[];
}

function isVisitStatus(value: unknown): value is VisitStatus {
  return value === "PLANNED" || value === "IN_PROGRESS" || value === "DONE";
}

function firstString(...values: (string | null | undefined)[]): string | undefined {
  for (const value of values) {
    if (typeof value === "string" && value.trim().length > 0) return value;
  }
  return undefined;
}

function optionalNumber(...values: (number | null | undefined)[]): number | undefined {
  for (const value of values) {
    if (typeof value === "number" && Number.isFinite(value)) return value;
  }
  return undefined;
}

export function normalizeRoute(data: RawRouteResponse): RouteVisit[] {
  const candidates =
    data.visits ?? data.route?.visits ?? data.stops ?? data.route?.stops;
  if (!Array.isArray(candidates)) {
    throw new Error("Сервер вернул маршрут в неподдерживаемом формате.");
  }

  const visits = candidates
    .filter((visit) => !visit.type || visit.type === "VISIT")
    .map((visit, index): RouteVisit | null => {
      const orderId = firstString(visit.order_id, visit.orderId, visit.order?.order_id);
      if (!orderId) return null;

      const status = isVisitStatus(visit.status) ? visit.status : undefined;
      return {
        orderId,
        address: firstString(visit.address, visit.order?.address) ?? "Адрес не указан",
        status,
        arrival: firstString(visit.arrival, visit.time, visit.scheduled_at),
        start: firstString(visit.start),
        end: firstString(visit.end),
        sequence:
          typeof visit.seq === "number"
            ? visit.seq
            : typeof visit.sequence === "number"
              ? visit.sequence
              : index + 1,
        latitude: optionalNumber(visit.latitude, visit.lat, visit.order?.lat),
        longitude: optionalNumber(visit.longitude, visit.lon, visit.order?.lon),
      };
    })
    .filter((visit): visit is RouteVisit => visit !== null);

  if (candidates.length > 0 && visits.length === 0) {
    throw new Error("В ответе маршрута не найдены визиты с идентификаторами нарядов.");
  }

  return visits.sort((left, right) => left.sequence - right.sequence);
}

export async function getAssignedRoute(
  date: string,
  staffId: string,
  signal?: AbortSignal,
): Promise<RouteVisit[]> {
  const response = await request(
    `/mobile/days/${encodeURIComponent(date)}/routes/${encodeURIComponent(staffId)}`,
    { signal },
  );
  const data = (await response.json()) as RawRouteResponse;
  return normalizeRoute(data);
}

export async function submitVisitAction(
  date: string,
  staffId: string,
  orderId: string,
  action: VisitAction,
): Promise<void> {
  await request(
    `/mobile/days/${encodeURIComponent(date)}/routes/${encodeURIComponent(staffId)}/visits/${encodeURIComponent(orderId)}/actions`,
    {
      method: "POST",
      body: JSON.stringify({ action, occurred_at: new Date().toISOString() }),
    },
  );
}
