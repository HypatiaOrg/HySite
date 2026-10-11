# The Next.js frontend

The website's pages, being moved here from `frontend-web2py` one page at a time. nginx
(`nginx/default.conf`) sends `/` here and the pages still under `/hypatia/default/` to web2py.
The pages get their data from the API (`backend`) at `/hypatia/api/frontend/`.

Porting a page: write it under `app/(USERSETTINGS)/<name>/page.tsx`, point its link in
`data/api_targets.tsx` at the new path, redirect the old `/hypatia/default/<name>` address in
`nginx/default.conf`, and add the page to `scripts/smoke_test.py` and `scripts/compare_pages.py`.

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

## The style page

`/style` (not in the menu) shows every piece of the site on one page: the six named colors with a picker
to try other values against everything at once, the headings, paragraphs, links, buttons and the table.
It answers only while `DEBUG` is true. To remove it for good, delete `app/(USERSETTINGS)/style/` and
`components/palette.tsx`.

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
