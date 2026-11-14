import httpx
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8080/api/v1"

def generate_simple_data():
    now = datetime(2026, 10, 26, 8, 30)
    
    # 1. СЦ
    scs = [
        {"service_center_id": "SC-01", "name": "СЦ-1", "address": "ул. Ленина, 1", 
         "lat": 56.8, "lon": 60.6, "opening_hours": {"open": "08:00", "close": "21:00"}, "restock_duration_min": 15}
    ]

    # 2. Сотрудники (2 штуки, оба могут всё)
    staff = []
    for i in range(1, 3):
        staff.append({
            "staff_id": f"ST-{i:03d}", "display_name": f"Сотрудник {i}",
            "service_center_id": "SC-01",
            "profiles": ["LTP3", "INSTALL"],
            "technologies": ["PON", "FTTB"],
            "height_permit": True,
            "shift": {"start": "09:00", "end": "18:00", "break_duration_min": 60, "break_window": {"from": "12:00", "to": "15:00"}},
            "equipment_start": {"ONT": 5, "ROUTER": 5, "STB": 2},
            "equipment_capacity": {"ONT": 10, "ROUTER": 10, "STB": 5}
        })

    # 3. Локации (1 СЦ и 2 дома)
    points = ["SC-01", "B-00001", "B-00002"]
    nodes = [
        {"access_node_id": "AN-0001", "node_type": "OLT", "technology": "PON", "name": "Узел 1", "lat": 56.81, "lon": 60.61,
         "buildings": [{"building_id": "B-00001", "address": "ул. Тестовая 1", "lat": 56.81, "lon": 60.61, "building_type": "MKD", "overhead_line": False}]},
        {"access_node_id": "AN-0002", "node_type": "OLT", "technology": "PON", "name": "Узел 2", "lat": 56.82, "lon": 60.62,
         "buildings": [{"building_id": "B-00002", "address": "ул. Тестовая 2", "lat": 56.82, "lon": 60.62, "building_type": "MKD", "overhead_line": False}]}
    ]

    # 4. Матрица (3x3)
    matrix = {
        "matrix_id": "test-v1", "points": points,
        "durations_sec": [[0, 600, 900], [600, 0, 300], [900, 300, 0]],
        "distances_m": [[0, 2000, 3000], [2000, 0, 1000], [3000, 1000, 0]]
    }

    # 5. Типы работ
    work_types = [
        {"code": "REPAIR", "name": "Ремонт", "profiles": ["LTP3"], "duration_min": 60, "max_start_delay_min": None, "deadline_kind": "HOURS", "deadline_value": 24, "repeat_deadline_value": 12, "pgp_relevant": True},
        {"code": "INST_PON_MKD", "name": "Инсталляция", "profiles": ["INSTALL"], "duration_min": 90, "max_start_delay_min": 10, "deadline_kind": "WORKING_DAYS", "deadline_value": 3, "repeat_deadline_value": None, "pgp_relevant": False}
    ]

    # 6. Заказы (2 штуки, слоты не пересекаются, чтобы 1 сотрудник мог сделать оба)
    orders = []
    # Заказ 1: слот 10:00 - 12:00
    slot1_start = now + timedelta(hours=1.5)
    orders.append({
        "order_id": "ORD-20261026-0001", "work_type_code": "REPAIR",
        "technology": "PON", "building_id": "B-00001", "address": "ул. Тестовая 1",
        "lat": 56.81, "lon": 60.61, "building_type": "MKD", "requires_height": False,
        "access_node_id": "AN-0001", "registered_at": (now - timedelta(days=1)).isoformat() + "+05:00",
        "slot": {"start": slot1_start.isoformat() + "+05:00", "end": (slot1_start + timedelta(hours=2)).isoformat() + "+05:00"},
        "latest_start": (slot1_start + timedelta(hours=2)).isoformat() + "+05:00",
        "deadline": (slot1_start + timedelta(hours=24)).isoformat() + "+05:00",
        "required_equipment": {"ONT": 0, "ROUTER": 0, "STB": 0}, "is_repeat": False
    })
    # Заказ 2: слот 13:00 - 15:00
    slot2_start = now + timedelta(hours=4.5)
    orders.append({
        "order_id": "ORD-20261026-0002", "work_type_code": "REPAIR",
        "technology": "PON", "building_id": "B-00002", "address": "ул. Тестовая 2",
        "lat": 56.82, "lon": 60.62, "building_type": "MKD", "requires_height": False,
        "access_node_id": "AN-0002", "registered_at": (now - timedelta(days=1)).isoformat() + "+05:00",
        "slot": {"start": slot2_start.isoformat() + "+05:00", "end": (slot2_start + timedelta(hours=2)).isoformat() + "+05:00"},
        "latest_start": (slot2_start + timedelta(hours=2)).isoformat() + "+05:00",
        "deadline": (slot2_start + timedelta(hours=24)).isoformat() + "+05:00",
        "required_equipment": {"ONT": 0, "ROUTER": 0, "STB": 0}, "is_repeat": False
    })

    return {
        "reference": {"service_centers": scs, "staff": staff, "access_nodes": nodes, "work_types": work_types},
        "matrix": matrix,
        "day": {"date": "2026-10-26", "now": now.isoformat() + "+05:00", "orders": orders, "absent_staff_ids": []}
    }

def main():
    data = generate_simple_data()
    with httpx.Client(timeout=300.0) as client:
        print("1. Загрузка справочников...")
        resp = client.put(f"{BASE_URL}/reference", json=data["reference"])
        print("Ответ:", resp.status_code, resp.text)

        print("2. Загрузка матрицы...")
        resp = client.put(f"{BASE_URL}/reference/travel-matrix", json=data["matrix"])
        print("Ответ:", resp.status_code, resp.text)

        print("3. Загрузка дня...")
        resp = client.put(f"{BASE_URL}/days/2026-10-26", json=data["day"])
        print("Ответ:", resp.status_code, resp.text)

        print("4. Построение плана...")
        resp = client.post(f"{BASE_URL}/days/2026-10-26/plan")
        print("Статус ответа:", resp.status_code)
        
        if resp.status_code == 200:
            plan = resp.json()
            print(f"✅ План построен!")
            print(f" - Маршрутов: {len(plan['routes'])}")
            print(f" - Не распределено: {len(plan['unassigned'])}")
        else:
            print("ОШИБКА:", resp.text)

if __name__ == "__main__":
    main()