"""Debug solver — запускает solve_vrp и выводит статистику."""
import json
import logging
import sys
sys.path.insert(0, '.')

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from api.app.models import DayInput, TravelMatrix, Order, Staff, WorkType
from solver.app.vrp import solve_vrp

sc = json.load(open('data/service_centers.json'))
staff = json.load(open('data/staff.json'))
wt = json.load(open('data/work_types.json'))
matrix_data = json.load(open('data/travel_matrix.json'))
orders_all = json.load(open('data/orders.json'))
orders = [o for o in orders_all if o['slot']['start'].startswith('2026-11-14')]

print(f"Orders for 2026-11-14: {len(orders)}")
print(f"Staff: {len(staff)}")
print(f"Work types: {len(wt)}")
print(f"Service centers: {len(sc)}")

matrix = TravelMatrix(**matrix_data)
day = DayInput(
    date='2026-11-14',
    now='2026-11-14T08:30:00+05:00',
    orders=[],
    absent_staff_ids=[],
)

plan = solve_vrp(
    date='2026-11-14',
    day=day,
    orders=orders,
    staff=staff,
    work_types=wt,
    service_centers=sc,
    matrix=matrix,
    plan_version=1,
    max_runtime_seconds=120,
)

print(f"\n=== RESULT ===")
print(f"Routes: {len(plan.routes)}")
print(f"Visits: {plan.summary.visits_planned if plan.summary else 0}")
print(f"Unassigned: {plan.summary.unassigned if plan.summary else 0}")
for i, route in enumerate(plan.routes[:10]):
    visits = [s for s in route.stops if s.type == 'VISIT']
    print(f"  Route {i+1} ({route.staff_id}): {len(visits)} visits, {route.totals.work_min} work_min")
