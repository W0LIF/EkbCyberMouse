"""Генерирует все JSON данные для тестов. Запуск: python scripts/generate_all_data.py"""
from __future__ import annotations
import json, math, random, shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data"
ROOT.mkdir(exist_ok=True)

# удаляем старьё
for name in ("service_centers.json", "staff.json", "access_nodes.json",
             "work_types.json", "orders.json", "orders_train.json",
             "travel_matrix.json", "events_example.json"):
    p = ROOT / name
    if p.exists():
        p.unlink()

random.seed(42)
TZ = timezone(timedelta(hours=5))
DAY_START = datetime(2026, 11, 14, 0, 0, tzinfo=TZ)  # любой референс, не используется


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ---------- 1. СЦ ----------
SCS = [
    ("SC-01", "СЦ «Центральный»", 56.858703, 60.507503),
    ("SC-02", "СЦ «Северный»",    56.796755, 60.566963),
    ("SC-03", "СЦ «Южный»",       56.875200, 60.703010),
    ("SC-04", "СЦ «Западный»",    56.901671, 60.526082),
    ("SC-05", "СЦ «Восточный»",   56.821727, 60.508939),
]
service_centers = [
    {
        "service_center_id": sid, "name": name,
        "address": f"г. Екатеринбург, {name}, 10",
        "lat": lat, "lon": lon,
        "opening_hours": {"open": "08:00", "close": "21:00"},
        "restock_duration_min": 15,
    }
    for sid, name, lat, lon in SCS
]

# ---------- 2. Work Types ----------
work_types = [
    {"code": "INST_PON_MKD", "name": "Установка PON в МКД", "profiles": ["INSTALL"],
     "duration_min": 90, "max_start_delay_min": 10, "deadline_kind": "WORKING_DAYS",
     "deadline_value": 3, "repeat_deadline_value": None, "pgp_relevant": True},
    {"code": "INST_FTTB_MKD", "name": "Установка FTTB в МКД", "profiles": ["INSTALL"],
     "duration_min": 90, "max_start_delay_min": 10, "deadline_kind": "WORKING_DAYS",
     "deadline_value": 3, "repeat_deadline_value": None, "pgp_relevant": True},
    {"code": "INST_PRIVATE_VLS", "name": "Установка в частном доме", "profiles": ["INSTALL"],
     "duration_min": 120, "max_start_delay_min": 10, "deadline_kind": "WORKING_DAYS",
     "deadline_value": 5, "repeat_deadline_value": None, "pgp_relevant": False},
    {"code": "ADD_SERVICE", "name": "Доп. услуга", "profiles": ["INSTALL"],
     "duration_min": 40, "max_start_delay_min": 10, "deadline_kind": "HOURS",
     "deadline_value": 1, "repeat_deadline_value": None, "pgp_relevant": False},
    {"code": "SURVEY_PRIVATE", "name": "Обследование", "profiles": ["INSTALL"],
     "duration_min": 60, "max_start_delay_min": 10, "deadline_kind": "WORKING_DAYS",
     "deadline_value": 2, "repeat_deadline_value": None, "pgp_relevant": False},
    {"code": "REPAIR", "name": "Ремонт", "profiles": ["INSTALL", "LTP3"],
     "duration_min": 90, "max_start_delay_min": None, "deadline_kind": "HOURS",
     "deadline_value": 24, "repeat_deadline_value": None, "pgp_relevant": False},
    {"code": "DEGRADATION", "name": "Деградация", "profiles": ["INSTALL", "LTP3"],
     "duration_min": 90, "max_start_delay_min": None, "deadline_kind": "HOURS",
     "deadline_value": 24, "repeat_deadline_value": None, "pgp_relevant": False},
    {"code": "DISMANTLE", "name": "Демонтаж", "profiles": ["INSTALL"],
     "duration_min": 60, "max_start_delay_min": None, "deadline_kind": "WORKING_DAYS",
     "deadline_value": 5, "repeat_deadline_value": None, "pgp_relevant": False},
]

