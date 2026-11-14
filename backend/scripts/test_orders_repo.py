import asyncio
import json
from pathlib import Path
from api.app.repositories.db import AsyncSessionLocal
from api.app.repositories.sql_orders_repo import SqlOrdersRepo
from api.app.models import Order  # <-- Добавили импорт

async def test():
    data_dir = Path("data")
    orders_data = json.loads((data_dir / "orders_train.json").read_text(encoding="utf-8"))
    
    # Превращаем словари в объекты Pydantic
    test_orders = [Order(**o) for o in orders_data[:10]]
    
    async with AsyncSessionLocal() as session:
        repo = SqlOrdersRepo(session)
        
        print("Тестируем upsert_many (10 нарядов)...")
        count = await repo.upsert_many("2026-10-26", test_orders)
        print(f"✅ Записано: {count}")
        
        print("Тестируем get_by_date...")
        fetched = await repo.get_by_date("2026-10-26")
        print(f"✅ Прочитано: {len(fetched)} нарядов")
        
        print("Тестируем get_by_id...")
        order_id = test_orders[0].order_id
        single = await repo.get_by_id("2026-10-26", order_id)
        print(f"✅ Найден наряд: {single['order_id']}")

if __name__ == "__main__":
    asyncio.run(test())