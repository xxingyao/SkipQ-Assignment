# SkipQ — frontend

The React client for SkipQ, a web application for ordering food from hawker and
food-court stalls without queueing. It renders every screen from the JSON the
SkipQ REST API returns; it holds no data of its own.

The API lives in the backend repository:
https://github.com/ICT381/ict381-2026-t02-tma-backend-xxingyao

## Prerequisites

- Node.js 18 or newer
- The SkipQ backend running, with its database seeded

## Install

```bash
npm install
```

## Point it at the API

The API's address is read from the environment in one place, `src/api/client.js`.

```bash
cp .env.example .env
```

`.env` holds a single line:

REACT_APP_API_URL=http://127.0.0.1:5000


Change it if the backend runs elsewhere. Create React App reads `.env` only at
start-up, so restart the dev server after editing it.

## Run

```bash
npm start
```

The application opens at http://localhost:3000.

Sign in with any account the backend's seed script creates — they are listed in
the backend `README.md`. A diner lands on the stall list; a stall owner lands on
their order board.

## How it is put together

| Path | What it owns |
| --- | --- |
| `src/api/client.js` | The API's base URL, the token on every request, and turning a refusal into an `ApiError` |
| `src/api/endpoints.js` | The API surface, one named function per endpoint |
| `src/api/useRequest.js` | Whether a request is in flight, the refusal if one came back, and preventing a second submit of the same action |
| `src/auth/AuthContext.js` | The signed-in session |
| `src/auth/RequireRole.js` | Which persona may reach which route |
| `src/domain/orderActions.js` | Which actions a vendor is offered for an order in a given state |
| `src/Pages/diner/` | The diner's screens |
| `src/Pages/vendor/` | The stall owner's screens |

## Screencast

The narrated demonstration is in the backend repository: q7-screencast/question 7a.mp4