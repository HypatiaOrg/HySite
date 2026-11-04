# Working on HySite with an AI coding agent

HySite is the Hypatia Catalog website (hypatiacatalog.com): a web2py frontend, a Django API and a MongoDB
database, run with Docker Compose behind nginx. The README says how the server deploys it and the GitHub
wiki is the documentation. This file is for anyone working in a checkout with an AI agent such as Claude
Code, students included; it records how the project likes work to be done. Personal and machine-specific
notes belong in `CLAUDE.local.md` beside it, which git ignores.

## Who decides what

- **The maintainers** run the site and review every change. Ask them about the code, the server and
  the deployment.
- **The science team** decides everything about the data and everything a visitor reads: which parameters
  the menus offer and in what order; the table's columns and their defaults; the representative errors and
  any other number that stands in for a measurement; the bin rules, ranges and caps of the histograms; the
  colour scales; the solar normalizations; the words of every warning, label, Help, About and API page.
  **Check with them, a lot.** Propose a change with its reason, show it on a running copy of the site (a
  published port or a screenshot), and put *their* words in. Never invent scientific wording and merge it as
  if it were theirs; when you must draft text to keep a page coherent, say so plainly and mark it for
  review. When a sentence is handed to you, use it exactly.
- The science team's choices are kept in two files so they can find them later:
  `backend/hypatia/configs/website_settings.py` (the site's choices: menus, table, defaults, bin rules,
  warning words, colours) and `backend/hypatia/configs/params_units.toml` (one block per parameter: units,
  label, decimals, log, error). A new choice goes there, not into the code that uses it. The frontend reads
  them from the API's settings and summary endpoints and keeps no copies.
- `backend/hypatia/plots/2D_plotly.py` and `2D_plt.py` are the science team's prototypes, kept as examples
  to work from. The site does not import them. Leave them alone.

## Branches, commits, pushing

- Work on a branch named `claude/<topic>` (or `<your-name>/<topic>`), made from the branch a maintainer
  names. Merge it back into that branch with `--no-ff` once it is verified. Maintainers merge into `main`;
  an agent never merges into `main` and never pushes unless asked in so many words.
- One change per commit. The subject is a plain sentence saying what is now true ("The bin size box takes
  the width the histogram has"), then a blank line, then a paragraph on what was wrong and why this is the
  fix. Date a decision when you record one ("the science team's choice, 2026-11-03"). End with the
  `Co-Authored-By` trailer the tool gives you.
- No feature changes without asking. Bug fixes, documentation, tests and upgrades are welcome. Ask before
  changing a beginner-friendly default (`DEBUG` is true by default on purpose).
- Leave a hand-off note when a session ends mid-task: what is done, what is in flight, what the next
  session should do first.

## Verify everything on a running site

The code is baked into the images: rebuild the service you changed before testing it.

- **The test stack** runs against a sample database and needs no credentials:
  `docker compose -p hysite-test --env-file test.env -f compose.yaml -f compose.test.yaml up --build --detach`,
  then `python3 scripts/smoke_test.py http://localhost:8081`. Run the smoke test after every change. Add
  a check for every behaviour you add or fix; check data as data (parse the JSON), not as a substring.
- **A refactor must change nothing.** Capture every page and endpoint before and after with
  `scripts/compare_pages.py` and compare; read every difference and account for it. For a Plotly figure,
  compare the data and layout as objects, not the HTML.
- **The full catalog**, when real value ranges matter: the default stack, `docker compose up --build
  --detach`, with a `.env` that names a database and a read-only user (see `example.env`). Treat those
  credentials as secrets: never print them, never use them for anything but the containers.
- **Anything visual needs a picture.** A layout claim made from markup alone has been wrong before.
  Headless Chromium takes a screenshot of a page, including what ajax loads, with a command such as
  `chromium --headless=new --disable-gpu --hide-scrollbars --window-size=1400,1100 --virtual-time-budget=15000 --screenshot=out.png http://localhost:8081/hypatia/default/density`
  (add `--no-sandbox` inside a container); the agent can then look at the PNG. For clicking, typing and
  reading element positions, use a Playwright tool: the Playwright plugin for Claude Code, or
  `playwright-core` in Node. Keep the screenshots of a review together, dated, in a folder git ignores.
- A bug reported from a browser needs a browser to reproduce; a scripted request can pass while the page
  fails (the Enter-key bug of issue #35 was found that way).
- The agent's own test expectations deserve the same scrutiny as the code: when a check fails, ask whether
  it also fails on the version that works.

## Python

- f-strings for formatting. Single quotes where there is a choice; double quotes only when the string
  holds a single quote.
- The standard library or NumPy for calculations. No pandas, no new dependency for something NumPy does.
- Comments say why, in sentences, and name the decision and its date when the science team or a maintainer
  made one. Docstrings say what a function decides and where its inputs come from (for example "the API
  decided the axes; this only draws").
- Keep a rule in one place. If the frontend and the API both need to know something, the API decides and
  the frontend reads it from an endpoint.

## Where things live

- `backend/api/web2py/`: the API behind the frontend pages. `views.py` the endpoints, `data_process.py`
  the settings parsing and queries, `plots.py` and `density.py` the plot data and the bin rules, `table.py`
  the table, `settings.py` the settings model every frontend reads.
- `backend/hypatia/configs/`: `website_settings.py` and `params_units.toml` (the science team's files),
  `env_load.py` (environment), `file_paths.py`.
- `frontend-web2py/app/`: `controllers/default.py` (the pages and the plot fragments), `models/summary.py`
  (what the frontend reads from the API at start), `models/plot_plotly.py` (the figures; it only draws),
  `views/default/plot_page.html` (the one template behind the four plot pages), `plot_controls.html`,
  `plot.load` (the one plot fragment), `table.load`, `table_options.html`, `dropdown.load`, and the text
  pages `help.html`, `about.html`, `api.html`, `credits.html`.
- `scripts/`: `smoke_test.py`, `compare_pages.py`, `make_test_data.py`, `refresh_versions.py`, the Mongo
  backup and restore scripts. `mongo/test_data/` is the sample database.
- `compose.yaml` and `compose.test.yaml`; `example.env` documents the settings; `test.env` is the test
  stack's.

## Traps

- web2py templates: `{{=x}}` escapes, `{{=XML(x)}}` does not; a `{{# comment }}` is one line only (a second
  line is run as code); models load in file-name order, so a model-level constant from `summary.py` is
  visible inside functions of `plot_plotly.py` but not at its top level; a `.load` fragment such as
  `dropdown.load` needs the variables the page's `LOAD()` passes, so a bare request to it fails, and that
  is not a bug.
- The frontend's session stores only the keys the API's settings model names; a new setting is added to
  the API's `DEFAULTS` or `TOGGLES`, never to the frontend alone.
- Never change a plot's axis range or the data's aspect ratio to make room for decoration.
- Files edited on a mounted folder can end up mode 600 and unreadable in an image: `chmod 644` after edits.
- `pgrep -f` and `pkill -f` from an agent's shell tool match the tool's own shell.
- Everything an agent reads goes to its model provider. Do not read secrets you do not need; redact `.env`
  values when you must look at the file.
