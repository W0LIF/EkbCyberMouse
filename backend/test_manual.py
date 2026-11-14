from pydantic import TypeAdapter
from api.app.models import Equipment, LocalTime, Plan

print("1. Проверяем Equipment...")
eq = Equipment(ONT=1, ROUTER=1, STB=0)
print("   OK:", eq.model_dump())

print("2. Проверяем LocalTime...")
t = TypeAdapter(LocalTime).validate_python("09:00")
print("   OK:", t)

print("3. Проверяем создание плана...")
plan = Plan(
    date="2026-10-26",
    plan_version=1,
    as_of="2026-10-26T08:30:00+05:00",
    routes=[],
    unassigned=[],
    pgp_groups=[],
    cancelled=[],
    alerts=[]
)
print("   OK, план валиден")
print("   Дата:", plan.date)
print("   Время (ISO):", plan.as_of)