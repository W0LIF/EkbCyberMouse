"""VRP-решатель. Возвращает Plan — pyvrp 0.14 compatible."""
from __future__ import annotations

import logging
from math import ceil
from datetime import datetime, timedelta, timezone

import numpy as np
from pyvrp import ProblemData, Depot, PenaltyParams, solve as pyvrp_solve
from pyvrp.stop import MaxRuntime
from pyvrp.solve import SolveParams

from api.app.models import (
    Plan, Route, Stop, RouteTotals, PlanSummary,
    UnassignedOrder, DayInput, Order, Staff, WorkType,
    ServiceCenter, TravelMatrix, Equipment,
)
from api.app.services.travel_time import adjusted_travel_seconds

logger = logging.getLogger(__name__)
BUSINESS_TZ = timezone(timedelta(hours=5))


def _as_dict(obj):
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "dict"):
        return obj.dict()
    return vars(obj)


def _minutes_from_midnight(dt: datetime) -> int:
    """Минуты от полуночи начала дня."""
    dt = dt.astimezone(BUSINESS_TZ)
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return int((dt - midnight).total_seconds() // 60)


def _ceil_minutes_from_midnight(dt: datetime) -> int:
    dt = dt.astimezone(BUSINESS_TZ)
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return ceil((dt - midnight).total_seconds() / 60)


# ---------------------------------------------------------------------------
# Вход в солвер
# ---------------------------------------------------------------------------

def _solve_vrp_core(
    *,
    date: str,
    day: DayInput,
    orders: list[Order] | list[dict],
    staff: list[Staff] | list[dict],
    work_types: list[WorkType] | list[dict],
    service_centers: list[ServiceCenter] | list[dict],
    matrix: TravelMatrix,
    plan_version: int = 1,
    max_runtime_seconds: int = 30,
) -> Plan:
    orders_d = [_as_dict(o) for o in orders]
    staff_d = [_as_dict(s) for s in staff]
    wt_d = {
        w["code"] if isinstance(w, dict) else w.code: _as_dict(w) for w in work_types
    }
    sc_d = [_as_dict(s) for s in service_centers]

    if not orders_d:
        raise ValueError("пустой список orders")
    if not sc_d:
        raise ValueError("нет service_centers")

    # ---- 1. Фильтр: кто может делать заказ ---------------------------------
    absent = set(day.absent_staff_ids or [])
    available_staff = [s for s in staff_d if s["staff_id"] not in absent]

    def _can_do(order: dict, st: dict) -> bool:
        wt = wt_d.get(order["work_type_code"])
        if not wt:
            return False
        if order["technology"] not in st["technologies"]:
            return False
        if not set(wt["profiles"]) & set(st["profiles"]):
            return False
        if order.get("requires_height") and not st["height_permit"]:
            return False
        return True

    client_to_order: list[int] = []
    skipped_prefilter: list[int] = []
    for i, o in enumerate(orders_d):
        if not any(_can_do(o, st) for st in available_staff):
            skipped_prefilter.append(i)
            continue
        client_to_order.append(i)

    # ---- 2. Индексы в travel matrix ----------------------------------------
    pts = {pid: idx for idx, pid in enumerate(matrix.points)}

    def _mat_idx(pid: str) -> int | None:
        return pts.get(pid)

    # ---- 3. Построение модели pyvrp ----------------------------------------
    from pyvrp import Model

    m = Model()
    depots: dict[str, Depot] = {}  # service_center_id -> Depot object

    for sc in sc_d:
        loc = m.add_location(x=sc["lon"], y=sc["lat"])
        depot = m.add_depot(location=loc)
        depots[sc["service_center_id"]] = depot

    # client indices внутри модели pyvrp
    client_model_indices: list[int] = []  # index в m.locations
    loc_idx_to_order_pos: dict[int, int] = {}  # m.locations index -> orders_d index

    # Each delivery dimension is bounded by the vehicle's maximum stock.
    if staff_d:
        cap0 = staff_d[0].get("equipment_capacity", {})
        cap_len = len(cap0) if isinstance(cap0, dict) else 1
    else:
        cap_len = 1

    for pos in client_to_order:
        o = orders_d[pos]
        loc = m.add_location(x=o["lon"], y=o["lat"])
        loc_idx = len(m.locations) - 1
        client_model_indices.append(loc_idx)
        loc_idx_to_order_pos[loc_idx] = pos

        wt = wt_d.get(o["work_type_code"], {})
        service_min = int(
            o.get("duration_estimate_min", wt.get("duration_min", 60))
        )

        # Временные окна — минуты от полуночи
        slot = o.get("slot") or {}
        try:
            s = datetime.fromisoformat(slot["start"]).astimezone(BUSINESS_TZ)
            e = datetime.fromisoformat(slot["end"]).astimezone(BUSINESS_TZ)
            latest = datetime.fromisoformat(o["latest_start"]).astimezone(BUSINESS_TZ)
            tw_early = _minutes_from_midnight(s)
            tw_late = _minutes_from_midnight(min(e, latest))
        except (KeyError, ValueError, TypeError):
            tw_early, tw_late = 0, 24 * 60

        tw_early = max(tw_early, 0)
        tw_late = max(tw_late, tw_early + 1)

        # Delivery lengths must match the vehicle capacity dimensions.
        req_eq = o.get("required_equipment", {})
        delivery = [
            req_eq.get("ONT", 0),
            req_eq.get("ROUTER", 0),
            req_eq.get("STB", 0),
        ]
        # Если capacity короче — обрезаем; если длиннее — дополняем нулями
        if len(delivery) > cap_len:
            delivery = delivery[:cap_len]
        elif len(delivery) < cap_len:
            delivery += [0] * (cap_len - len(delivery))
        pickup = [0] * cap_len

        m.add_client(
            location=loc,
            delivery=delivery,
            pickup=pickup,
            service_duration=service_min,
            tw_early=tw_early,
            tw_late=tw_late,
        )

    # ---- 4. Машины (vehicle_type) ------------------------------------------
    staff_order: list[dict] = []
    for st in available_staff:
        depot = depots.get(st["service_center_id"])
        if depot is None:
            continue

        shift = st["shift"]
        try:
            sh_s = datetime.strptime(shift["start"], "%H:%M").time()
            sh_e = datetime.strptime(shift["end"], "%H:%M").time()
            shift_start_min = sh_s.hour * 60 + sh_s.minute
            end_min = sh_e.hour * 60 + sh_e.minute
            if end_min <= shift_start_min:
                end_min += 24 * 60
            start_min = max(
                shift_start_min, _ceil_minutes_from_midnight(day.now)
            )
            if start_min >= end_min:
                continue
        except (KeyError, ValueError):
            start_min, end_min = 0, 24 * 60

        capacity = st["equipment_capacity"]
        cap_list = (
            [capacity["ONT"], capacity["ROUTER"], capacity["STB"]]
            if isinstance(capacity, dict) else []
        )

        # Restrict both departure and route duration to the remaining shift.
        m.add_vehicle_type(
            num_available=1,
            start_depot=depot,
            end_depot=depot,
            capacity=cap_list,
            tw_early=start_min,
            tw_late=end_min,
            shift_duration=end_min - start_min,
        )
        staff_order.append(st)

    if not staff_order:
        return _empty_plan(date, plan_version, day.now, orders_d, "NO_QUALIFIED_STAFF")

    logger.info(f"Staff in solver: {len(staff_order)}, clients: {len(client_to_order)}, vehicle types: {len(m.vehicle_types)}")

    # ---- 5. Матрицы расстояний / длительности ------------------------------
    n_loc = len(m.locations)
    source_ids = (
        [sc["service_center_id"] for sc in sc_d]
        + [orders_d[i]["building_id"] for i in client_to_order]
    )
    m_idx = [_mat_idx(sid) for sid in source_ids]
    matrix_indices = [idx for idx in m_idx if idx is not None]

    if len(matrix_indices) != n_loc:
        logger.warning("Не все точки найдены в матрице — использую fallback")
        base_travel_seconds = _fallback_matrix(source_ids)
        distances_raw = base_travel_seconds
    else:
        base_travel_seconds = [
            [matrix.durations_sec[matrix_indices[i]][matrix_indices[j]] for j in range(n_loc)]
            for i in range(n_loc)
        ]
        distances_raw = [
            [matrix.distances_m[matrix_indices[i]][matrix_indices[j]] for j in range(n_loc)]
            for i in range(n_loc)
        ]

    factors = matrix.hourly_factors or []
    factors_by_hour = {item.hour: item.factor for item in factors}
    average_factor = sum(
        factors_by_hour.get(hour, 1.0) for hour in range(24)
    ) / 24
    # PyVRP needs a static matrix; final route timings use the factor at each leg's
    # actual departure hour.
    durations = np.array(
        [
            [ceil(seconds * average_factor / 60) for seconds in row]
            for row in base_travel_seconds
        ],
        dtype=np.int64,
    )
    travel_seconds = np.array(base_travel_seconds, dtype=np.int64)
    distances = np.array(distances_raw, dtype=np.int64)

    def leg_duration_seconds(from_idx: int, to_idx: int, departure: datetime) -> int:
        return adjusted_travel_seconds(
            int(travel_seconds[from_idx][to_idx]),
            departure,
            factors,
        )

    data = ProblemData(
        locations=m.locations,
        clients=m.clients,
        depots=m.depots,
        vehicle_types=m.vehicle_types,
        distance_matrices=[distances],  # pyright: ignore[reportArgumentType]
        duration_matrices=[durations],  # pyright: ignore[reportArgumentType]
    )

    # Penalty params: снижаем penalty чтобы солвер агрессивнее искал решения
    penalty = PenaltyParams(
        solutions_between_updates=300,
        penalty_increase=1.34,
        penalty_decrease=0.32,
        target_feasible=0.43,
    )
    params = SolveParams(penalty=penalty)

    result = pyvrp_solve(data, stop=MaxRuntime(max_runtime_seconds), params=params)
    solution = result.best

    # ---- 6. Маппинг результата в Plan --------------------------------------
    routes_out: list[Route] = []
    assigned_order_ids: set[str] = set()

    for rt in solution.routes():
        if not rt.is_feasible():
            continue
        try:
            vt_idx = rt.vehicle_type()
        except AttributeError:
            vt_idx = len(routes_out)
        if vt_idx >= len(staff_order):
            continue

        st = staff_order[vt_idx]

        # Routes start no earlier than either the shift or the planning timestamp.
        shift = st["shift"]
        try:
            sh_s = datetime.strptime(shift["start"], "%H:%M").time()
            shift_start_min = sh_s.hour * 60 + sh_s.minute
        except (KeyError, ValueError):
            shift_start_min = 0
        base_start_min = max(shift_start_min, _ceil_minutes_from_midnight(day.now))

        local_now = day.now.astimezone(BUSINESS_TZ)
        day_date = local_now.date()
        midnight = datetime.combine(
            day_date, datetime.min.time(), tzinfo=BUSINESS_TZ
        )
        try:
            shift_end_time = datetime.strptime(shift["end"], "%H:%M").time()
            shift_end_min = shift_end_time.hour * 60 + shift_end_time.minute
            if shift_end_min <= shift_start_min:
                shift_end_min += 24 * 60
        except (KeyError, ValueError):
            shift_end_min = 24 * 60
        shift_end = midnight + timedelta(minutes=shift_end_min)

        stops: list[Stop] = []
        dep_start_time = midnight + timedelta(minutes=base_start_min)
        stops.append(Stop(
            seq=1, type="DEPOT_START",
            location_id=st["service_center_id"],
            arrival=dep_start_time,
            start=dep_start_time,
            end=dep_start_time,
        ))

        depot_loc_idx = depots[st["service_center_id"]].location
        visit_info: list[tuple[dict, int, int]] = []

        for sa in rt:
            if sa.is_depot():
                continue

            client = m.clients[sa.idx]
            client_loc_idx = client.location
            pos = client_to_order[sa.idx]
            o = orders_d[pos]
            wt = wt_d.get(o["work_type_code"], {})
            service = int(wt.get("duration_min", 60))
            visit_info.append((o, client_loc_idx, service))

        if not visit_info:
            continue

        break_duration = int(shift.get("break_duration_min", 0))
        break_window = shift.get("break_window") or {}
        break_from_str = break_window.get("from", break_window.get("from_"))
        break_to_str = break_window.get("to")
        if not isinstance(break_from_str, str) or not isinstance(break_to_str, str):
            logger.warning("Missing break window for staff %s", st["staff_id"])
            continue
        try:
            break_from_time = datetime.strptime(break_from_str, "%H:%M").time()
            break_to_time = datetime.strptime(break_to_str, "%H:%M").time()
        except (TypeError, ValueError):
            logger.warning("Invalid break window for staff %s", st["staff_id"])
            continue
        break_from = datetime.combine(day_date, break_from_time, tzinfo=BUSINESS_TZ)
        break_to = datetime.combine(day_date, break_to_time, tzinfo=BUSINESS_TZ)
        if break_to <= break_from:
            break_to += timedelta(days=1)

        initial_equipment = dict(st["equipment_start"])
        maximum_equipment = dict(st["equipment_capacity"])
        valid_schedules: list[tuple[datetime, list[Stop]]] = []
        for boundary in range(len(visit_info) + 1):
            feasible = True
            route_stops = [
                Stop(
                    seq=1,
                    type="DEPOT_START",
                    location_id=st["service_center_id"],
                    arrival=dep_start_time,
                    start=dep_start_time,
                    end=dep_start_time,
                    equipment_after=Equipment.model_validate(initial_equipment),
                )
            ]
            cursor_time = dep_start_time
            current_location_idx = depot_loc_idx
            current_location_id = st["service_center_id"]
            inventory = initial_equipment.copy()

            for visit_index in range(len(visit_info) + 1):
                if visit_index == boundary:
                    break_start = max(cursor_time, break_from)
                    if break_start > break_to:
                        feasible = False
                        break
                    break_end = break_start + timedelta(minutes=break_duration)
                    route_stops.append(Stop(
                        seq=len(route_stops) + 1,
                        type="BREAK",
                        location_id=current_location_id,
                        arrival=break_start,
                        start=break_start,
                        end=break_end,
                        travel_sec=0,
                        distance_m=0,
                        equipment_after=Equipment.model_validate(inventory),
                    ))
                    cursor_time = break_end

                if visit_index == len(visit_info):
                    break

                order, order_location_idx, service = visit_info[visit_index]
                required = order.get("required_equipment", {})
                if any(
                    required.get(item, 0) > maximum_equipment.get(item, 0)
                    for item in ("ONT", "ROUTER", "STB")
                ):
                    feasible = False
                    break

                if any(
                    inventory.get(item, 0) < required.get(item, 0)
                    for item in ("ONT", "ROUTER", "STB")
                ):
                    restock_candidates = []
                    for center in sc_d:
                        center_id = center["service_center_id"]
                        center_location_idx = depots[center_id].location
                        hours = center["opening_hours"]
                        opens_at = datetime.combine(
                            day_date,
                            datetime.strptime(hours["open"], "%H:%M").time(),
                            tzinfo=BUSINESS_TZ,
                        )
                        closes_at = datetime.combine(
                            day_date,
                            datetime.strptime(hours["close"], "%H:%M").time(),
                            tzinfo=BUSINESS_TZ,
                        )
                        if closes_at <= opens_at:
                            closes_at += timedelta(days=1)
                        travel_to_center = leg_duration_seconds(
                            current_location_idx,
                            center_location_idx,
                            cursor_time,
                        )
                        restock_arrival = cursor_time + timedelta(
                            seconds=travel_to_center
                        )
                        restock_start = max(restock_arrival, opens_at)
                        restock_end = restock_start + timedelta(
                            minutes=int(center["restock_duration_min"])
                        )
                        if restock_end > closes_at:
                            continue
                        travel_to_order = leg_duration_seconds(
                            center_location_idx,
                            order_location_idx,
                            restock_end,
                        )
                        order_arrival = restock_end + timedelta(
                            seconds=travel_to_order
                        )
                        order_start = max(
                            order_arrival,
                            datetime.fromisoformat(order["slot"]["start"]).astimezone(
                                BUSINESS_TZ
                            ),
                        )
                        latest_start = datetime.fromisoformat(
                            order["latest_start"]
                        ).astimezone(BUSINESS_TZ)
                        if order_start <= latest_start:
                            restock_candidates.append(
                                (
                                    order_start,
                                    center_id,
                                    center_location_idx,
                                    restock_arrival,
                                    restock_start,
                                    restock_end,
                                    travel_to_center,
                                    int(distances[current_location_idx][center_location_idx]),
                                    travel_to_order,
                                    int(distances[center_location_idx][order_location_idx]),
                                )
                            )
                    if not restock_candidates:
                        feasible = False
                        break

                    (
                        _,
                        center_id,
                        center_location_idx,
                        restock_arrival,
                        restock_start,
                        restock_end,
                        travel_to_center,
                        distance_to_center,
                        _,
                        _,
                    ) = min(restock_candidates, key=lambda candidate: candidate[0])
                    route_stops.append(Stop(
                        seq=len(route_stops) + 1,
                        type="RESTOCK",
                        location_id=center_id,
                        arrival=restock_arrival,
                        start=restock_start,
                        end=restock_end,
                        travel_sec=travel_to_center,
                        distance_m=distance_to_center,
                        equipment_after=Equipment.model_validate(maximum_equipment),
                    ))
                    cursor_time = restock_end
                    current_location_idx = center_location_idx
                    current_location_id = center_id
                    inventory = maximum_equipment.copy()

                travel_sec = leg_duration_seconds(
                    current_location_idx,
                    order_location_idx,
                    cursor_time,
                )
                distance_m = int(distances[current_location_idx][order_location_idx])
                arrival = cursor_time + timedelta(seconds=travel_sec)
                visit_start = max(
                    arrival,
                    datetime.fromisoformat(order["slot"]["start"]).astimezone(
                        BUSINESS_TZ
                    ),
                )
                if visit_start > datetime.fromisoformat(
                    order["latest_start"]
                ).astimezone(BUSINESS_TZ):
                    feasible = False
                    break
                visit_end = visit_start + timedelta(minutes=service)
                required_profiles = set(wt.get("profiles", []))
                matching_profiles = sorted(
                    required_profiles & set(st.get("profiles", []))
                )
                explanation_parts = [
                    f"Подходящий профиль: {', '.join(matching_profiles)}",
                    f"Технология {order['technology']} поддерживается",
                    (
                        f"переезд от {current_location_id} — "
                        f"{ceil(travel_sec / 60)} мин"
                    ),
                    f"слот соблюден, начало в {visit_start:%H:%M}",
                    f"работа — норматив {service} мин",
                ]
                if order.get("duration_source") == "HISTORY":
                    explanation_parts.append(
                        "для выбора маршрута использована оценка "
                        f"{order['duration_estimate_min']} мин по истории"
                    )
                if order.get("requires_height"):
                    explanation_parts.append("есть допуск к высоте")
                explanation_parts.append("необходимое оборудование доступно")
                inventory = {
                    item: inventory.get(item, 0) - required.get(item, 0)
                    for item in ("ONT", "ROUTER", "STB")
                }
                route_stops.append(Stop(
                    seq=len(route_stops) + 1,
                    type="VISIT",
                    location_id=order["building_id"],
                    order_id=order["order_id"],
                    arrival=arrival,
                    start=visit_start,
                    end=visit_end,
                    travel_sec=travel_sec,
                    distance_m=distance_m,
                    status="PLANNED",
                    equipment_after=Equipment.model_validate(inventory),
                    explanation="; ".join(explanation_parts),
                ))
                cursor_time = visit_end
                current_location_idx = order_location_idx
                current_location_id = order["building_id"]

            if not feasible:
                continue

            return_sec = leg_duration_seconds(
                current_location_idx,
                depot_loc_idx,
                cursor_time,
            )
            return_distance = int(distances[current_location_idx][depot_loc_idx])
            return_time = cursor_time + timedelta(seconds=return_sec)
            if return_time > shift_end:
                continue
            route_stops.append(Stop(
                seq=len(route_stops) + 1,
                type="DEPOT_END",
                location_id=st["service_center_id"],
                arrival=return_time,
                start=return_time,
                end=return_time,
                travel_sec=return_sec,
                distance_m=return_distance,
                equipment_after=Equipment.model_validate(inventory),
            ))
            valid_schedules.append((return_time, route_stops))

        if not valid_schedules:
            continue

        _, stops = min(valid_schedules, key=lambda schedule: schedule[0])
        visits_in_route = sum(stop.type == "VISIT" for stop in stops)
        if not visits_in_route:
            continue

        assigned_order_ids.update(order["order_id"] for order, _, _ in visit_info)
        travel_total = sum(stop.travel_sec or 0 for stop in stops)
        dist_total = sum(stop.distance_m or 0 for stop in stops)
        visits_in_route = len(visit_info)
        work_min_total = sum(service for _, _, service in visit_info)

        routes_out.append(Route(
            staff_id=st["staff_id"],
            team_staff_ids=st.get("team_staff_ids"),
            service_center_id=st["service_center_id"],
            status="ACTIVE",
            stops=stops,
            totals=RouteTotals(
                visits=visits_in_route,
                travel_sec=int(travel_total),
                distance_m=int(dist_total),
                work_min=int(work_min_total),
            ),
        ))

    # ---- 7. Unassigned -----------------------------------------------------
    unassigned: list[UnassignedOrder] = []
    for pos in skipped_prefilter:
        o = orders_d[pos]
        unassigned.append(UnassignedOrder(
            order_id=o["order_id"],
            reason_code="NO_QUALIFIED_STAFF",
            reason_text="Нет сотрудника с нужными профилями/технологиями",
            suggested_action="REASSIGN",
        ))
    for pos, o in enumerate(orders_d):
        if pos in skipped_prefilter:
            continue
        if o["order_id"] not in assigned_order_ids:
            unassigned.append(UnassignedOrder(
                order_id=o["order_id"],
                reason_code="SLOT_UNREACHABLE",
                reason_text="Не удалось встроить в маршрут",
                suggested_action="RESCHEDULE",
            ))

    # ---- 8. Summary --------------------------------------------------------
    summary = PlanSummary(
        orders_total=len(orders_d),
        visits_planned=len(assigned_order_ids),
        unassigned=len(unassigned),
        pgp_orders=0,
        cancelled=0,
        travel_sec_total=sum(
            route.totals.travel_sec or 0
            for route in routes_out
            if route.totals is not None
        ),
    )

    return Plan(
        date=date,
        plan_version=plan_version,
        as_of=day.now,
        routes=routes_out,
        unassigned=unassigned,
        pgp_groups=[],
        cancelled=[],
        alerts=[],
        summary=summary,
    )


def _staff_can_do(order: dict, staff: dict, work_type: dict) -> bool:
    return (
        order["technology"] in staff["technologies"]
        and bool(set(work_type["profiles"]) & set(staff["profiles"]))
        and (
            not order.get("requires_height")
            or staff.get("height_permit", False)
        )
    )


def _minutes(value: str) -> int:
    hour, minute = map(int, value.split(":"))
    return hour * 60 + minute


def _clock_time(minutes: int) -> str:
    return f"{(minutes // 60) % 24:02d}:{minutes % 60:02d}"


def _make_team_staff(first: dict, second: dict) -> dict | None:
    if first["service_center_id"] != second["service_center_id"]:
        return None

    shift_start = max(_minutes(first["shift"]["start"]), _minutes(second["shift"]["start"]))
    first_end = _minutes(first["shift"]["end"])
    second_end = _minutes(second["shift"]["end"])
    if first_end <= _minutes(first["shift"]["start"]):
        first_end += 24 * 60
    if second_end <= _minutes(second["shift"]["start"]):
        second_end += 24 * 60
    shift_end = min(first_end, second_end)
    if shift_end <= shift_start:
        return None

    first_break = first["shift"]["break_window"]
    second_break = second["shift"]["break_window"]
    first_break_start = _minutes(
        first_break.get("from", first_break.get("from_"))
    )
    second_break_start = _minutes(
        second_break.get("from", second_break.get("from_"))
    )
    first_break_end = _minutes(first_break["to"])
    second_break_end = _minutes(second_break["to"])
    if first_break_end <= first_break_start:
        first_break_end += 24 * 60
    if second_break_end <= second_break_start:
        second_break_end += 24 * 60
    break_start = max(first_break_start, second_break_start)
    break_end = min(first_break_end, second_break_end)
    break_duration = max(
        int(first["shift"].get("break_duration_min", 0)),
        int(second["shift"].get("break_duration_min", 0)),
    )
    if break_end - break_start < break_duration:
        return None

    profiles = sorted(set(first["profiles"]) & set(second["profiles"]))
    technologies = sorted(
        set(first["technologies"]) & set(second["technologies"])
    )
    if not profiles or not technologies:
        return None

    equipment_start = {
        item: int(first["equipment_start"].get(item, 0))
        + int(second["equipment_start"].get(item, 0))
        for item in ("ONT", "ROUTER", "STB")
    }
    equipment_capacity = {
        item: int(first["equipment_capacity"].get(item, 0))
        + int(second["equipment_capacity"].get(item, 0))
        for item in ("ONT", "ROUTER", "STB")
    }
    first_id, second_id = sorted((first["staff_id"], second["staff_id"]))
    return {
        **first,
        "staff_id": first_id,
        "team_staff_ids": [first_id, second_id],
        "display_name": f"{first_id} + {second_id}",
        "profiles": profiles,
        "technologies": technologies,
        "height_permit": first.get("height_permit", False)
        and second.get("height_permit", False),
        "shift": {
            "start": _clock_time(shift_start),
            "end": _clock_time(shift_end),
            "break_duration_min": break_duration,
            "break_window": {
                "from": _clock_time(break_start),
                "to": _clock_time(break_end),
            },
        },
        "equipment_start": equipment_start,
        "equipment_capacity": equipment_capacity,
    }


def solve_vrp(
    *,
    date: str,
    day: DayInput,
    orders: list[Order] | list[dict],
    staff: list[Staff] | list[dict],
    work_types: list[WorkType] | list[dict],
    service_centers: list[ServiceCenter] | list[dict],
    matrix: TravelMatrix,
    plan_version: int = 1,
    max_runtime_seconds: int = 30,
) -> Plan:
    orders_data = [_as_dict(order) for order in orders]
    staff_data = [_as_dict(person) for person in staff]
    work_type_data = {
        str(item["code"] if isinstance(item, dict) else item.code): _as_dict(item)
        for item in work_types
    }
    absent = set(day.absent_staff_ids or [])
    available_staff = [
        person for person in staff_data if person["staff_id"] not in absent
    ]
    joint_orders = [
        order
        for order in orders_data
        if order["work_type_code"] == "INST_PRIVATE_VLS"
        and order.get("building_type") == "PRIVATE"
    ]
    remaining_joint = {order["order_id"]: order for order in joint_orders}
    free_staff = {person["staff_id"]: person for person in available_staff}
    joint_routes: list[Route] = []
    joint_unassigned: dict[str, UnassignedOrder] = {}
    team_runtime = max(1, max_runtime_seconds // max(1, len(joint_orders)))

    while remaining_joint:
        work_items = [
            (order, work_type_data[order["work_type_code"]])
            for order in remaining_joint.values()
        ]
        candidates: list[tuple[int, str, str, dict, list[dict]]] = []
        people = sorted(free_staff.values(), key=lambda person: person["staff_id"])
        for first_idx, first in enumerate(people):
            for second in people[first_idx + 1 :]:
                team = _make_team_staff(first, second)
                if team is None:
                    continue
                covered = [
                    order
                    for order, work_type in work_items
                    if _staff_can_do(order, first, work_type)
                    and _staff_can_do(order, second, work_type)
                ]
                if covered:
                    candidates.append(
                        (
                            -len(covered),
                            first["staff_id"],
                            second["staff_id"],
                            team,
                            covered,
                        )
                    )

        if not candidates:
            break
        _, _, _, team, covered = min(candidates, key=lambda item: item[:3])
        covered_ids = {order["order_id"] for order in covered}
        team_plan = _solve_vrp_core(
            date=date,
            day=day,
            orders=covered,
            staff=[team],
            work_types=work_types,
            service_centers=service_centers,
            matrix=matrix,
            plan_version=plan_version,
            max_runtime_seconds=team_runtime,
        )
        joint_routes.extend(team_plan.routes)
        for item in team_plan.unassigned:
            joint_unassigned[item.order_id] = item
        scheduled = {
            stop.order_id
            for route in team_plan.routes
            for stop in route.stops
            if stop.type == "VISIT" and stop.order_id
        }
        for order_id in scheduled:
            remaining_joint.pop(order_id, None)
            joint_unassigned.pop(order_id, None)
        for order_id in covered_ids - scheduled:
            item = next(
                (entry for entry in team_plan.unassigned if entry.order_id == order_id),
                None,
            )
            if item is not None:
                joint_unassigned[order_id] = item
        for staff_id in team["team_staff_ids"]:
            free_staff.pop(staff_id, None)

    for order in remaining_joint.values():
        joint_unassigned[order["order_id"]] = UnassignedOrder(
            order_id=order["order_id"],
            reason_code="NO_QUALIFIED_STAFF",
            reason_text=(
                "Для установки в частном секторе с ВЛС нужны два доступных "
                "квалифицированных сотрудника одной бригады"
            ),
            suggested_action="ESCALATE",
        )

    joint_ids = {order["order_id"] for order in joint_orders}
    ordinary_orders = [
        order for order in orders_data if order["order_id"] not in joint_ids
    ]
    groups: dict[tuple[str, ...], list[dict]] = {}
    ordinary_unassigned: list[UnassignedOrder] = []
    for order in ordinary_orders:
        work_type = work_type_data.get(order["work_type_code"], {})
        eligible_staff_ids = tuple(
            person["staff_id"]
            for person in sorted(
                free_staff.values(), key=lambda item: item["staff_id"]
            )
            if _staff_can_do(order, person, work_type)
        )
        if not eligible_staff_ids:
            ordinary_unassigned.append(
                UnassignedOrder(
                    order_id=order["order_id"],
                    reason_code="NO_QUALIFIED_STAFF",
                    reason_text="Нет доступного сотрудника с нужными допусками",
                    suggested_action="ESCALATE",
                )
            )
            continue
        groups.setdefault(eligible_staff_ids, []).append(order)

    ordered_groups = sorted(
        groups.items(),
        key=lambda item: (
            len(item[0]),
            min(
                datetime.fromisoformat(order["latest_start"])
                for order in item[1]
            ),
            item[0],
        ),
    )
    ordinary_routes: list[Route] = []
    group_runtime = max(
        1,
        max_runtime_seconds // max(1, len(ordered_groups)),
    )
    for eligible_ids, group_orders in ordered_groups:
        eligible_staff = [
            free_staff[staff_id]
            for staff_id in eligible_ids
            if staff_id in free_staff
        ]
        if not eligible_staff:
            ordinary_unassigned.extend(
                UnassignedOrder(
                    order_id=order["order_id"],
                    reason_code="NO_SHIFT_TIME",
                    reason_text=(
                        "Все квалифицированные сотрудники уже заняты "
                        "более приоритетными нарядами"
                    ),
                    suggested_action="RESCHEDULE",
                )
                for order in group_orders
            )
            continue
        group_plan = _solve_vrp_core(
            date=date,
            day=day,
            orders=group_orders,
            staff=eligible_staff,
            work_types=work_types,
            service_centers=service_centers,
            matrix=matrix,
            plan_version=plan_version,
            max_runtime_seconds=group_runtime,
        )
        ordinary_routes.extend(group_plan.routes)
        ordinary_unassigned.extend(group_plan.unassigned)
        assigned_staff_ids = {
            staff_id
            for route in group_plan.routes
            for staff_id in [route.staff_id, *(route.team_staff_ids or [])]
        }
        for staff_id in assigned_staff_ids:
            free_staff.pop(staff_id, None)

    routes = joint_routes + ordinary_routes
    unassigned = list(joint_unassigned.values()) + ordinary_unassigned
    travel_total = sum(
        route.totals.travel_sec or 0 for route in routes if route.totals
    )
    summary = PlanSummary(
        orders_total=len(orders_data),
        visits_planned=sum(
            1
            for route in routes
            for stop in route.stops
            if stop.type == "VISIT"
        ),
        unassigned=len(unassigned),
        pgp_orders=0,
        cancelled=0,
        travel_sec_total=travel_total,
    )
    return Plan(
        date=date,
        plan_version=plan_version,
        as_of=day.now,
        routes=routes,
        unassigned=unassigned,
        pgp_groups=[],
        cancelled=[],
        alerts=[],
        summary=summary,
    )


def _fallback_matrix(source_ids: list[str]) -> list[list[int]]:
    """Если точки нет в матрице — 10 минут на переход."""
    n = len(source_ids)
    return [[0 if i == j else 600 for j in range(n)] for i in range(n)]


def _empty_plan(date, version, now, orders, reason) -> Plan:
    return Plan(
        date=date, plan_version=version, as_of=now,
        routes=[],
        unassigned=[
            UnassignedOrder(
                order_id=orders[i]["order_id"],
                reason_code=reason,
                reason_text="Нет доступных машин",
                suggested_action="ESCALATE",
            )
            for i in range(len(orders))
        ],
        pgp_groups=[], cancelled=[], alerts=[],
        summary=PlanSummary(orders_total=len(orders), visits_planned=0,
                            unassigned=len(orders), pgp_orders=0, cancelled=0),
    )
