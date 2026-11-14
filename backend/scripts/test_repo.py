import asyncio
import json
import csv
from pathlib import Path
from api.app.repositories.db import AsyncSessionLocal
from api.app.repositories.sql_reference_repo import SqlReferenceRepo
from api.app.models import ReferenceData, WorkType

async def test():
    data_dir = Path("data")
    
    # Читаем JSON-файлы
    scs = json.loads((data_dir / "service_centers.json").read_text(encoding="utf-8"))
    staff = json.loads((data_dir / "staff.json").read_text(encoding="utf-8"))
    nodes = json.loads((data_dir / "access_nodes.json").read_text(encoding="utf-8"))
    
    # Читаем CSV с типами работ
    work_types = []
    with open(data_dir / "work_types.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["duration_min"] = int(row["duration_min"])
            row["pgp_relevant"] = row["pgp_relevant"].lower() == "true"
            row["profiles"] = row["profiles"].split("|")
            for k in ["max_start_delay_min", "deadline_value", "repeat_deadline_value"]:
                row[k] = int(row[k]) if row[k] else None
            work_types.append(WorkType(**row))

    # Собираем все данные
    ref_data = ReferenceData(
        service_centers=scs, 
        staff=staff, 
        access_nodes=nodes, 
        work_types=work_types
    )

    # Открываем сессию и вызываем наш репозиторий
    async with AsyncSessionLocal() as session:
        repo = SqlReferenceRepo(session)
        await repo.replace_all(ref_data)
        print("✅ Репозиторий успешно записал данные в БД!")

if __name__ == "__main__":
    asyncio.run(test())