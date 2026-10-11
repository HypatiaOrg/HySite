# The Next.js frontend

The website's pages, ported from the web2py frontend (`frontend-web2py`) in October 2026. Both
frontends run on the same API (`backend`, at `/hypatia/api/frontend/`): nginx (`nginx/default.conf`)
serves web2py at hypatiacatalog.com and this frontend at new.hypatiacatalog.com, for people to try it
before it takes over. For testing, the port picks the frontend: this one on nginx's port 80
(http://localhost/), web2py on 8082 (http://localhost:8082/); on this host every old
`/hypatia/default/` address redirects to the page here.

A new page: write it under `app/<name>/page.tsx`, link it from `lib/urls.ts`
and the menu (`components/Header.tsx`), and add it to `scripts/smoke_test.py` and `scripts/compare_pages.py`.

## The plot pages

`/scatter`, `/targets` and `/hist` (`components/plot/PlotPage.tsx`) hold their settings in React state
and in the page URL, under the API's own names (`lib/settings.ts`), so a plot is a link to share and
the menu carries the settings from one plot page to the next. The API's `settings/` endpoint is the
model: defaults, toggles and choices. A change posts the settings as JSON to `/data/<kind>`
(`app/data/[kind]/route.ts`), which asks the API inside the network, where a long star list fits in
a URL; the figure (`components/plot/figures.ts`, from `models/plot_plotly.py`) is drawn by plotly.js,
loaded only on these pages. The form is `components/settings/`, the table `components/table/`. Non-component code is in `lib/`
(the settings model, the API types and fetchers, the page paths), page content in `content/`.

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
It answers only while `DEBUG` is true. To remove it for good, delete `app/style/` and
`components/Palette.tsx` and `components/StyleSamples.tsx`.

## Versions

`package.json` holds the ranges to follow (`^16` for Next.js: a new major version is a decision,
like a new Python minor version). `package-lock.json` is not in git: the weekly update job
(`scripts/refresh_versions.py`) writes it with the newest versions inside the pinned Node image,
tests the site and deploys it, so it matches `requirements.lock` for the Python services. Without
a lock file, `npm install` and the Docker build resolve the newest allowed versions.

```bash
npm run lint         # ESLint: the Next.js and React rules
npm run typecheck    # TypeScript
npm test             # Vitest: the settings model and the figures (also run by the Docker build)
npm run format       # Prettier (format:check only checks)
```
