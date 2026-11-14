"""Сравнивает raw orders vs _flat_to_order."""
import sys, json
sys.path.insert(0, 'backend')

orders_all = json.load(open('backend/data/orders.json'))
orders = [o for o in orders_all if o['slot']['start'].startswith('2026-11-14')]

# Check required_equipment distribution
eq_dist = {}
for o in orders:
    eq = (o['required_equipment']['ONT'], o['required_equipment']['ROUTER'], o['required_equipment']['STB'])
    eq_dist[eq] = eq_dist.get(eq, 0) + 1

print("Required equipment distribution:")
for eq, cnt in sorted(eq_dist.items()):
    print(f"  ONT={eq[0]}, ROUTER={eq[1]}, STB={eq[2]}: {cnt} orders")

# Check first 3 orders
print("\nFirst 3 orders:")
for o in orders[:3]:
    print(f"  {o['order_id']}: {o['required_equipment']}")
