"""VRP-решатель. Возвращает Plan — pyvrp 0.14 compatible."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Iterable

import numpy as np
from pyvrp import ProblemData, Depot, solve as pyvrp_solve
from pyvrp.stop import MaxRuntime

from api.app.models import (
    Plan, Route, Stop, RouteTotals, PlanSummary,
    UnassignedOrder, DayInput, Order, Staff, WorkType,
    ServiceCenter, TravelMatrix,
)

logger = logging.getLogger(__name__)


def _as_dict(obj):
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return vars(obj)


def _minutes_from_midnight(dt: datetime) -> int:
    """Минуты от полуночи начала дня."""
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return int((dt - midnight).total_seconds() // 60)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Вход в солвер
# ---------------------------------------------------------------------------

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

    # Какого размера capacity (для delivery)
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
        service_min = int(wt.get("duration_min", 60))

        # Временные окна — минуты от полуночи
        slot = o.get("slot") or {}
        try:
            s = datetime.fromisoformat(slot["start"])
            e = datetime.fromisoformat(slot["end"])
            latest = datetime.fromisoformat(o["latest_start"])
            tw_early = _minutes_from_midnight(s)
            tw_late = _minutes_from_midnight(min(e, latest))
        except (KeyError, ValueError, TypeError):
            tw_early, tw_late = 0, 24 * 60

        tw_early = max(tw_early, 0)
        tw_late = max(tw_late, tw_early + 1)

        # delivery должен совпадать по длине с capacity vehicle_type
        delivery = [1] + [0] * (cap_len - 1)
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
            start_min = sh_s.hour * 60 + sh_s.minute
            end_min = sh_e.hour * 60 + sh_e.minute
            if end_min <= start_min:
                end_min += 24 * 60
        except (KeyError, ValueError):
            start_min, end_min = 0, 24 * 60

        cap = st["equipment_capacity"]
        cap_list = [cap["ONT"], cap["ROUTER"], cap["STB"]] if isinstance(cap, dict) else []

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
        return _empty_plan(date, plan_version, day.now, orders_d, skipped_prefilter, "NO_QUALIFIED_STAFF")

    # ---- 5. Матрицы расстояний / длительности ------------------------------
    n_loc = len(m.locations)
    source_ids = (
        [sc["service_center_id"] for sc in sc_d]
        + [orders_d[i]["building_id"] for i in client_to_order]
    )
    m_idx = [_mat_idx(sid) for sid in source_ids]

    if any(x is None for x in m_idx):
        logger.warning("Не все точки найдены в матрице — использую fallback")
        durations_raw = _fallback_matrix(source_ids, matrix)
        distances_raw = durations_raw
    else:
        # duration_matrix должен быть в МИНУТАХ (service_duration тоже в минутах)
        durations_raw = [
            [matrix.durations_sec[m_idx[i]][m_idx[j]] // 60 for j in range(n_loc)]
            for i in range(n_loc)
        ]
        distances_raw = [
            [matrix.distances_m[m_idx[i]][m_idx[j]] for j in range(n_loc)]
            for i in range(n_loc)
        ]

    durations = np.array(durations_raw, dtype=int)
    distances = np.array(distances_raw, dtype=int)

    data = ProblemData(
        locations=m.locations,
        clients=m.clients,
        depots=m.depots,
        vehicle_types=m.vehicle_types,
        distance_matrices=[distances],
        duration_matrices=[durations],
    )

    result = pyvrp_solve(data, stop=MaxRuntime(max_runtime_seconds))
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

        # начало смены — минуты от полуночи
        shift = st["shift"]
        try:
            sh_s = datetime.strptime(shift["start"], "%H:%M").time()
            base_start_min = sh_s.hour * 60 + sh_s.minute
        except (KeyError, ValueError):
            base_start_min = 0

        # day.now — aware datetime, берём дату
        day_date = day.now.date()
        midnight = datetime(day_date.year, day_date.month, day_date.day, tzinfo=day.now.tzinfo)

        stops: list[Stop] = []
        seq = 1

        # DEPOT_START
        dep_start_time = midnight + timedelta(minutes=base_start_min)
        stops.append(Stop(
            seq=seq, type="DEPOT_START",
            location_id=st["service_center_id"],
            arrival=_iso(dep_start_time),
            start=_iso(dep_start_time),
            end=_iso(dep_start_time),
        ))
        seq += 1

        travel_total = 0
        dist_total = 0
        cur_time_min = base_start_min
        depot_loc_idx = depots[st["service_center_id"]].location
        prev_location_idx = depot_loc_idx
        visits_in_route = 0
        work_min_total = 0

        for sa in rt:
            # ScheduledActivity: depot или client
            if sa.is_depot():
                # DEPOT_END — последняя остановка
                trav_back = int(durations[prev_location_idx][depot_loc_idx])
                dist_back = int(distances[prev_location_idx][depot_loc_idx])
                travel_total += int(trav_back)
                dist_total += int(dist_back)
                arrival_end = int(cur_time_min + trav_back // 60)
                dep_end_time = midnight + timedelta(minutes=arrival_end)
                stops.append(Stop(
                    seq=seq, type="DEPOT_END",
                    location_id=st["service_center_id"],
                    arrival=_iso(dep_end_time),
                    start=_iso(dep_end_time),
                    end=_iso(dep_end_time),
                    travel_sec=trav_back,
                    distance_m=dist_back,
                ))
                continue

            # Клиент
            client = m.clients[sa.idx]
            client_loc_idx = client.location  # index в m.locations
            pos = client_to_order[sa.idx]
            o = orders_d[pos]

            trav = int(durations[prev_location_idx][client_loc_idx])
            dist = int(distances[prev_location_idx][client_loc_idx])
            travel_total += trav
            dist_total += dist
            arrival = int(cur_time_min + trav // 60)

            wt = wt_d.get(o["work_type_code"], {})
            service = int(wt.get("duration_min", 60))
            start = arrival
            end = int(start + service)

            stop_time = midnight + timedelta(minutes=start)
            stops.append(Stop(
                seq=seq, type="VISIT",
                location_id=o["building_id"],
                order_id=o["order_id"],
                arrival=_iso(midnight + timedelta(minutes=arrival)),
                start=_iso(stop_time),
                end=_iso(midnight + timedelta(minutes=end)),
                travel_sec=int(trav),
                distance_m=int(dist),
                status="PLANNED",
            ))
            seq += 1
            assigned_order_ids.add(o["order_id"])
            visits_in_route += 1
            work_min_total += service
            prev_location_idx = client_loc_idx
            cur_time_min = end

        routes_out.append(Route(
            staff_id=st["staff_id"],
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
        travel_sec_total=sum(r.totals.travel_sec or 0 for r in routes_out),
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


def _fallback_matrix(source_ids: list[str], matrix: TravelMatrix) -> list[list[int]]:
    """Если точки нет в матрице — 10 минут на переход."""
    n = len(source_ids)
    return [[0 if i == j else 600 for j in range(n)] for i in range(n)]


def _empty_plan(date, version, now, orders, skipped, reason) -> Plan:
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
