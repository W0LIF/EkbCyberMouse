import asyncio
from datetime import datetime
from api.app.repositories.db import AsyncSessionLocal
from api.app.repositories.sql_plans_repo import SqlPlansRepo
from api.app.models import Plan
from sqlalchemy import text

async def test():
    print("Проверяем сохранение плана в БД...")
    
    # 1. Создаем Pydantic-модель плана
    test_plan = Plan(
        date="2026-10-26",
        plan_version=1,
        based_on_event_id=None,
        as_of="2026-10-26T08:30:00+05:00",
        routes=[], unassigned=[], pgp_groups=[], cancelled=[], alerts=[]
    )

    async with AsyncSessionLocal() as session:
        repo = SqlPlansRepo(session)
        
        # 2. Создаем запись дня (чтобы пройти проверку Foreign Key)
        print("Создаем запись дня...")
        date_obj = datetime.strptime("2026-10-26", "%Y-%m-%d").date()
        
        await session.execute(text("""
            INSERT INTO days (date, model_now, absent_staff_ids, event_received) 
            VALUES (:date, :now, '{}', false)
            ON CONFLICT (date) DO NOTHING
        """), {"date": date_obj, "now": test_plan.as_of})
        await session.commit()
        print("✅ Запись дня создана (или уже существует)")
        
        # 3. Сохраняем план
        print("Сохраняем тестовый план в БД...")
        await repo.save_version("2026-10-26", test_plan)
        print("✅ План сохранен!")
        
        # 4. Читаем обратно
        print("Читаем обратно...")
        latest = await repo.get_latest("2026-10-26")
        
        if latest:
            print(f"✅ Прочитан план версии: {latest.plan_version}")
        else:
            print("❌ Ошибка: план не найден после сохранения")

if __name__ == "__main__":
    asyncio.run(test())