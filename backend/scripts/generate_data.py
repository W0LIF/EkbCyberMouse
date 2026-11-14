import os
import json
from datetime import datetime, timedelta, time
import random

os.makedirs("data", exist_ok=True)

def generate_data():

    service_centers = [
        {"id": "SC-1", "name": "Центральный СЦ", "lat": 56.8389, "lon": 60.6057, "opens_at": "08:00", "closes_at": "22:00"},
        {"id": "SC-2", "name": "Северный СЦ", "lat": 56.8850, "lon": 60.6100, "opens_at": "08:00", "closes_at": "22:00"},
        {"id": "SC-3", "name": "Южный СЦ", "lat": 56.7900, "lon": 60.5900, "opens_at": "08:00", "closes_at": "22:00"},
        {"id": "SC-4", "name": "Западный СЦ", "lat": 56.8400, "lon": 60.5200, "opens_at": "08:00", "closes_at": "22:00"},
        {"id": "SC-5", "name": "Восточный СЦ", "lat": 56.8400, "lon": 60.6800, "opens_at": "08:00", "closes_at": "22:00"}
    ]


    work_types = [
        {"code": "INSTALL_PON", "name": "Инсталляция PON", "profile": "installation", "requires_height": False, "norm_minutes": 90, "deadline_hours": None, "deadline_days": 3},
        {"code": "INSTALL_FTTB", "name": "Инсталляция FTTB", "profile": "installation", "requires_height": False, "norm_minutes": 60, "deadline_hours": None, "deadline_days": 3},
        {"code": "FIX_PON", "name": "Ремонт PON (3ЛТП)", "profile": "3ltp", "requires_height": True, "norm_minutes": 45, "deadline_hours": 4, "deadline_days": None},
        {"code": "FIX_FTTB", "name": "Ремонт FTTB (3ЛТП)", "profile": "3ltp", "requires_height": True, "norm_minutes": 40, "deadline_hours": 4, "deadline_days": None},
    ]


    technologies = ["PON", "FTTB", "xDSL", "DOCSIS"]
    access_nodes = []
    for i in range(1, 121):
        access_nodes.append({
            "id": f"NODE-{i:03d}",
            "type": random.choice(["olt", "switch"]),
            "lat": round(56.8000 + random.uniform(-0.06, 0.06), 6),
            "lon": round(60.6000 + random.uniform(-0.08, 0.08), 6)
        })


    staff = []
    staff_id_counter = 1
    for sc in service_centers:

        for _ in range(6):
            staff.append({
                "id": f"STAFF-{staff_id_counter:03d}",
                "service_center_id": sc["id"],
                "profile": "installation",
                "technologies": random.sample(technologies, k=2),
                "height_access": random.choice([True, False]),
                "shift_start": "08:00",
                "shift_end": "20:00",
                "lunch_start": "13:00",
                "lunch_end": "14:00",
                "backpack_ont": random.randint(3, 8),
                "backpack_router": random.randint(3, 8),
                "backpack_tv": random.randint(1, 4)
            })
            staff_id_counter += 1

        for _ in range(8):
            staff.append({
                "id": f"STAFF-{staff_id_counter:03d}",
                "service_center_id": sc["id"],
                "profile": "3ltp",
                "technologies": technologies,
                "height_access": True,
                "shift_start": "08:00",
                "shift_end": "20:00",
                "lunch_start": "13:00",
                "lunch_end": "14:00",
                "backpack_ont": 0,
                "backpack_router": 0,
                "backpack_tv": 0
            })
            staff_id_counter += 1

    orders = []
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    order_id_counter = 1

    for day_offset in range(10):
        current_date = base_date + timedelta(days=day_offset)
        for _ in range(350):
            node = random.choice(access_nodes)
            wt = random.choice(work_types)

            slot_hour = random.randint(9, 17)
            slot_start = current_date + timedelta(hours=slot_hour, minutes=random.choice([0, 30]))
            slot_end = slot_start + timedelta(hours=2) # Двухчасовое окно

            orders.append({
                "id": f"ORD-{order_id_counter:05d}",
                "work_type_code": wt["code"],
                "technology": random.choice(technologies),
                "lat": node["lat"] + random.uniform(-0.001, 0.001),
                "lon": node["lon"] + random.uniform(-0.001, 0.001),
                "address": f"Ул. Примерная, д. {random.randint(1, 100)}",
                "access_node_id": node["id"],
                "registered_at": (slot_start - timedelta(days=random.randint(1, 3))).isoformat(),
                "slot_start": slot_start.isoformat(),
                "slot_end": slot_end.isoformat(),
                "is_repeat": random.random() < 0.1, # 10% повторных
                "req_ont": 1 if "INSTALL" in wt["code"] else 0,
                "req_router": 1 if "INSTALL" in wt["code"] else 0,
                "req_tv": 1 if random.random() < 0.3 else 0,
                "status": "pending"
            })
            order_id_counter += 1

    events = [
        {
            "received_at": datetime.now().isoformat(),
            "type": "new_order",
            "payload": {
                "id": f"ORD-{order_id_counter:05d}",
                "work_type_code": "FIX_PON",
                "technology": "PON",
                "lat": 56.8389,
                "lon": 60.6057,
                "address": "Срочный вызов, Ленина 1",
                "slot_start": datetime.now().isoformat(),
                "slot_end": (datetime.now() + timedelta(hours=2)).isoformat()
            }
        }
    ]

    with open("data/service_centers.json", "w", encoding="utf-8") as f:
        json.dump(service_centers, f, ensure_ascii=False, indent=2)
    with open("data/access_nodes.json", "w", encoding="utf-8") as f:
        json.dump(access_nodes, f, ensure_ascii=False, indent=2)
    with open("data/work_types.json", "w", encoding="utf-8") as f:
        json.dump(work_types, f, ensure_ascii=False, indent=2)
    with open("data/staff.json", "w", encoding="utf-8") as f:
        json.dump(staff, f, ensure_ascii=False, indent=2)
    with open("data/orders.json", "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
    with open("data/events_example.json", "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    print("✅ Сгенерировано:")
    print(f" - СЦ: {len(service_centers)}")
    print(f" - Узлов: {len(access_nodes)}")
    print(f" - Сотрудников: {len(staff)}")
    print(f" - Нарядов: {len(orders)} (на 10 дней)")

if __name__ == "__main__":
    generate_data()