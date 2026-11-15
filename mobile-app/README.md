# Employee route app

Standalone Expo/React Native app for employees to view a day's assigned visits,
navigate to an address, and record customer-call, arrival, and completion actions.

## Run

### Docker Compose

Из корня репозитория запустите весь проект:

```powershell
docker compose up --build
```

Для использования на физическом телефоне укажите в корневом `.env` адрес
компьютера, доступный из локальной сети:

```dotenv
MOBILE_PACKAGER_HOSTNAME=192.168.1.25
MOBILE_API_BASE_URL=http://192.168.1.25:8080/api/v1
```

Замените IP на адрес своего компьютера, перезапустите Compose, затем откройте
QR-код Expo из логов `docker compose logs -f mobile` в Expo Go. Телефон и
компьютер должны быть в одной сети. Compose публикует Metro на порту `8081`.

### Local development

```sh
npm install
npm start
```

Use `npm run android` or `npm run ios` to open an installed simulator/device.
`npm run typecheck` runs TypeScript validation, and `npm run build` typechecks
and exports an Android bundle.

The app reads `EXPO_PUBLIC_API_BASE_URL` at build time. It defaults to
`http://localhost:8080/api/v1`; set it before starting Expo when the API is
running on another host. For a physical phone, `localhost` refers to the phone,
so use the computer's LAN address, for example
`EXPO_PUBLIC_API_BASE_URL=http://192.168.1.25:8080/api/v1`.

The app loads employees from `GET /reference/staff`, then requests the selected
employee's route from
`GET /mobile/days/{date}/routes/{staff_id}`. Route responses may contain a
`visits` array, a `stops` array, or those arrays under `route`; each visit
includes its order ID, address, status, and available time fields (`arrival`,
`start`, and `end`). Route stops with a `type` field are filtered to `VISIT`.

Actions are posted to
`POST /mobile/days/{date}/routes/{staff_id}/visits/{order_id}/actions` with the
selected action and a client-generated UTC `occurred_at` timestamp. The route
is reloaded after the server accepts an action; the app does not optimistically
change visit status.
