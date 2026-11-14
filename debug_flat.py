"""Проверяем как данные проходят через _flat_to_order и SQL."""
import json
import sys
sys.path.insert(0, 'backend')

from datetime import datetime

orders_all = json.load(open('backend/data/orders.json'))
orders = [o for o in orders_all if o['slot']['start'].startswith('2026-11-14')]
o = orders[0]

def _minutes_from_midnight(dt):
    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return int((dt - midnight).total_seconds() // 60)

s = datetime.fromisoformat(o['slot']['start'])
e = datetime.fromisoformat(o['slot']['end'])
latest = datetime.fromisoformat(o['latest_start'])
tw_early = _minutes_from_midnight(s)
tw_late = _minutes_from_midnight(min(e, latest))

print(f'Order: {o["order_id"]}')
print(f'Slot: {o["slot"]["start"]} to {o["slot"]["end"]}')
print(f'Latest: {o["latest_start"]}')
print(f'tw_early={tw_early}, tw_late={tw_late}')
print(f'Work type: {o["work_type_code"]}')
print(f'Technology: {o["technology"]}')
print(f'Requires height: {o["requires_height"]}')
print(f'Access node: {o["access_node_id"]}')
print(f'Building: {o["building_id"]}')

# Check how many orders have slots that overlap with ANY shift
shifts = [(8*60, 17*60), (9*60, 18*60), (12*60, 21*60)]
overlap_count = 0
for o in orders:
    slot_s = datetime.fromisoformat(o['slot']['start'])
    slot_e = datetime.fromisoformat(o['slot']['end'])
    latest_start = datetime.fromisoformat(o['latest_start'])
    slot_min_start = _minutes_from_midnight(slot_s)
    slot_min_end = _minutes_from_midnight(slot_e)
    latest_min = _minutes_from_midnight(latest_start)
    tw_late = min(slot_min_end, latest_min)
    for sh_s, sh_e in shifts:
        if slot_min_start < sh_e and tw_late >= sh_s:
            overlap_count += 1
            break
print(f'\nOrders overlapping with shifts: {overlap_count}/{len(orders)}')

# Check capacity
print(f'\nRequired equipment: ONT={o["required_equipment"]["ONT"]}, ROUTER={o["required_equipment"]["ROUTER"]}, STB={o["required_equipment"]["STB"]}')