# ---------- 3. Access Nodes + Buildings ----------
# 120 узлов, ~7 зданий на узел → 766 зданий
NODE_BASE = [
    (56.812090, 60.566997), (56.841704, 60.520998), (56.777289, 60.627911),
    (56.810843, 60.570505), (56.762024, 60.561121), (56.762509, 60.564720),
    (56.801068, 60.591198), (56.749676, 60.594750), (56.760377, 60.642353),
    (56.848245, 60.551773), (56.756009, 60.649607), (56.828297, 60.640912),
    (56.757685, 60.592886), (56.854455, 60.642882), (56.806141, 60.604909),
    (56.813182, 60.559914), (56.849497, 60.576904), (56.812323, 60.636594),
    (56.838432, 60.571748), (56.779701, 60.620388), (56.806690, 60.632409),
    (56.855547, 60.537574), (56.773759, 60.606306), (56.794486, 60.661949),
    (56.744062, 60.594456), (56.784612, 60.579044), (56.847967, 60.572374),
    (56.769941, 60.561496), (56.818805, 60.586949), (56.778011, 60.664228),
    (56.766440, 60.607382), (56.755650, 60.605503), (56.750474, 60.628010),
    (56.840345, 60.537001), (56.839458, 60.534789), (56.816313, 60.654603),
    (56.780395, 60.558155), (56.857404, 60.532309), (56.790486, 60.599615),
    (56.772177, 60.596749), (56.777267, 60.532655), (56.766906, 60.635250),
    (56.780983, 60.617039), (56.759895, 60.671603), (56.759346, 60.610609),
    (56.826194, 60.641755), (56.810886, 60.546264), (56.843883, 60.634153),
    (56.843124, 60.651077), (56.851502, 60.572979), (56.842095, 60.541149),
    (56.838755, 60.554601), (56.853264, 60.673066), (56.797945, 60.549885),
    (56.773843, 60.546447), (56.786227, 60.678244), (56.786991, 60.553885),
    (56.856908, 60.677457), (56.790768, 60.667277), (56.801046, 60.632446),
    (56.853288, 60.667912), (56.790594, 60.660834), (56.766852, 60.663144),
    (56.743420, 60.604452), (56.843788, 60.612197), (56.743974, 60.667423),
    (56.773571, 60.626213), (56.785781, 60.658481), (56.779599, 60.572250),
    (56.843573, 60.536178), (56.769033, 60.653420), (56.790277, 60.674934),
    (56.830424, 60.603727), (56.800435, 60.617185), (56.779697, 60.633950),
    (56.799129, 60.523008), (56.847591, 60.520768), (56.813490, 60.653531),
    (56.816739, 60.603455), (56.851614, 60.573979), (56.852356, 60.555527),
    (56.824507, 60.596749), (56.749770, 60.529661), (56.850021, 60.657345),
    (56.772735, 60.644506), (56.826345, 60.663014), (56.746388, 60.668146),
    (56.802908, 60.595789), (56.763395, 60.667944), (56.833941, 60.663334),
    (56.856128, 60.656441), (56.802730, 60.594029), (56.810972, 60.558567),
    (56.851425, 60.586811), (56.751725, 60.566022), (56.781820, 60.582813),
    (56.798678, 60.653419), (56.823572, 60.615105), (56.833460, 60.552657),
    (56.791188, 60.546683), (56.811996, 60.554365), (56.852550, 60.574271),
    (56.798633, 60.673300), (56.819058, 60.584359), (56.833173, 60.576002),
    (56.846972, 60.635417), (56.845410, 60.629732), (56.828804, 60.530702),
    (56.845501, 60.606558), (56.792100, 60.533598), (56.851111, 60.671013),
    (56.858636, 60.565323), (56.750413, 60.645443), (56.811458, 60.619626),
    (56.812983, 60.564445), (56.854140, 60.627225), (56.760602, 60.628049),
    (56.755189, 60.618450), (56.802793, 60.669650), (56.783297, 60.530245),
]

N_NODES = len(NODE_BASE)
assert N_NODES == 120
TECHNOLOGIES = ["PON", "FTTB", "XDSL", "DOCSIS"]

access_nodes: list[dict] = []
buildings_flat: list[dict] = []

