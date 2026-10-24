# SkipQ — backend

SkipQ lets diners at GreenLeaf Kopitiam order and pay from their phones, and
lets vendors receive and manage those orders without a counter queue. This
repository is the REST API; the React client lives in the frontend repository.

Frontend: https://github.com/ICT381/ict381-2026-t02-tma-frontend-xxingyao

## Prerequisites

- Python 3.10 or later
- MongoDB running locally on port 27017

## Install

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configure

```bash
cp .env.example .env
```

Adjust `.env` if your MongoDB is elsewhere. The application reads the database
host and name from the environment, so it can be pointed at a test database
without changing code.

| Variable | Default | Purpose |
| --- | --- | --- |
| `MONGODB_DB` | `skipq` | Database name |
| `MONGODB_HOST` | `127.0.0.1` | MongoDB host |
| `MONGODB_PORT` | `27017` | MongoDB port |
| `SECRET_KEY` | *(dev value)* | Flask secret |

## Seed

```bash
python db_seed/seed.py
```

Drops the SkipQ collections and reseeds, so it is safe to run repeatedly.

### Seeded accounts

Every account uses the password **`Password1!`**

| Email | Role | Notes |
| --- | --- | --- |
| `weiling@skipq.test` | Diner | Has orders across several statuses |
| `kumar@skipq.test` | Diner | A second diner, for scope checks |
| `ahhock@skipq.test` | Vendor | Ah Hock Chicken Rice — trading, one sold-out item |
| `meixiang@skipq.test` | Vendor | Mei Xiang Laksa — **not** accepting orders |
| `tanglin@skipq.test` | Vendor | Tanglin Table — trading, restaurant |

## Run

```bash
./start.sh
```

Serves on `http://127.0.0.1:5000`. There is no homepage: `/` returns 404
because SkipQ is an API consumed by the React client.

## API

Every endpoint returns JSON. Obtain a token, then send it as HTTP Basic auth
with the account's email as the username.

```bash
curl -s -X POST http://127.0.0.1:5000/api/user/gettoken \
  -H "Content-Type: application/json" \
  -d '{"email":"weiling@skipq.test","password":"Password1!"}'

curl -s -u 'weiling@skipq.test:<token>' http://127.0.0.1:5000/api/diner/stalls
```

| Method | Path | Persona | Purpose |
| --- | --- | --- | --- |
| POST | `/api/user/gettoken` | any | Exchange credentials for a token |
| GET | `/api/diner/stalls` | Diner | Every stall, trading or closed |
| GET | `/api/diner/stalls/<id>/menu` | Diner | One stall and its menu |
| POST | `/api/diner/orders` | Diner | Place an order |
| GET | `/api/diner/orders` | Diner | The caller's own orders |
| GET | `/api/diner/orders/<id>` | Diner | One of the caller's own orders |
| POST | `/api/diner/orders/<id>/pay` | Diner | Pay for an order |
| GET | `/api/diner/notifications` | Diner | Unread notifications |
| POST | `/api/diner/notifications/read` | Diner | Mark the caller's notifications as read |
| GET | `/api/vendor/stall` | Vendor | The caller's own stall |
| PATCH | `/api/vendor/stall` | Vendor | Open or close the stall |
| GET | `/api/vendor/menu` | Vendor | The caller's own menu |
| POST | `/api/vendor/menu` | Vendor | Add a menu item |
| PATCH | `/api/vendor/menu/<id>` | Vendor | Edit a menu item |
| PATCH | `/api/vendor/menu/<id>/availability` | Vendor | Mark sold out or restock |
| GET | `/api/vendor/orders` | Vendor | Orders at the caller's stall |
| PATCH | `/api/vendor/orders/<id>/status` | Vendor | Advance or reject an order |
| GET | `/api/vendor/dashboard` | Vendor | Today's takings, top items, sold-out |

### Status codes

| Code | Means |
| --- | --- |
| 200 | A successful read or update |
| 201 | A resource was created: an order, a payment, a menu item |
| 400 | The request was malformed, or a value was out of range |
| 401 | No valid token |
| 403 | The caller's role or scope does not allow the action |
| 404 | No such record or endpoint |
| 409 | A business rule refused the action in the state it was attempted |

## Tests

```bash
python -m pytest                     # 94 tests: the unit and functional suites
python -m pytest tests/unit          # 73 tests, no MongoDB server required
python -m pytest tests/functional    # 21 tests, requires MongoDB
```

`pytest.ini` deselects the `browser` marker by default, so the plain `pytest`
run needs neither server. The browser test is run on its own, below.

## Browser test (Question 6a)

Needs the backend on :5000, the frontend on :3000 and a freshly seeded database.

```bash
playwright install chromium
pytest tests/playwright -m browser -q
```

It is excluded from the default `pytest` run, which needs neither server.

## Performance test (Question 6b)

```bash
mkdir -p q6-performance
locust -f tests/stress/locustfile.py --host http://127.0.0.1:5000 \
       --headless -u 20 -r 5 -t 60s --csv q6-performance/vendor-orders
```

The run output the report cites is committed under `q6-performance/`.

## Screencast

The narrated demonstration is in `q7-screencast/`.
