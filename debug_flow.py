"""Имитирует серверный flow: загрузка через API, затем solver."""
import sys, json
sys.path.insert(0, 'backend')

from datetime import datetime
from api.app.models import DayInput, TravelMatrix
from api.app.routers.plan import _flat_to_order

# Load raw orders (как сервер при загрузке)
orders_all = json.load(open('backend/data/orders.json'))
orders = [o for o in orders_all if o['slot']['start'].startswith('2026-11-14')]

# Имитируем то, что сервер делает при загрузке в БД
# Order model → DB row → _flat_to_order
from api.app.models import Order
orders_objs = [Order(**o) for o in orders]

# Имитируем строку из БД
def simulate_db_row(o: Order) -> dict:
    return {
        "order_id": o.order_id,
        "work_type_code": o.work_type_code,
        "technology": o.technology,
        "building_id": o.building_id,
        "address": o.address,
        "lat": o.lat,
        "lon": o.lon,
        "building_type": o.building_type,
        "requires_height": o.requires_height,
        "access_node_id": o.access_node_id,
        "registered_at": o.registered_at,
        "slot_start": o.slot.start,
        "slot_end": o.slot.end,
        "latest_start": o.latest_start,
        "deadline": o.deadline,
        "req_ont": o.required_equipment.ONT,
        "req_router": o.required_equipment.ROUTER,
        "req_stb": o.required_equipment.STB,
        "is_repeat": o.is_repeat,
        "previous_order_id": o.previous_order_id,
    }

# Прогоняем через _flat_to_order
flat_orders = [_flat_to_order(simulate_db_row(o)) for o in orders_objs]

# Сравниваем с raw
raw_eq = orders[0]['required_equipment']
flat_eq = flat_orders[0]['required_equipment']
print(f"Raw equipment: {raw_eq}")
print(f"Flat equipment: {flat_eq}")
print(f"Match: {raw_eq == flat_eq}")

# Проверяем slot
print(f"\nRaw slot: {orders[0]['slot']}")
print(f"Flat slot: {flat_orders[0]['slot']}")

# Проверяем latest_start
print(f"Raw latest: {orders[0]['latest_start']}")
print(f"Flat latest: {flat_orders[0]['latest_start']}")

# Проверяем все ли orders одинаковые
diffs = 0
for i in range(len(orders)):
    raw = orders[i]
    flat = flat_orders[i]
    if raw['required_equipment'] != flat['required_equipment']:
        diffs += 1
        if diffs <= 3:
            print(f"\nDIFF at {i}: raw={raw['required_equipment']}, flat={flat['required_equipment']}")
print(f"\nTotal equipment diffs: {diffs}/{len(orders)}")
