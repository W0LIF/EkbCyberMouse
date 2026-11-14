from datetime import datetime
from pyvrp import Model
from pyvrp.stop import MaxRuntime
from api.app.models import DayInput, Staff, TravelMatrix, Plan, WorkType, Route, Stop, UnassignedOrder

def to_sec(dt, base_date):
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return int((dt - base_date).total_seconds())

def solve_vrp(day: DayInput, staff_list: list[Staff], matrix: TravelMatrix, work_types: list[WorkType]) -> Plan:
    m = Model()
    base_date = day.now
    wt_dict = {wt.code: wt.duration_min * 60 for wt in work_types}
    point_idx = {p: i for i, p in enumerate(matrix.points)}
    
    # 1. Создаём все локации
    all_point_ids = list(set([sc.service_center_id for sc in staff_list] + [o.building_id for o in day.orders]))
    loc_objects = []
    loc_map = {}
    
    for i, point_id in enumerate(all_point_ids):
        loc = m.add_location(x=0, y=0)
        loc_objects.append(loc)
        loc_map[point_id] = i
    
    # 2. Депо
    sc_ids = list(set(s.service_center_id for s in staff_list))
    depot_objects = []
    depot_map = {}
    
    for i, sc_id in enumerate(sc_ids):
        depot = m.add_depot(location=loc_objects[loc_map[sc_id]])
        depot_objects.append(depot)
        depot_map[sc_id] = i
    
    # 3. Клиенты
    NUM_SKILLS = 3
    client_order_ids = []
    
    for order in day.orders:
        tw_early = max(0, to_sec(order.slot.start, base_date))
        tw_late = max(0, to_sec(order.latest_start, base_date))
        
        delivery = [0] * NUM_SKILLS
        if order.work_type_code in ["REPAIR", "DEGRADATION", "DISMANTLE", "SURVEY_PRIVATE"]:
            delivery[0] = 1
        else:
            delivery[1] = 1
        if order.requires_height:
            delivery[2] = 1
            
        duration = wt_dict.get(order.work_type_code, 3600)
        
        m.add_client(
            location=loc_objects[loc_map[order.building_id]],
            delivery=delivery,
            service_duration=duration,
            tw_early=tw_early,
            tw_late=tw_late,
            required=False, 
            prize=100000  # Штраф за невыполнение (достаточно большой, но не ломающий солвер)
        )
        client_order_ids.append(order.order_id)

    # 4. Машины
    vehicle_staff_ids = []
    
    for s in staff_list:
        capacity = [1000, 1000, 1000]
        if "LTP3" not in s.profiles: capacity[0] = 0
        if "INSTALL" not in s.profiles: capacity[1] = 0
        if not s.height_permit: capacity[2] = 0
        
        shift_start_time = datetime.strptime(s.shift.start, "%H:%M").time()
        shift_end_time = datetime.strptime(s.shift.end, "%H:%M").time()
        shift_start_dt = datetime.combine(day.now.date(), shift_start_time, tzinfo=day.now.tzinfo)
        shift_end_dt = datetime.combine(day.now.date(), shift_end_time, tzinfo=day.now.tzinfo)
        
        v_start = max(0, to_sec(shift_start_dt, base_date))
        v_end = max(0, to_sec(shift_end_dt, base_date))
        
        m.add_vehicle_type(
            num_available=1,
            capacity=capacity,
            start_depot=depot_objects[depot_map[s.service_center_id]],
            end_depot=depot_objects[depot_map[s.service_center_id]],
            tw_early=v_start,
            tw_late=v_end
        )
        vehicle_staff_ids.append(s.staff_id)

    # 5. Рёбра
    for i, loc1 in enumerate(loc_objects):
        for j, loc2 in enumerate(loc_objects):
            if i == j:
                continue
            p1 = point_idx[all_point_ids[i]]
            p2 = point_idx[all_point_ids[j]]
            m.add_edge(
                loc1, loc2,
                distance=matrix.distances_m[p1][p2],
                duration=matrix.durations_sec[p1][p2]
            )

    # 6. Оптимизация
    print(f"Запуск PyVRP: {len(day.orders)} заказов, {len(staff_list)} сотрудников.")
    res = m.solve(stop=MaxRuntime(10))
    print(f"Решение найдено: {res.is_feasible()}")
    
    # 7. Формирование ответа
    routes = []
    visited_clients = set()
    
    if res.is_feasible():
        for route in res.best.routes():
            v_type_idx = route.vehicle_type()
            staff_id = vehicle_staff_ids[v_type_idx]
            s_obj = next(s for s in staff_list if s.staff_id == staff_id)
            
            stops = []
            seq = 1
            shift_start_time = datetime.strptime(s_obj.shift.start, "%H:%M").time()
            shift_start_dt = datetime.combine(day.now.date(), shift_start_time, tzinfo=day.now.tzinfo)
            stops.append(Stop(
                seq=seq, type="DEPOT_START", location_id=s_obj.service_center_id,
                arrival=shift_start_dt, start=shift_start_dt, end=shift_start_dt
            ))
            seq += 1
            
            # В PyVRP 0.14.1 используем route.clients() вместо route.visits()
            for client_idx in route.clients():
                visited_clients.add(client_idx)
                o_id = client_order_ids[client_idx]
                o_obj = next(o for o in day.orders if o.order_id == o_id)
                stops.append(Stop(
                    seq=seq, type="VISIT", location_id=o_obj.building_id,
                    order_id=o_id, arrival=day.now, start=day.now, end=day.now
                ))
                seq += 1
                
            shift_end_time = datetime.strptime(s_obj.shift.end, "%H:%M").time()
            shift_end_dt = datetime.combine(day.now.date(), shift_end_time, tzinfo=day.now.tzinfo)
            stops.append(Stop(
                seq=seq, type="DEPOT_END", location_id=s_obj.service_center_id,
                arrival=shift_end_dt, start=shift_end_dt, end=shift_end_dt
            ))
            
            routes.append(Route(
                staff_id=staff_id, service_center_id=s_obj.service_center_id,
                status="ACTIVE", stops=stops
            ))

    # Собираем нераспределенные заказы
    unassigned = []
    for i, o_id in enumerate(client_order_ids):
        if i not in visited_clients:
            unassigned.append(UnassignedOrder(
                order_id=o_id,
                reason_code="NO_QUALIFIED_STAFF",
                reason_text="Не удалось уложиться в слот",
                suggested_action="RESCHEDULE"
            ))

    return Plan(
        date=day.date, plan_version=1, as_of=day.now,
        routes=routes, unassigned=unassigned, pgp_groups=[], cancelled=[], alerts=[]
    )