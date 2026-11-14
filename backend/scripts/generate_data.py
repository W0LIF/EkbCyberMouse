import json
import csv
import random
import math
from datetime import datetime, timedelta, time
from pathlib import Path

# Фиксируем seed, чтобы данные были воспроизводимы
random.seed(42)

OUT_DIR = Path(__file__).parent.parent / "data"
OUT_DIR.mkdir(exist_ok=True)

# Bounding box Екатеринбурга (примерно)
LAT_MIN, LAT_MAX = 56.75, 56.92
LON_MIN, LON_MAX = 60.50, 60.80

def rand_coord():
    return (random.uniform(LAT_MIN, LAT_MAX), random.uniform(LON_MIN, LON_MAX))

# 1. SERVICE CENTERS
def gen_sc():
    scs = []
    names = ["Центральный", "Северный", "Южный", "Западный", "Восточный"]
    for i in range(1, 6):
        lat, lon = rand_coord()
        scs.append({
            "service_center_id": f"SC-{i:02d}",
            "name": f"СЦ «{names[i-1]}»",
            "address": f"г. Екатеринбург, ул. {names[i-1]}, {i*10}",
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "opening_hours": {"open": "08:00", "close": "21:00"},
            "restock_duration_min": 15
        })
    return scs

# 2. WORK TYPES (по спеке)
def gen_work_types():
    # code, name, profiles, duration_min, max_start_delay_min, deadline_kind, deadline_value, repeat_deadline_value, pgp_relevant
    data = [
        ("INST_PON_MKD", "Инсталляция ШПД/IPTV, МКД, PON", "INSTALL", 90, 10, "WORKING_DAYS", 3, None, False),
        ("INST_FTTB_MKD", "Инсталляция ШПД/IPTV, МКД, FTTB", "INSTALL", 60, 10, "WORKING_DAYS", 3, None, False),
        ("INST_PRIVATE_VLS", "Инсталляция, частный сектор, с ВЛС", "INSTALL", 180, 10, "WORKING_DAYS", 5, None, False),
        ("ADD_SERVICE", "Доподключение услуги (IPTV, Wi-Fi-роутер)", "INSTALL", 40, 10, "SLOT", None, None, False),
        ("SURVEY_PRIVATE", "Обследование (частный сектор)", "INSTALL|LTP3", 45, 10, "WORKING_DAYS", 2, None, False),
        ("REPAIR", "Устранение неисправности (обращение абонента)", "LTP3", 60, None, "HOURS", 24, 12, True),
        ("DEGRADATION", "Устранение деградации, выявленной мониторингом", "LTP3", 45, None, "HOURS", 48, None, True),
        ("DISMANTLE", "Демонтаж АО", "LTP3", 30, None, "WORKING_DAYS", 5, None, False),
    ]
    with open(OUT_DIR / "work_types.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["code", "name", "profiles", "duration_min", "max_start_delay_min", "deadline_kind", "deadline_value", "repeat_deadline_value", "pgp_relevant"])
        for row in data:
            # None превращаем в пустую строку для CSV, как требует спека
            writer.writerow(["" if v is None else v for v in row])
    return data

# 3. ACCESS NODES & BUILDINGS
def gen_access_nodes_and_buildings():
    nodes = []
    buildings_pool = []
    b_id_counter = 1

    for i in range(1, 121):
        node_id = f"AN-{i:04d}"
        tech = random.choice(["PON", "FTTB", "XDSL", "DOCSIS"])
        node_type = {"PON": "OLT", "FTTB": "SWITCH", "XDSL": "DSLAM", "DOCSIS": "CMTS"}[tech]
        n_lat, n_lon = rand_coord()
        
        buildings = []
        for _ in range(random.randint(3, 10)):
            b_id = f"B-{b_id_counter:05d}"
            b_id_counter += 1
            b_lat = n_lat + random.uniform(-0.005, 0.005)
            b_lon = n_lon + random.uniform(-0.005, 0.005)
            b_type = random.choice(["MKD", "MKD", "PRIVATE"])
            overhead = True if b_type == "PRIVATE" and random.random() < 0.5 else False
            
            building = {
                "building_id": b_id,
                "address": f"г. Екатеринбург, ул. Тестовая, {random.randint(1, 200)}",
                "lat": round(b_lat, 6),
                "lon": round(b_lon, 6),
                "building_type": b_type,
                "overhead_line": overhead,
                "zone_service_center_id": f"SC-{random.randint(1, 5):02d}"
            }
            buildings.append(building)
            buildings_pool.append(building)

        nodes.append({
            "access_node_id": node_id,
            "node_type": node_type,
            "technology": tech,
            "name": f"{node_type} {node_id}",
            "address": f"г. Екатеринбург, ул. Узловая, {i}",
            "lat": round(n_lat, 6),
            "lon": round(n_lon, 6),
            "buildings": buildings
        })
    return nodes, buildings_pool

# 4. STAFF
def gen_staff(scs):
    staff = []
    techs = ["PON", "FTTB", "XDSL", "DOCSIS"]
    
    for i in range(1, 41):
        is_install = i <= 12
        shift_start, shift_end = ("09:00", "18:00") if random.random() < 0.7 else ("12:00", "21:00")
        
        if shift_start == "09:00":
            break_window = {"from": "12:00", "to": "15:00"}
        else:
            break_window = {"from": "15:00", "to": "18:00"}
            
        profiles = ["INSTALL"] if is_install else ["LTP3"]
        
        staff.append({
            "staff_id": f"ST-{i:03d}",
            "display_name": f"Сотрудник {i:03d}",
            "service_center_id": f"SC-{random.randint(1, 5):02d}",
            "profiles": profiles,
            "technologies": random.sample(techs, k=random.randint(2, 4)),
            "height_permit": is_install and random.random() < 0.5,
            "shift": {
                "start": shift_start,
                "end": shift_end,
                "break_duration_min": 60,
                "break_window": break_window
            },
            "equipment_start": {
                "ONT": random.randint(0, 3),
                "ROUTER": random.randint(0, 3),
                "STB": random.randint(0, 2)
            },
            "equipment_capacity": {
                "ONT": 6, "ROUTER": 6, "STB": 4
            },
            "experience_years": round(random.uniform(0.5, 10.0), 1)
        })
    return staff

# 5. TRAVEL MATRIX
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def gen_travel_matrix(scs, buildings):
    points = [sc["service_center_id"] for sc in scs] + [b["building_id"] for b in buildings]
    coords = [(sc["lat"], sc["lon"]) for sc in scs] + [(b["lat"], b["lon"]) for b in buildings]
    N = len(points)
    
    durations_sec = [[0] * N for _ in range(N)]
    distances_m = [[0] * N for _ in range(N)]
    
    for i in range(N):
        for j in range(N):
            if i == j: continue
            dist_km = haversine(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
            # Средняя скорость 25 км/ч + случайный шум (пробки)
            time_hours = dist_km / 25.0
            noise = random.uniform(0.9, 1.3)
            durations_sec[i][j] = max(0, int(time_hours * 3600 * noise))
            distances_m[i][j] = max(0, int(dist_km * 1000))
            
    return {
        "matrix_id": "ekb-v1",
        "points": points,
        "durations_sec": durations_sec,
        "distances_m": distances_m
    }

# 6. ORDERS
def gen_orders(nodes, work_types, days=10):
    orders = []
    # Генерируем начиная с понедельника 26 октября 2026
    base_date = datetime(2026, 10, 26)
    
    for day in range(days):
        if base_date.weekday() >= 5: # Пропускаем выходные
            base_date += timedelta(days=1)
            continue
            
        num_orders = random.randint(300, 400)
        
        for _ in range(num_orders):
            node = random.choice(nodes)
            bld = random.choice(node["buildings"])
            wt = random.choice(work_types)
            wt_code, _, profiles_str, duration, max_delay, _, deadline_val, repeat_deadline, _ = wt
            
            is_install = "INSTALL" in profiles_str
            if is_install and bld["building_type"] == "PRIVATE" and not bld["overhead_line"]:
                # Если инсталляция, но дом без ВЛС, то делаем обычную или доп. услугу
                if random.random() < 0.5:
                    wt_code = "INST_FTTB_MKD"
                    duration = 60
                    max_delay = 10
            elif not is_install and bld["building_type"] == "PRIVATE" and bld["overhead_line"]:
                wt_code = "REPAIR"
                duration = 60
                max_delay = None
                deadline_val = 24
                repeat_deadline = 12

            slot_hour = random.choice([8, 10, 12, 14, 16, 18])
            slot_start = base_date.replace(hour=slot_hour, minute=0, second=0)
            slot_end = slot_start + timedelta(hours=2)
            
            latest_start = slot_end if max_delay is None else min(slot_end, slot_start + timedelta(minutes=max_delay))
            
            # Расчет дедлайна
            if deadline_val is None:
                deadline = latest_start + timedelta(minutes=duration)
            elif deadline_val == 24 or deadline_val == 48: # HOURS
                deadline = slot_start + timedelta(hours=deadline_val) # Упрощенно
            else: # WORKING_DAYS
                deadline = slot_start + timedelta(days=deadline_val)

            req_eq = {"ONT": 0, "ROUTER": 0, "STB": 0}
            if "INST" in wt_code:
                req_eq["ONT"] = random.randint(0, 1)
                req_eq["ROUTER"] = random.randint(0, 1)
                req_eq["STB"] = random.randint(0, 1)
            elif "ADD" in wt_code:
                req_eq["ROUTER"] = 1
            elif "REPAIR" in wt_code or "DEGRADATION" in wt_code:
                req_eq["ROUTER"] = random.randint(0, 1)
                
            is_repeat = random.random() < 0.10
            
            orders.append({
                "order_id": f"ORD-{base_date.strftime('%Y%m%d')}-{random.randint(1, 9999):04d}",
                "work_type_code": wt_code,
                "technology": node["technology"],
                "building_id": bld["building_id"],
                "address": bld["address"],
                "lat": bld["lat"],
                "lon": bld["lon"],
                "building_type": bld["building_type"],
                "requires_height": bld["overhead_line"] and wt_code == "INST_PRIVATE_VLS",
                "access_node_id": node["access_node_id"],
                "registered_at": (slot_start - timedelta(days=random.randint(1, 3), hours=random.randint(0, 5))).isoformat() + "+05:00",
                "slot": {"start": slot_start.isoformat() + "+05:00", "end": slot_end.isoformat() + "+05:00"},
                "latest_start": latest_start.isoformat() + "+05:00",
                "deadline": deadline.isoformat() + "+05:00",
                "required_equipment": req_eq,
                "is_repeat": is_repeat,
                "previous_order_id": None
            })
        base_date += timedelta(days=1)
    return orders

# 7. EVENTS EXAMPLE
def gen_events_example(orders):
    # Выбираем случайные наряды для событий
    sample_orders = random.sample(orders, min(20, len(orders)))
    events = []
    
    base_time = datetime(2026, 10, 26, 8, 30)
    
    for i, order in enumerate(sample_orders):
        event_time = base_time + timedelta(minutes=i*15)
        # Чередуем типы событий
        if i % 3 == 0:
            events.append({
                "event_id": f"EV-{i:04d}",
                "type": "ORDER_CANCELLED",
                "timestamp": event_time.isoformat() + "+05:00",
                "order_id": order["order_id"],
                "reason": "CUSTOMER_REQUEST"
            })
        elif i % 3 == 1:
             events.append({
                "event_id": f"EV-{i:04d}",
                "type": "TIME_TICK",
                "timestamp": event_time.isoformat() + "+05:00"
            })
        elif i % 3 == 2:
            events.append({
                "event_id": f"EV-{i:04d}",
                "type": "STAFF_UNAVAILABLE",
                "timestamp": event_time.isoformat() + "+05:00",
                "staff_id": "ST-001",
                "reason": "VEHICLE_BREAKDOWN"
            })

    return {
        "date": "2026-10-26",
        "now": "2026-10-26T08:30:00+05:00",
        "events": events,
        "triggers": []
    }

def main():
    print("Генерация данных...")
    scs = gen_sc()
    with open(OUT_DIR / "service_centers.json", "w", encoding="utf-8") as f:
        json.dump(scs, f, ensure_ascii=False, indent=2)
        
    wts = gen_work_types()
    
    nodes, buildings = gen_access_nodes_and_buildings()
    with open(OUT_DIR / "access_nodes.json", "w", encoding="utf-8") as f:
        json.dump(nodes, f, ensure_ascii=False, indent=2)
        
    staff = gen_staff(scs)
    with open(OUT_DIR / "staff.json", "w", encoding="utf-8") as f:
        json.dump(staff, f, ensure_ascii=False, indent=2)
        
    matrix = gen_travel_matrix(scs, buildings)
    with open(OUT_DIR / "travel_matrix.json", "w", encoding="utf-8") as f:
        json.dump(matrix, f, ensure_ascii=False, indent=2)
        
    orders = gen_orders(nodes, wts)
    with open(OUT_DIR / "orders_train.json", "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
        
    events = gen_events_example(orders)
    with open(OUT_DIR / "events_example.json", "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    print("✅ Успешно сгенерировано в папку data/:")
    print(f" - СЦ: {len(scs)}")
    print(f" - Узлов: {len(nodes)}")
    print(f" - Домов: {len(buildings)}")
    print(f" - Сотрудников: {len(staff)}")
    print(f" - Нарядов: {len(orders)}")
    print(f" - Точек в матрице: {len(matrix['points'])}")

if __name__ == "__main__":
    main()