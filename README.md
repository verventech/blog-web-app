# blog-web-app

Full-stack blog: **React (Vite) frontend**, **FastAPI backend**, **PostgreSQL**.

## Run with Docker

```bash
cp .env.example .env   # then set SECRET_KEY etc.
docker compose up -d --build
```

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:3000        |
| Backend  | http://localhost:8000/docs   |
| Postgres | localhost:5432               |

The frontend is served by nginx, which proxies `/api/*` to the `backend` service on the
internal Docker network, so no CORS configuration is needed. Change the host port with
`FRONTEND_PORT` in `.env`.

## Frontend development

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173, proxies /api to http://localhost:8000
```

Set `VITE_BACKEND_URL` to point the dev proxy at a different backend.

### Features

- Explore feed with search and Latest / Popular / Discussed sorting
- Story page with reading progress bar, likes, responses, share, and delete (author only)
- Sign up, log in, edit profile (JWT stored in `localStorage`)
- Distraction-free editor with live word count, preview, and auto-saved drafts
- Author profiles with stats and follow / unfollow
