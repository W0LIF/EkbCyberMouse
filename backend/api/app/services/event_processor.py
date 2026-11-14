from datetime import datetime, timedelta
import uuid
from api.app.models import Plan, Event, Route, Stop, UnassignedOrder, Alert, DayInput, Staff, TravelMatrix, WorkType
from solver.app.vrp import solve_vrp
from api.app.services import state

def recalculate_route_times(route: Route, matrix: TravelMatrix, start_idx: int):
    """Пересчитывает время прибытия для всех остановок после start_idx."""
    for i in range(start_idx + 1, len(route.stops)):
        prev_stop = route.stops[i-1]
        curr_stop = route.stops[i]
        
        # Получаем время в пути из матрицы (в секундах)
        # Упрощенно берем 10 минут, если не нашли
        travel_sec = 600 
        if matrix and matrix.points and prev_stop.location_id in matrix.points and curr_stop.location_id in matrix.points:
            idx_from = matrix.points.index(prev_stop.location_id)
            idx_to = matrix.points.index(curr_stop.location_id)
            travel_sec = matrix.durations_sec[idx_from][idx_to]
        
        # Сдвигаем время
        curr_stop.arrival = prev_stop.end + timedelta(seconds=travel_sec)
        curr_stop.start = curr_stop.arrival
        # Длительность работ берем из предыдущего end - start
        duration = curr_stop.end - curr_stop.start if curr_stop.end > curr_stop.start else timedelta(minutes=30)
        curr_stop.end = curr_stop.start + duration

def process_event(
    event: Event, 
    day: DayInput, 
    current_plan: Plan, 
    staff_list: list[Staff], 
    matrix: TravelMatrix, 
    work_types: list[WorkType]
) -> Plan:
    now = datetime.fromisoformat(event.timestamp)
    new_version = current_plan.plan_version + 1
    
    # Делаем копию плана, чтобы менять её
    plan = current_plan.model_copy(deep=True)
    alerts = list(plan.alerts)
    
    # 1. ОБНОВЛЯЕМ СОСТОЯНИЕ ДНЯ
    if event.type == "NEW_ORDER":
        day.orders.append(event.order)
    elif event.type == "ORDER_CANCELLED":
        day.orders = [o for o in day.orders if o.order_id != event.order_id]
    elif event.type == "STAFF_UNAVAILABLE":
        if event.staff_id not in day.absent_staff_ids:
            day.absent_staff_ids.append(event.staff_id)
            
    # 2. МОДИФИЦИРУЕМ МАРШРУТЫ
    # Нам нужно сохранить все визиты, которые уже начались (start < now)
    frozen_visits = []
    for r in plan.routes:
        for s in r.stops:
            if s.type == "VISIT" and s.start < now:
                frozen_visits.append(s)

    routes_to_replan = []
    for r in plan.routes:
        # Убираем сотрудника, если он недоступен
        if event.type == "STAFF_UNAVAILABLE" and r.staff_id == event.staff_id:
            r.stops = [s for s in r.stops if s.start < now] # Оставляем только начатые
            continue
            
        # Отмена визита
        if event.type == "ORDER_CANCELLED":
            r.stops = [s for s in r.stops if s.order_id != event.order_id]
            
        # Задержка на объекте
        if event.type == "VISIT_DELAYED" and r.staff_id == event.staff_id:
            for i, s in enumerate(r.stops):
                if s.order_id == event.order_id:
                    s.end = datetime.fromisoformat(event.expected_end)
                    recalculate_route_times(r, matrix, i) # Пересчитываем хвост
                    break
                    
        # Передача наряда в другое подразделение (освобождаем время)
        if event.type == "ORDER_TRANSFERRED" and r.staff_id == event.staff_id:
            for i, s in enumerate(r.stops):
                if s.order_id == event.order_id:
                    s.end = datetime.fromisoformat(event.actual_end)
                    recalculate_route_times(r, matrix, i)
                    break
                    
        routes_to_replan.append(r)

    # 3. СОБИРАЕМ НАРЯДЫ, КОТОРЫЕ НУЖНО РАСПРЕДЕЛИТЬ ЗАНОВО
    # Это наряды, которые не начались, или новые наряды
    scheduled_order_ids = {s.order_id for r in plan.routes for s in r.stops if s.order_id}
    orders_to_plan = []
    for o in day.orders:
        if o.order_id not in scheduled_order_ids:
            orders_to_plan.append(o)

    # 4. ВЫЗЫВАЕМ СОЛВЕР ДЛЯ НЕРАСПРЕДЕЛЕННЫХ (если есть)
    if orders_to_plan:
        # Берем только сотрудников, которые доступны
        free_staff = [s for s in staff_list if s.staff_id not in day.absent_staff_ids]
        
        # Создаем временный день для солвера
        temp_day = day.model_copy(update={"orders": orders_to_plan})
        
        # Запускаем солвер (он вернет маршруты для оставшихся нарядов)
        # Важно: для скорости солвер должен решать только "хвост" дня
        new_plan = solve_vrp(temp_day, free_staff, matrix, work_types)
        
        # Мержим новые визиты в существующие маршруты
        for new_route in new_plan.routes:
            existing = next((r for r in routes_to_replan if r.staff_id == new_route.staff_id), None)
            if existing:
                # Добавляем только визиты (без depot_start и depot_end, они уже есть)
                for stop in new_route.stops:
                    if stop.type == "VISIT":
                        existing.stops.append(stop)
                # Пересортируем остановки по времени
                existing.stops.sort(key=lambda x: x.start)
                # Пересчитываем seq
                for i, s in enumerate(existing.stops):
                    s.seq = i + 1
            else:
                routes_to_replan.append(new_route)

    # 5. ГЕНЕРАЦИЯ АЛЕРТОВ (LATE_RISK)
    for r in routes_to_replan:
        for s in r.stops:
            if s.type == "VISIT" and s.order_id and s.start > now:
                order = next((o for o in day.orders if o.order_id == s.order_id), None)
                if order and s.start > order.latest_start:
                    # Визит опаздывает!
                    alerts.append(Alert(
                        alert_id=str(uuid.uuid4())[:8],
                        created_at=now,
                        type="LATE_RISK",
                        status="ACTIVE",
                        order_id=order.order_id,
                        staff_id=r.staff_id,
                        lateness_min=int((s.start - order.latest_start).total_seconds() / 60),
                        suggested_action="REASSIGN",
                        message=f"Визит не успевает в слот"
                    ))

    # 6. СОБИРАЕМ ФИНАЛЬНЫЙ ПЛАН
    plan.plan_version = new_version
    plan.as_of = now
    plan.based_on_event_id = event.event_id
    plan.routes = routes_to_replan
    plan.alerts = alerts
    
    # Добавляем в unassigned те, что не попали в маршруты
    final_scheduled = {s.order_id for r in plan.routes for s in r.stops if s.order_id}
    plan.unassigned = [
        UnassignedOrder(
            order_id=o.order_id, 
            reason_code="NO_SHIFT_TIME", 
            reason_text="Не удалось вписать после события", 
            suggested_action="RESCHEDULE"
        ) for o in day.orders if o.order_id not in final_scheduled
    ]

    return plan