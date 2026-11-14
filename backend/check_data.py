import json
from datetime import datetime

with open('data/orders.json') as f:
    orders = json.load(f)

# Check slot.start dates
dates = {}
for o in orders:
    d = o['slot']['start'][:10]
    dates[d] = dates.get(d, 0) + 1
print('Orders per date:', dates)

# Check staff equipment_capacity
with open('data/staff.json') as f:
    staff = json.load(f)
print('Staff count:', len(staff))
print('First staff equipment_capacity:', staff[0].get('equipment_capacity'))

# Check work_types
with open('data/work_types.json') as f:
    wt = json.load(f)
for w in wt:
    code = w['code']
    print(f'  WT {code}: profiles={w["profiles"]}, duration={w["duration_min"]}min, pgp_relevant={w["pgp_relevant"]}')
