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

### Blog list pagination

`GET /api/blogs` and authenticated `GET /api/feed` return pages with `items`,
`has_more`, and `next_cursor`. The default page size is 20; `limit` can be set
from 1 to 100. Request the next page by passing the returned cursor, for example
`/api/blogs?limit=20&cursor=...`. `GET /api/blogs` also accepts `author_id` to
list one writer's stories.

### Editing stories and responses

Authors can edit their stories from the story page; signed-in users can edit
their own responses inline. The API exposes authenticated `PATCH /api/blog/{id}`
and `PATCH /api/blog/{blog_id}/comment/{comment_id}` endpoints. Both reject
edits by anyone other than the original author.

### CI checks

The Jenkins pipeline scans checked-out files for secrets with Gitleaks, runs
backend lint and unit tests, then API integration tests against an isolated
PostgreSQL database. It builds separate backend and frontend images and checks
`/api/health` on staging before the approval gate. The secret scan redacts
detected values in logs and fails the build if it finds a match.
Configure Jenkins credentials `docker-hub-pat`, `vm-ssh-key`,
`blog-app-db-password`, and `blog-app-secret-key` before enabling deployments.

### Features

- Explore feed with search and Latest / Popular / Discussed sorting
- Load additional stories with cursor pagination
- Story page with reading progress bar, likes, editable responses, share, and story edit/delete (owner only)
- Sign up, log in, edit profile (JWT stored in `localStorage`)
- Distraction-free editor with live word count, preview, and auto-saved drafts
- Author profiles with stats and follow / unfollow
