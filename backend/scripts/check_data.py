import json
import csv
from pathlib import Path
from pydantic import TypeAdapter

from api.app.models import (
    ReferenceData, TravelMatrix, Order, 
    DayInput, EventScenarioFile, ServiceCenter,
    Staff, AccessNode, WorkType
)

DATA_DIR = Path(__file__).parent.parent / "data"

def load_json(name):
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))

def main():
    print("Проверка файлов в data/...")
    
    # 1. Справочники
    scs = TypeAdapter(list[ServiceCenter]).validate_python(load_json("service_centers.json"))
    staff = TypeAdapter(list[Staff]).validate_python(load_json("staff.json"))
    nodes = TypeAdapter(list[AccessNode]).validate_python(load_json("access_nodes.json"))
    
    # 2. Work Types (парсим CSV)
    work_types = []
    with open(DATA_DIR / "work_types.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["duration_min"] = int(row["duration_min"])
            row["pgp_relevant"] = row["pgp_relevant"].lower() == "true"
            row["profiles"] = row["profiles"].split("|")
            # пустые строки превращаем в None
            for k in ["max_start_delay_min", "deadline_value", "repeat_deadline_value"]:
                row[k] = int(row[k]) if row[k] else None
            work_types.append(WorkType(**row))

    ref_data = ReferenceData(
        service_centers=scs, staff=staff, 
        access_nodes=nodes, work_types=work_types
    )
    print(f"OK: ReferenceData ({len(scs)} СЦ, {len(staff)} сотрудников, {len(nodes)} узлов, {len(work_types)} работ)")

    # 3. Матрица
    matrix = TravelMatrix(**load_json("travel_matrix.json"))
    assert len(matrix.points) == len(matrix.durations_sec)
    print(f"OK: TravelMatrix ({len(matrix.points)} точек)")

    # 4. Наряды
    orders_data = load_json("orders_train.json")
    orders = TypeAdapter(list[Order]).validate_python(orders_data)
    print(f"OK: Orders ({len(orders)} нарядов)")

    # 5. События
    events_data = load_json("events_example.json")
    EventScenarioFile(**events_data)
    print(f"OK: EventScenarioFile ({len(events_data['events'])} событий)")

    print("\n✅ ВСЕ ДАННЫЕ ВАЛИДНЫ И ГОТОВЫ К ЗАГРУЗКЕ!")

if __name__ == "__main__":
    main()