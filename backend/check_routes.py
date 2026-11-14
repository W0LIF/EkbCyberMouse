import traceback
import sys
sys.path.insert(0, '.')

print('Importing reference router...')
try:
    from api.app.routers import reference
    print(f'  reference router: {reference.router}')
    print(f'  routes: {len(reference.router.routes)}')
    for r in reference.router.routes:
        methods = getattr(r, 'methods', set())
        path = getattr(r, 'path', '<unknown>')
        print(f'    {methods} {path}')
except Exception as e:
    traceback.print_exc()

print('\nImporting plan router...')
try:
    from api.app.routers import plan
    print(f'  plan router: {plan.router}')
    print(f'  routes: {len(plan.router.routes)}')
    for r in plan.router.routes:
        methods = getattr(r, 'methods', set())
        path = getattr(r, 'path', '<unknown>')
        print(f'    {methods} {path}')
except Exception as e:
    traceback.print_exc()

print('\nImporting events router...')
try:
    from api.app.routers import events
    print(f'  events router: {events.router}')
    print(f'  routes: {len(events.router.routes)}')
    for r in events.router.routes:
        methods = getattr(r, 'methods', set())
        path = getattr(r, 'path', '<unknown>')
        print(f'    {methods} {path}')
except Exception as e:
    traceback.print_exc()
