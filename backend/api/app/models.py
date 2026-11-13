from _future_ import annotations

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
    StringConstrints
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