# 766 зданий: первые 46 узлов получат по 7, остальные по 6
per_node = [7 if i < 46 else 6 for i in range(N_NODES)]
assert sum(per_node) == 766

b_counter = 1
for i, (lat, lon) in enumerate(NODE_BASE):
    node_id = f"AN-{i+1:04d}"
    node_tech = TECHNOLOGIES[i % len(TECHNOLOGIES)]
    node_type = "OLT" if node_tech == "PON" else ("DSLAM" if node_tech == "XDSL" else "SWITCH")
    sc_id = SCS[i % 5][0]

    node_buildings: list[dict] = []
    for _ in range(per_node[i]):
        b_id = f"B-{b_counter:05d}"
        b_counter += 1
        # лёгкий разброс ~200-400 м
        b_lat = lat + random.uniform(-0.003, 0.003)
        b_lon = lon + random.uniform(-0.005, 0.005)
        b_type = random.choice(["MKD", "PRIVATE"])
        b = {
            "building_id": b_id,
            "address": f"г. Екатеринбург, ул. Тестовая, {b_counter}",
            "lat": round(b_lat, 6),
            "lon": round(b_lon, 6),
            "building_type": b_type,
            "overhead_line": random.random() < 0.3,
            "zone_service_center_id": sc_id,
        }
        node_buildings.append(b)
        buildings_flat.append(b)

    access_nodes.append({
        "access_node_id": node_id,
        "node_type": node_type,
        "technology": node_tech,
        "name": f"Узел {node_id}",
        "address": f"г. Екатеринбург, ул. Тестовая, {i+1}",
        "lat": lat, "lon": lon,
        "buildings": node_buildings,
    })

# ---------- 4. Staff ----------
staff_list: list[dict] = []
shift_patterns = [
    ("08:00", "17:00", {"from": "12:00", "to": "14:00"}),
    ("12:00", "21:00", {"from": "16:00", "to": "18:00"}),
    ("09:00", "18:00", {"from": "13:00", "to": "15:00"}),
]
sid = 1
for sc_id, _, _, _ in SCS:
    for _ in range(8):  # 8 сотрудников на СЦ × 5 = 40
        profile = "LTP3" if sid % 4 == 0 else "INSTALL"
        techs = random.sample(TECHNOLOGIES, k=random.choice([2, 3, 4]))
        start, end, bw = shift_patterns[sid % 3]
        staff_list.append({
            "staff_id": f"ST-{sid:03d}",
            "display_name": f"Сотрудник {sid:03d}",
            "service_center_id": sc_id,
            "profiles": [profile] if profile == "LTP3" else ["INSTALL"],
            "technologies": techs,
            "height_permit": random.random() < 0.5,
            "shift": {
                "start": start, "end": end, "break_duration_min": 60,
                "break_window": bw,
            },
            "equipment_start": {"ONT": 2, "ROUTER": 2, "STB": 2},
            "equipment_capacity": {"ONT": 6, "ROUTER": 6, "STB": 4},
            "experience_years": round(random.uniform(0.5, 10), 1),
        })
        sid += 1

# ---------- 5. Orders ----------
# 200 на день × 5 дней = 1000
order_dates = [datetime(2026, 11, 14, tzinfo=TZ) + timedelta(days=d) for d in range(5)]
all_orders: list[dict] = []

