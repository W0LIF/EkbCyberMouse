from datetime import datetime
from pyvrp import Model
from pyvrp.stop import MaxRuntime
from pyvrp import Solve
from api.app.models import DayInput, Staff, TravelMatrix, Plan, WorkType

def to_sec(dt_str: str, base_date: datetime) -> int:
    dt = datetime.fromisoformat(dt_str)
    return int((dt - base_date).total_seconds())

def solve_vrp(day: DayInput, staff_list: list[Staff], matrix: TravelMatrix, work_types: list[WorkType]) -> Plan:
    m = Model()
    base_date = datetime.fromisoformat(day.now)
    
    wt_dict = {wt.code: wt.duration_min * 60 for wt in work_types}
    
    point_idx = {p: i for i, p in enumerate(matrix.points)}
    
    depots = {}
    sc_ids = list(set(s.service_center_id for s in staff_list))
    for sc in sc_ids:
        depots[sc] = m.add_depot(x=0, y=0)
    
    
    NUM_SKILLS = 3
    
    
    client_map = {}
    for order in day.orders:
        tw_early = to_sec(order.slot.start, base_date)
        tw_late = to_sec(order.latest_start, base_date)
        
      
        delivery = [0] * NUM_SKILLS
        if order.work_type_code in ["REPAIR", "DEGRADATION", "DISMANTLE", "SURVEY_PRIVATE"]:
            delivery[0] = 1
        else:
            delivery[1] = 1
            
        if order.requires_height:
            delivery[2] = 1
            
        duration = wt_dict.get(order.work_type_code, 3600)
        
        c = m.add_client(
            x=0, y=0,
            delivery=delivery,
            service_duration=duration,
            tw_early=tw_early,
            tw_late=tw_late
        )
        client_map[c] = order.order_id

    
    vehicle_types = {}
    for s in staff_list:
        capacity = [0] * NUM_SKILLS
        if "LTP3" in s.profiles: capacity[0] = 1
        if "INSTALL" in s.profiles: capacity[1] = 1
        if s.height_permit: capacity[2] = 1
        
        shift_start = to_sec(f"{day.date}T{s.shift.start}:00+05:00", base_date)
        shift_end = to_sec(f"{day.date}T{s.shift.end}:00+05:00", base_date)
        
        v_type = m.add_vehicle_type(
            num_available=1,
            capacity=capacity,
            start_depot=depots[s.service_center_id],
            end_depot=depots[s.service_center_id],
            tw_early=shift_start,
            tw_late=shift_end
        )
        vehicle_types[v_type] = s.staff_id

    all_locations = list(depots.values()) + list(client_map.keys())
   
    loc_to_point = {}
    for sc, idx in depots.items():
        loc_to_point[idx] = point_idx[sc]
        
    for c_idx, order_id in client_map.items():
        order = next(o for o in day.orders if o.order_id == order_id)
        loc_to_point[c_idx] = point_idx[order.building_id]

    for i in range(len(all_locations)):
        for j in range(len(all_locations)):
            frm = all_locations[i]
            to = all_locations[j]
            if frm == to: continue
            
            p1 = loc_to_point[frm]
            p2 = loc_to_point[to]
            
            dur = matrix.durations_sec[p1][p2]
            dist = matrix.distances_m[p1][p2]
            
            m.add_edge(frm, to, distance=dist, duration=dur)

    res = m.solve(stop=MaxRuntime(10))
    
    routes = []
    if res.is_feasible():
        for v_idx, route in enumerate(res.best.routes()):
            staff_id = vehicle_types[route.vehicle_type()]
            sc_id = staff_list[v_idx].service_center_id
            
            stops = []
            seq = 1
           
            stop_depot_start = {
                "seq": seq, "type": "DEPOT_START", "location_id": sc_id,
                "arrival": day.now, "start": day.now, "end": day.now
            }
            stops.append(stop_depot_start)
            seq += 1
            
            for visit in route.visits():
                o_id = client_map[visit.client()]
                stops.append({
                    "seq": seq, "type": "VISIT", "location_id": "B", "order_id": o_id,
                    "arrival": day.now, "start": day.now, "end": day.now
                })
                seq += 1
                
            stops.append({
                "seq": seq, "type": "DEPOT_END", "location_id": sc_id,
                "arrival": day.now, "start": day.now, "end": day.now
            })
            
            routes.append({
                "staff_id": staff_id, "service_center_id": sc_id,
                "status": "ACTIVE", "stops": stops
            })

    return Plan(
        date=day.date, plan_version=1, as_of=day.now,
        routes=routes, unassigned=[], pgp_groups=[], cancelled=[], alerts=[]
    )