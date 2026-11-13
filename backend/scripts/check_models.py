import json
from pathlib import Path

from pydantic import TypeAdapter

from api.app.models import (
    DayInput,
    Event,
    EventScenarioFile,
    Plan,
    ReferenceData,
    TravelMatrix,
)

EXAMPLES = json.loads(Path("scripts/spec_examples.json").read_text())

TypeAdapter(ReferenceData).validate_python(EXAMPLES["ReferenceData"])
TypeAdapter(TravelMatrix).validate_python(EXAMPLES["TravelMatrix"])
TypeAdapter(DayInput).validate_python(EXAMPLES["DayInputExample"])
TypeAdapter(ReferenceData).validate_python(EXAMPLES["ReferenceData"])
TypeAdapter(Plan).validate_python(EXAMPLES["PlanExample"])

for ev_examle in [
    "NewOrderEventExample",
    "OrderCancelledEventExample",
    "VisitDelayedEventExample",
    "OrderTransferredEventExample",
    "StaffUnavailableEventExample",
    "TimeTickEventExample",
]:

    TypeAdapter(Event).validate_python(EXAMPLES[ev_example])

print("OK: все примеры из спеки валидны")   