for day_idx, day_dt in enumerate(order_dates):
    date_str = day_dt.strftime("%Y%m%d")
    for k in range(200):
        # 70% INSTALL (INST_PON_MKD / INST_FTTB_MKD / INST_PRIVATE_VLS),
        # 30% others
        wt = random.choices(
            ["INST_PON_MKD", "INST_FTTB_MKD", "INST_PRIVATE_VLS", "ADD_SERVICE",
             "SURVEY_PRIVATE", "REPAIR", "DEGRADATION", "DISMANTLE"],
            weights=[25, 25, 10, 10, 10, 8, 7, 5],
        )[0]
        b = random.choice(buildings_flat)
        node = next(n for n in access_nodes if any(
            bb["building_id"] == b["building_id"] for bb in n["buildings"]
        ))
        slot_start_h = random.choice([9, 10, 11, 12, 13, 14, 15, 16, 17])
        slot_start = day_dt.replace(hour=slot_start_h, minute=0)
        slot_end = slot_start + timedelta(hours=2)
        registered = day_dt - timedelta(hours=random.randint(6, 48))
        latest = slot_end - timedelta(minutes=random.choice([0, 5, 10, 20, 30]))
        deadline = slot_end + timedelta(days=random.choice([0, 1, 2]))
        req_eq = {
            "ONT": 1 if wt in ("INST_PON_MKD", "INST_FTTB_MKD", "INST_PRIVATE_VLS") else 0,
            "ROUTER": 1 if wt in ("INST_PON_MKD", "INST_FTTB_MKD", "INST_PRIVATE_VLS") else 0,
            "STB": random.randint(0, 1),
        }
        all_orders.append({
            "order_id": f"ORD-{date_str}-{k+1:04d}",
            "work_type_code": wt,
            "technology": random.choice(TECHNOLOGIES),
            "building_id": b["building_id"],
            "address": b["address"],
            "lat": b["lat"],
            "lon": b["lon"],
            "building_type": b["building_type"],
            "requires_height": random.random() < 0.3,
            "access_node_id": node["access_node_id"],
            "registered_at": iso(registered),
            "slot": {"start": iso(slot_start), "end": iso(slot_end)},
            "latest_start": iso(latest),
            "deadline": iso(deadline),
            "required_equipment": req_eq,
            "is_repeat": random.random() < 0.1,
            "previous_order_id": None,
        })

# 30 "тренировочных" из последнего дня
orders_train = all_orders[:30]

# ---------- 6. Travel Matrix ----------
points = [sc[0] for sc in SCS] + [b["building_id"] for b in buildings_flat]
coords = [(sc[2], sc[3]) for sc in SCS] + [(b["lat"], b["lon"]) for b in buildings_flat]
n = len(points)
print(f"Строю матрицу {n}x{n} ...")

# Для читаемости: 1.4 — коэффициент кривизны дорог, 40 км/ч средняя скорость
durations = [[0] * n for _ in range(n)]
distances = [[0] * n for _ in range(n)]
for i in range(n):
    for j in range(n):
        if i == j:
            continue
        d = haversine(*coords[i], *coords[j]) * 1.4
        distances[i][j] = int(d)
        durations[i][j] = max(1, int(d / 40000 * 3600))  # 40 км/ч

# ---------- 7. Events example ----------
events_example = {
    "date": "2026-11-14",
    "now": "2026-11-14T08:30:00+05:00",
    "events": [
        {"event_id": "EV-0000", "type": "ORDER_CANCELLED", "timestamp": "2026-11-14T08:30:00+05:00",
         "order_id": orders_train[0]["order_id"], "reason": "CUSTOMER_REQUEST"},
        {"event_id": "EV-0001", "type": "TIME_TICK", "timestamp": "2026-11-14T08:45:00+05:00"},
        {"event_id": "EV-0002", "type": "STAFF_UNAVAILABLE", "timestamp": "2026-11-14T09:00:00+05:00",
         "staff_id": "ST-001", "reason": "VEHICLE_BREAKDOWN"},
    ],
    "triggers": [],
}

# ---------- запись ----------
def dump(name, obj):
    with open(ROOT / name, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"✓ {name}")

dump("service_centers.json", service_centers)
dump("staff.json", staff_list)
dump("access_nodes.json", access_nodes)
dump("work_types.json", work_types)
dump("orders.json", all_orders)
dump("orders_train.json", orders_train)
dump("events_example.json", events_example)

# матрицу пишем отдельно — большой файл, без indent
with open(ROOT / "travel_matrix.json", "w", encoding="utf-8") as f:
    f.write('{\n  "matrix_id": "ekb-v1",\n  "points": ')
    json.dump(points, f)
    f.write(',\n  "durations_sec": ')
    json.dump(durations, f)
    f.write(',\n  "distances_m": ')
    json.dump(distances, f)
    f.write("\n}\n")
print("✓ travel_matrix.json")
print("\nГотово.")