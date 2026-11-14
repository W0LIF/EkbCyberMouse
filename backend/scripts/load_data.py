import asyncio
import json
import os
import asyncpg
import csv
from datetime import datetime
from pathlib import Path


DB_URL = os.getenv("DATABASE_URL", "postgresql://ekb:ekb@127.0.0.1:5434/ekb_connect")
DATA_DIR = Path(__file__).parent.parent / "data"

async def load_data():
    print("Подключение к БД...")
    conn = await asyncpg.connect(DB_URL)
    
    print("Очистка старых данных...")
  
    await conn.execute("""
        TRUNCATE TABLE alerts, plan_versions, events, orders, days, 
        access_node_buildings, access_nodes, buildings, staff, work_types, service_centers CASCADE;
    """)

    print("Загрузка СЦ...")
    scs = json.loads((DATA_DIR / "service_centers.json").read_text(encoding="utf-8"))
    for sc in scs:
        await conn.execute("""
            INSERT INTO service_centers (service_center_id, name, address, lat, lon, opening_hours, restock_duration_min)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, sc["service_center_id"], sc["name"], sc["address"], sc["lat"], sc["lon"], json.dumps(sc["opening_hours"]), sc["restock_duration_min"])

    # 2. Справочники: Типы работ
    print("Загрузка типов работ...")
    with open(DATA_DIR / "work_types.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            await conn.execute("""
                INSERT INTO work_types (code, name, profiles, duration_min, max_start_delay_min, deadline_kind, deadline_value, repeat_deadline_value, pgp_relevant)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, row["code"], row["name"], row["profiles"].split("|"), int(row["duration_min"]), 
                int(row["max_start_delay_min"]) if row["max_start_delay_min"] else None,
                row["deadline_kind"], int(row["deadline_value"]) if row["deadline_value"] else None,
                int(row["repeat_deadline_value"]) if row["repeat_deadline_value"] else None,
                row["pgp_relevant"].lower() == "true")

    # 3. Сотрудники
    print("Загрузка сотрудников...")
    staff = json.loads((DATA_DIR / "staff.json").read_text(encoding="utf-8"))
    for s in staff:
        await conn.execute("""
            INSERT INTO staff (staff_id, display_name, service_center_id, profiles, technologies, height_permit, shift, equipment_start, equipment_capacity, experience_years)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, s["staff_id"], s.get("display_name"), s["service_center_id"], s["profiles"], s["technologies"], s["height_permit"],
            json.dumps(s["shift"]), json.dumps(s["equipment_start"]), json.dumps(s["equipment_capacity"]), s.get("experience_years"))

    # 4. Узлы и дома
    print("Загрузка узлов и домов...")
    nodes = json.loads((DATA_DIR / "access_nodes.json").read_text(encoding="utf-8"))
    for n in nodes:
        await conn.execute("""
            INSERT INTO access_nodes (access_node_id, node_type, technology, name, address, lat, lon)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, n["access_node_id"], n["node_type"], n["technology"], n["name"], n.get("address"), n["lat"], n["lon"])
        
        for b in n["buildings"]:
            await conn.execute("""
                INSERT INTO buildings (building_id, address, lat, lon, building_type, overhead_line, zone_service_center_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (building_id) DO NOTHING
            """, b["building_id"], b["address"], b["lat"], b["lon"], b["building_type"], b["overhead_line"], b.get("zone_service_center_id"))
            
            await conn.execute("""
                INSERT INTO access_node_buildings (access_node_id, building_id)
                VALUES ($1, $2) ON CONFLICT DO NOTHING
            """, n["access_node_id"], b["building_id"])

    # 5. Наряды (Orders)
    print("Загрузка нарядов (это может занять пару секунд)...")
    orders = json.loads((DATA_DIR / "orders_train.json").read_text(encoding="utf-8"))
    for o in orders:
        # Конвертация строк в datetime для asyncpg
        reg_at = datetime.fromisoformat(o["registered_at"])
        s_start = datetime.fromisoformat(o["slot"]["start"])
        s_end = datetime.fromisoformat(o["slot"]["end"])
        l_start = datetime.fromisoformat(o["latest_start"])
        d_line = datetime.fromisoformat(o["deadline"])

        await conn.execute("""
            INSERT INTO orders (order_id, work_type_code, technology, building_id, address, lat, lon, building_type, requires_height, access_node_id, registered_at, slot_start, slot_end, latest_start, deadline, req_ont, req_router, req_stb, is_repeat, previous_order_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
            ON CONFLICT (order_id) DO NOTHING
        """, o["order_id"], o["work_type_code"], o["technology"], o["building_id"], o["address"], o["lat"], o["lon"], o["building_type"], o["requires_height"], o.get("access_node_id"), 
            reg_at, s_start, s_end, l_start, d_line, 
            o["required_equipment"]["ONT"], o["required_equipment"]["ROUTER"], o["required_equipment"]["STB"], o["is_repeat"], o.get("previous_order_id"))

    await conn.close()
    print("✅ Все данные успешно загружены в PostgreSQL!")

if __name__ == "__main__":
    asyncio.run(load_data())