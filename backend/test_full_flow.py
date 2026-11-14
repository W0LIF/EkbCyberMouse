"""Полный тест flow: reference -> day -> plan -> events -> get plan."""
import json
import requests
import sys

BASE = "http://localhost:8080/api/v1"
DATA = "data"

def log(msg):
    print(f"  {msg}")

def check(status_code, expected, desc):
    if status_code == expected:
        log(f"OK [{status_code}] {desc}")
    else:
        log(f"FAIL [{status_code}] expected {expected} - {desc}")
        sys.exit(1)

def main():
    # Step 1: Health
    log("1. Health check")
    r = requests.get(f"{BASE}/health")
    check(r.status_code, 200, "health")
    log(f"   team={r.json().get('team')}, version={r.json().get('version')}")

    # Step 2: Load reference
    log("2. Load reference data")
    with open(f"{DATA}/service_centers.json") as f:
        sc = json.load(f)
    with open(f"{DATA}/staff.json") as f:
        staff = json.load(f)
    with open(f"{DATA}/access_nodes.json") as f:
        an = json.load(f)
    with open(f"{DATA}/work_types.json") as f:
        wt = json.load(f)

    ref_payload = {
        "service_centers": sc,
        "staff": staff,
        "access_nodes": an,
        "work_types": wt,
    }
    r = requests.put(f"{BASE}/reference", json=ref_payload)
    check(r.status_code, 200, "reference loaded")
    log(f"   counts={r.json().get('counts')}")

    # Step 3: Load travel matrix
    log("3. Load travel matrix")
    with open(f"{DATA}/travel_matrix.json") as f:
        matrix = json.load(f)
    r = requests.put(f"{BASE}/reference/travel-matrix", json=matrix)
    check(r.status_code, 200, "travel matrix loaded")
    log(f"   points={r.json().get('counts', {}).get('points')}")

    # Step 4: Load day
    log("4. Load day orders")
    with open(f"{DATA}/orders.json") as f:
        all_orders = json.load(f)
    # Filter orders for the test date
    orders = [o for o in all_orders if o["slot"]["start"].startswith("2026-11-14")]
    log(f"   Total orders in file: {len(all_orders)}, for 2026-11-14: {len(orders)}")
    day_payload = {
        "date": "2026-11-14",
        "now": "2026-11-14T08:30:00+05:00",
        "orders": orders,
        "absent_staff_ids": [],
    }
    r = requests.put(f"{BASE}/days/2026-11-14", json=day_payload)
    check(r.status_code, 200, "day loaded")
    log(f"   orders={r.json().get('counts', {}).get('orders')}")

    # Step 5: Build plan
    log("5. Build initial plan")
    r = requests.post(f"{BASE}/days/2026-11-14/plan")
    check(r.status_code, 200, "plan built")
    plan = r.json()
    log(f"   version={plan['plan_version']}, routes={len(plan['routes'])}")
    log(f"   visits={plan['summary']['visits_planned'] if plan['summary'] else 0}")
    log(f"   unassigned={plan['summary']['unassigned'] if plan['summary'] else 0}")

    # Step 6: Get plan
    log("6. Get plan")
    r = requests.get(f"{BASE}/days/2026-11-14/plan")
    check(r.status_code, 200, "get plan")
    plan2 = r.json()
    check(plan2['plan_version'], plan['plan_version'], "plan version matches")
    log(f"   version={plan2['plan_version']}")

    # Step 7: Try rebuild plan before events (should rebuild, 200)
    log("7. Try rebuild plan before events (should be 200)")
    r = requests.post(f"{BASE}/days/2026-11-14/plan")
    check(r.status_code, 200, "200 on rebuild before events")
    log(f"   version={r.json().get('plan_version')}")

    # Step 8: Send ORDER_CANCELLED event
    log("8. Send ORDER_CANCELLED event")
    order_id = None
    for route in plan['routes']:
        for stop in route['stops']:
            if stop['type'] == 'VISIT' and stop.get('order_id'):
                order_id = stop['order_id']
                break
        if order_id:
            break

    if order_id:
        cancel_event = {
            "event_id": "EV-20261114-0001",
            "type": "ORDER_CANCELLED",
            "timestamp": "2026-11-14T09:15:00+05:00",
            "order_id": order_id,
            "reason": "NOT_CONFIRMED",
        }
        r = requests.post(f"{BASE}/days/2026-11-14/events", json=cancel_event)
        check(r.status_code, 200, "ORDER_CANCELLED processed")
        result = r.json()
        log(f"   accepted={result['accepted']}, duplicate={result['duplicate']}, version={result['plan_version']}")
        log(f"   message={result.get('message')}")

        r2 = requests.get(f"{BASE}/days/2026-11-14/plan")
        plan3 = r2.json()
        log(f"   new version={plan3['plan_version']}, cancelled={len(plan3['cancelled'])}")
        if plan3['cancelled']:
            log(f"   cancelled orders: {[c['order_id'] for c in plan3['cancelled']]}")
    else:
        log("   SKIP - no orders in routes")

    # Step 9: Send duplicate event (should be 200 with duplicate=true)
    log("9. Send duplicate event")
    if order_id:
        dup_event = {
            "event_id": "EV-20261114-0001",
            "type": "ORDER_CANCELLED",
            "timestamp": "2026-11-14T09:15:00+05:00",
            "order_id": order_id,
            "reason": "NOT_CONFIRMED",
        }
        r = requests.post(f"{BASE}/days/2026-11-14/events", json=dup_event)
        check(r.status_code, 200, "duplicate accepted")
        result = r.json()
        check(result['duplicate'], True, "duplicate=true")
        log(f"   message={result.get('message')}")

    # Step 10: Send TIME_TICK event
    log("10. Send TIME_TICK event")
    tick_event = {
        "event_id": "EV-20261114-0002",
        "type": "TIME_TICK",
        "timestamp": "2026-11-14T10:00:00+05:00",
    }
    r = requests.post(f"{BASE}/days/2026-11-14/events", json=tick_event)
    check(r.status_code, 200, "TIME_TICK processed")
    result = r.json()
    log(f"   accepted={result['accepted']}, version={result['plan_version']}")
    log(f"   new_alerts={len(result.get('new_alerts') or [])}")
    if result.get('new_alerts'):
        for a in result['new_alerts']:
            log(f"     alert: type={a['type']}, status={a['status']}, message={a['message'][:80]}")

    # Step 11: Check all alerts in plan
    log("11. Check alerts in plan")
    r = requests.get(f"{BASE}/days/2026-11-14/plan")
    plan_final = r.json()
    alerts = plan_final.get('alerts', [])
    log(f"   total alerts: {len(alerts)}")
    for a in alerts[:5]:
        log(f"     alert: type={a['type']}, status={a['status']}, order_id={a.get('order_id')}, message={a['message'][:80]}")

    # Step 12: Send STAFF_UNAVAILABLE event
    log("12. Send STAFF_UNAVAILABLE event")
    if plan['routes']:
        staff_id = plan['routes'][0]['staff_id']
        su_event = {
            "event_id": "EV-20261114-0003",
            "type": "STAFF_UNAVAILABLE",
            "timestamp": "2026-11-14T11:00:00+05:00",
            "staff_id": staff_id,
            "until": "2026-11-14T14:00:00+05:00",
            "reason": "VEHICLE_BREAKDOWN",
        }
        r = requests.post(f"{BASE}/days/2026-11-14/events", json=su_event)
        check(r.status_code, 200, "STAFF_UNAVAILABLE processed")
        result = r.json()
        log(f"   accepted={result['accepted']}, version={result['plan_version']}")
        log(f"   changed_staff_ids={result.get('changed_staff_ids')}")

        r2 = requests.get(f"{BASE}/days/2026-11-14/plan")
        plan_su = r2.json()
        for route in plan_su['routes']:
            if route['staff_id'] == staff_id:
                log(f"   route {staff_id}: status={route['status']}, stops={len(route['stops'])}")
    else:
        log("   SKIP - no routes")

    # Step 13: Send NEW_ORDER event (timestamp 12:00, after STAFF_UNAVAILABLE 11:00)
    log("13. Send NEW_ORDER event")
    new_order = {
        "order_id": "ORD-20261114-9999",
        "work_type_code": "REPAIR",
        "technology": "PON",
        "building_id": "B-00001",
        "address": "г. Екатеринбург, тестовый адрес",
        "lat": 56.8380,
        "lon": 60.6000,
        "building_type": "MKD",
        "requires_height": False,
        "access_node_id": "AN-0001",
        "registered_at": "2026-11-14T11:30:00+05:00",
        "slot": {"start": "2026-11-14T14:00:00+05:00", "end": "2026-11-14T16:00:00+05:00"},
        "latest_start": "2026-11-14T14:10:00+05:00",
        "deadline": "2026-11-14T15:30:00+05:00",
        "required_equipment": {"ONT": 1, "ROUTER": 0, "STB": 0},
        "is_repeat": False,
    }
    new_order_event = {
        "event_id": "EV-20261114-0004",
        "type": "NEW_ORDER",
        "timestamp": "2026-11-14T12:00:00+05:00",
        "order": new_order,
    }
    r = requests.post(f"{BASE}/days/2026-11-14/events", json=new_order_event)
    check(r.status_code, 200, "NEW_ORDER processed")
    result = r.json()
    log(f"   accepted={result['accepted']}, version={result['plan_version']}")
    log(f"   message={result.get('message')}")

    # Final plan check
    log("14. Final plan summary")
    r = requests.get(f"{BASE}/days/2026-11-14/plan")
    plan_final2 = r.json()
    log(f"   version={plan_final2['plan_version']}")
    log(f"   routes={len(plan_final2['routes'])}")
    for route in plan_final2['routes'][:3]:
        visits = sum(1 for s in route['stops'] if s['type'] == 'VISIT')
        log(f"   route {route['staff_id']}: status={route['status']}, visits={visits}")
    log(f"   unassigned={len(plan_final2['unassigned'])}")
    log(f"   cancelled={len(plan_final2['cancelled'])}")
    log(f"   pgp_groups={len(plan_final2['pgp_groups'])}")
    log(f"   alerts={len(plan_final2['alerts'])}")

    log("\n=== ALL TESTS PASSED ===")

if __name__ == "__main__":
    main()
