# The Next.js frontend

The website's pages, being moved here from `frontend-web2py` one page at a time. nginx
(`nginx/default.conf`) sends `/` here and the pages still under `/hypatia/default/` to web2py.
The pages get their data from the API (`backend`) at `/hypatia/api/frontend/`.

## Running it

The whole site, with this frontend built in Docker:

```bash
docker compose --profile api up --build
```

For development with live reloading, run only the API and nginx in Docker and this frontend on the
host (it needs [Node.js](https://nodejs.org/en/download)):

```bash
docker compose --profile api up --detach
cd frontend
npm install
npm run dev        # http://localhost:3000, fetching from the API at http://localhost/
```

`API_BASE_SERVER` is where the server-side fetches go (`http://localhost/` when unset; compose.yaml
sets the API container's address). The browser fetches from the page's own origin. `DEBUG=true`
logs the fetches.

## Versions

`package.json` holds the ranges to follow (`^16` for Next.js: a new major version is a decision,
like a new Python minor version). `package-lock.json` is not in git: the weekly update job
(`scripts/refresh_versions.py`) writes it with the newest versions inside the pinned Node image,
tests the site and deploys it, so it matches `requirements.lock` for the Python services. Without
a lock file, `npm install` and the Docker build resolve the newest allowed versions.

```bash
npm run lint
npm run typecheck
```
