from api.app.models import ReferenceData, DayInput, Plan

CURRENT_REFERENCE: ReferenceData | None = None
CURRENT_DAY: DayInput | None = None
CURRENT_PLAN: Plan | None = None