import requests, json
r = requests.get('http://localhost:8080/openapi.json')
d = r.json()
paths = d.get('paths', {})
for path, methods in paths.items():
    verbs = list(methods.keys())
    print(f'{verbs} {path}')
