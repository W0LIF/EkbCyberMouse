from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    NonNegativeInt,
    PlainSerializer,
    StringConstraints,
)

DateTime = Annotated[
    AwareDatetime,
    PlainSerializer(lambda v: v.isoformat(timespec="seconds"), return_type=str),
]

LocalTime = Annotated[
    str,
    StringConstraints(pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$"),
]

def _unique(v: list) -> list:
    if len(v) != len(set(v)):
        raise ValueError("элементы списка должны быть уникальны")
    return v

def UniqueList(inner_type):  # noqa: N802 (фабрика типов)
    return Annotated[list[inner_type], AfterValidator(_unique)]

Technology = Literal["PON", "FTTB", "XDSL", "DOCSIS"]
Profile = Literal["INSTALL", "LTP3"]
WorkTypeCode = Literal[
    "INST_PON_MKD",
    "INST_FTTB_MKD",
    "INST_PRIVATE_VLS",
    "ADD_SERVICE",
    "SURVEY_PRIVATE",
    "REPAIR",
    "DEGRADATION",
    "DISMANTLE",
]
BuildingType = Literal["MKD", "PRIVATE"]
NodeType = Literal["OLT", "SWITCH", "DSLAM", "CMTS"]
DeadlineKind = Literal["SLOT", "HOURS", "WORKING_DAYS"]
StopType = Literal["DEPOT_START", "VISIT", "BREAK", "RESTOCK", "DEPOT_END"]
StopStatus = Literal["PLANNED", "IN_PROGRESS", "DONE"]
RouteStatus = Literal["ACTIVE", "UNAVAILABLE"]
UnassignedReasonCode = Literal[
    "NO_QUALIFIED_STAFF",
    "NO_SHIFT_TIME",
    "SLOT_UNREACHABLE",
    "NO_EQUIPMENT",
    "STAFF_UNAVAILABLE",
    "OTHER",
]
SuggestedAction = Literal["RESCHEDULE", "REASSIGN", "ESCALATE"]
AlertType = Literal["LATE_RISK", "PGP_DETECTED", "UNASSIGNED"]
AlertStatus = Literal["ACTIVE", "RESOLVED"]
AlertSuggestedAction = Literal["REASSIGN", "RESCHEDULE", "TRANSFER_TO_STATION", "NONE"]
PgpAction = Literal["TRANSFER_TO_STATION"]
EventType = Literal[
    "NEW_ORDER",
    "ORDER_CANCELLED",
    "VISIT_DELAYED",
    "ORDER_TRANSFERRED",
    "STAFF_UNAVAILABLE",
    "TIME_TICK",
]
OrderFactOutcome = Literal[
    "COMPLETED",
    "TRANSFERRED_TO_STATION",
    "CANCELLED",
    "RESCHEDULED",
    "PGP_GROUPED",
]


class TimeWindow(BaseModel):
    model_config = ConfigDict(extra="ignore")
    start: DateTime
    end: DateTime


class Equipment(BaseModel):
    """Количество АО по видам. Все три поля обязательны (required в спеке)."""
    model_config = ConfigDict(extra="ignore")
    ONT: NonNegativeInt
    ROUTER: NonNegativeInt
    STB: NonNegativeInt


class OpeningHours(BaseModel):
    model_config = ConfigDict(extra="ignore")
    open: LocalTime
    close: LocalTime


class ServiceCenter(BaseModel):
    model_config = ConfigDict(extra="ignore")
    service_center_id: Annotated[str, StringConstraints(pattern=r"^SC-[0-9]{2}$")]
    name: str
    address: str
    lat: Annotated[float, Field(ge=-90, le=90)]
    lon: Annotated[float, Field(ge=-180, le=180)]
    opening_hours: OpeningHours
    restock_duration_min: NonNegativeInt


class BreakWindow(BaseModel):
    """`from` — зарезервированное слово в Python, используем алиас."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    from_: LocalTime = Field(alias="from")
    to: LocalTime


class Shift(BaseModel):
    model_config = ConfigDict(extra="ignore")
    start: LocalTime
    end: LocalTime
    break_duration_min: NonNegativeInt
    break_window: BreakWindow


class Staff(BaseModel):
    model_config = ConfigDict(extra="ignore")
    staff_id: Annotated[str, StringConstraints(pattern=r"^ST-[0-9]{3}$")]
    display_name: str | None = None
    service_center_id: str
    profiles: UniqueList(Profile) = Field(..., min_length=1)
    technologies: UniqueList(Technology) = Field(..., min_length=1)
    height_permit: bool
    shift: Shift
    equipment_start: Equipment
    equipment_capacity: Equipment
    experience_years: Annotated[float, Field(ge=0)] | None = None


class Building(BaseModel):
    model_config = ConfigDict(extra="ignore")
    building_id: Annotated[str, StringConstraints(pattern=r"^B-[0-9]{5}$")]
    address: str
    lat: Annotated[float, Field(ge=-90, le=90)]
    lon: Annotated[float, Field(ge=-180, le=180)]
    building_type: BuildingType
    overhead_line: bool
    zone_service_center_id: str | None = None


class AccessNode(BaseModel):
    model_config = ConfigDict(extra="ignore")
    access_node_id: Annotated[str, StringConstraints(pattern=r"^AN-[0-9]{4}$")]
    node_type: NodeType
    technology: Technology
    name: str
    address: str | None = None
    lat: Annotated[float, Field(ge=-90, le=90)]
    lon: Annotated[float, Field(ge=-180, le=180)]
    buildings: list[Building] = Field(..., min_length=1)


class WorkType(BaseModel):
    model_config = ConfigDict(extra="ignore")
    code: WorkTypeCode
    name: str
    profiles: UniqueList(Profile) = Field(..., min_length=1)
    duration_min: Annotated[int, Field(ge=1)]
    max_start_delay_min: Annotated[int, Field(ge=0)] | None
    deadline_kind: DeadlineKind
    deadline_value: Annotated[int, Field(ge=1)] | None
    repeat_deadline_value: Annotated[int, Field(ge=1)] | None
    pgp_relevant: bool


class ReferenceData(BaseModel):
    """Тело `PUT /api/v1/reference`."""
    model_config = ConfigDict(extra="ignore")
    service_centers: list[ServiceCenter] = Field(..., min_length=1)
    staff: list[Staff] = Field(..., min_length=1)
    access_nodes: list[AccessNode] = Field(..., min_length=1)
    work_types: list[WorkType] = Field(..., min_length=1)


class HourlyFactor(BaseModel):
    model_config = ConfigDict(extra="ignore")
    hour: Annotated[int, Field(ge=0, le=23)]
    factor: Annotated[float, Field(ge=0)]


class TravelMatrix(BaseModel):
    """Тело `PUT /api/v1/reference/travel-matrix`.

    durations_sec и distances_m — N×N, N = len(points).
    points: все service_center_id + все building_id из справочника.
    """
    model_config = ConfigDict(extra="ignore")
    matrix_id: str
    points: UniqueList(str) = Field(..., min_length=2)
    durations_sec: list[list[NonNegativeInt]]
    distances_m: list[list[NonNegativeInt]]
    hourly_factors: list[HourlyFactor] | None = None


class OrderFact(BaseModel):
    """Фактическое исполнение — только в обучающем наборе. Поле `fact` игнорируется сервисом."""
    model_config = ConfigDict(extra="ignore")
    outcome: OrderFactOutcome
    staff_id: str | None = None
    actual_start: DateTime | None = None
    actual_duration_min: NonNegativeInt | None = None
    pgp_incident_id: str | None = None


class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    order_id: Annotated[str, StringConstraints(pattern=r"^ORD-[0-9]{8}-[0-9]{4}$")]
    work_type_code: WorkTypeCode
    technology: Technology
    building_id: str
    address: str
    lat: Annotated[float, Field(ge=-90, le=90)]
    lon: Annotated[float, Field(ge=-180, le=180)]
    building_type: BuildingType
    requires_height: bool
    access_node_id: str
    registered_at: DateTime
    slot: TimeWindow
    latest_start: DateTime
    deadline: DateTime
    required_equipment: Equipment
    is_repeat: bool
    previous_order_id: str | None = None
    fact: OrderFact | None = None


class DayInput(BaseModel):
    """Тело `PUT /api/v1/days/{date}`."""
    model_config = ConfigDict(extra="ignore")
    date: Annotated[str, StringConstraints(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")]
    now: DateTime
    orders: list[Order]
    absent_staff_ids: UniqueList(str) = Field(default_factory=list)



class Stop(BaseModel):
    model_config = ConfigDict(extra="ignore")
    seq: Annotated[int, Field(ge=1)]
    type: StopType
    location_id: str
    order_id: str | None = None
    arrival: DateTime
    start: DateTime
    end: DateTime
    travel_sec: NonNegativeInt | None = None
    distance_m: NonNegativeInt | None = None
    status: StopStatus | None = None
    equipment_after: Equipment | None = None
    explanation: str | None = None


class RouteTotals(BaseModel):
    model_config = ConfigDict(extra="ignore")
    visits: NonNegativeInt | None = None
    travel_sec: NonNegativeInt | None = None
    distance_m: NonNegativeInt | None = None
    work_min: NonNegativeInt | None = None
    utilization: Annotated[float, Field(ge=0)] | None = None


class Route(BaseModel):
    model_config = ConfigDict(extra="ignore")
    staff_id: str
    service_center_id: str
    status: RouteStatus
    unavailable_from: DateTime | None = None
    unavailable_until: DateTime | None = None
    stops: list[Stop]
    totals: RouteTotals | None = None


class UnassignedOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    order_id: str
    reason_code: UnassignedReasonCode
    reason_text: str
    suggested_action: SuggestedAction
    proposed_slot: TimeWindow | None = None
    since: DateTime | None = None


class PgpGroup(BaseModel):
    model_config = ConfigDict(extra="ignore")
    group_id: str
    access_node_id: str
    order_ids: UniqueList(str) = Field(..., min_length=2)
    detected_at: DateTime
    action: PgpAction
    comment: str | None = None


class CancelledOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    order_id: str
    cancelled_at: DateTime
    event_id: str | None = None


class Alert(BaseModel):
    """Предупреждение. Список только пополняется (append-only)."""
    model_config = ConfigDict(extra="ignore")
    alert_id: str
    created_at: DateTime
    type: AlertType
    status: AlertStatus
    resolved_at: DateTime | None = None
    order_id: str | None = None
    group_id: str | None = None
    staff_id: str | None = None
    forecast_start: DateTime | None = None
    lateness_min: int | None = None
    suggested_action: AlertSuggestedAction
    suggested_staff_id: str | None = None
    proposed_slot: TimeWindow | None = None
    applied: bool = False
    message: str


class PlanSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    orders_total: int | None = None
    visits_planned: int | None = None
    unassigned: int | None = None
    pgp_orders: int | None = None
    cancelled: int | None = None
    travel_sec_total: int | None = None
    utilization_cv: float | None = None


class Plan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    date: str
    plan_version: Annotated[int, Field(ge=1)]
    based_on_event_id: str | None = None
    as_of: DateTime
    computation_ms: NonNegativeInt | None = None
    routes: list[Route]
    unassigned: list[UnassignedOrder]
    pgp_groups: list[PgpGroup]
    cancelled: list[CancelledOrder]
    alerts: list[Alert]
    summary: PlanSummary | None = None


class _EventBase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    event_id: str
    type: EventType
    timestamp: DateTime


class NewOrderEvent(_EventBase):
    type: Literal["NEW_ORDER"]
    order: Order


class OrderCancelledEvent(_EventBase):
    type: Literal["ORDER_CANCELLED"]
    order_id: str
    reason: Literal["NOT_CONFIRMED", "CUSTOMER_REQUEST"]


class VisitDelayedEvent(_EventBase):
    type: Literal["VISIT_DELAYED"]
    staff_id: str
    order_id: str
    expected_end: DateTime


class OrderTransferredEvent(_EventBase):
    type: Literal["ORDER_TRANSFERRED"]
    staff_id: str
    order_id: str
    actual_end: DateTime
    transferred_to: Literal["STATION_EQUIPMENT", "TRUNK_CABLE"]


class StaffUnavailableEvent(_EventBase):
    type: Literal["STAFF_UNAVAILABLE"]
    staff_id: str
    until: DateTime | None = None
    reason: Literal["VEHICLE_BREAKDOWN", "ILLNESS", "OTHER"]


class TimeTickEvent(_EventBase):
    type: Literal["TIME_TICK"]


Event = Annotated[
    Union[
        NewOrderEvent,
        OrderCancelledEvent,
        VisitDelayedEvent,
        OrderTransferredEvent,
        StaffUnavailableEvent,
        TimeTickEvent,
    ],
    Field(discriminator="type"),
]


class EventResult(BaseModel):
    """Ответ `POST /api/v1/days/{date}/events`."""
    model_config = ConfigDict(extra="ignore")
    event_id: str
    accepted: bool
    duplicate: bool
    plan_version: Annotated[int, Field(ge=1)]
    as_of: DateTime
    processing_ms: NonNegativeInt | None = None
    changed_staff_ids: list[str] | None = None
    new_alerts: list[Alert] | None = None
    message: str | None = None



class ScenarioTrigger(BaseModel):
    model_config = ConfigDict(extra="ignore")
    trigger_id: str
    type: Literal["VISIT_DELAYED", "ORDER_TRANSFERRED"]
    order_id: str
    fire_after_start_min: NonNegativeInt
    extra_duration_min: Annotated[int, Field(ge=1)] | None = None
    transferred_to: Literal["STATION_EQUIPMENT", "TRUNK_CABLE"] | None = None


class EventScenarioFile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    date: str
    now: DateTime
    events: list[Event]
    triggers: list[ScenarioTrigger]


class Health(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: Literal["ok"]
    team: str | None = None
    version: str | None = None


class LoadResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    status: Literal["loaded"]
    counts: dict[str, NonNegativeInt] | None = None


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    field: str | None = None
    message: str


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="ignore")
    code: str
    message: str
    details: list[ErrorDetail] | None = None


class ErrorResponse(BaseModel):
    """Формат всех ошибок."""
    model_config = ConfigDict(extra="ignore")
    error: ErrorBody


class PlanRequest(BaseModel):
    """Тело `POST /api/v1/days/{date}/plan` (опционально)."""
    model_config = ConfigDict(extra="ignore")
    time_limit_sec: Annotated[int, Field(ge=1, le=300)] = 300