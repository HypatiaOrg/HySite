#!/usr/bin/env python3
"""Check that a running HySite answers its main pages and API endpoints.

    python scripts/smoke_test.py next http://localhost:8081      # the Next.js frontend
    python scripts/smoke_test.py web2py http://localhost:8083    # the web2py frontend

Two frontends share the API (nginx/default.conf): hypatiacatalog.com is the web2py frontend and
new.hypatiacatalog.com the Next.js one; for testing, the Next.js frontend is on nginx's port 80 and
web2py on its port 8082 (8081 and 8083 in the test stack). The first argument says which frontend's
pages to check; the API checks are the same for both.

Waits up to --wait seconds for the site to come up, then requests each URL through nginx and checks
the status code and the content. Exits with 1 if anything fails. Standard library only.

The checks are written for the sample database (mongo/test_data), but all except the
named-star check also pass against the full database.
"""
import argparse
import http.cookiejar
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# a star kept in the sample database by scripts/make_test_data.py (38 Vir); the API matches
# catalog names such as HIP or HD numbers, not common names
TEST_STAR = "HIP 62875"

# (path, what the response must be[, form data to POST]): "json" parses as non-empty JSON, "found" is
# JSON for a star the API found, "png" is an image, any other string must appear in the page
NEXT_CHECKS = [
    # the home page, with the counts from the API (the sample database has planet hosts)
    ("/", "Hypatia Catalog"),
    ("/", "/_next/static/"),
    ("/", "planet hosts"),
    # the text pages, and their web2py addresses, which nginx redirects to them on this host
    ("/help", "GETTING STARTED"),
    ("/hypatia/default/help", "/_next/static/"),
    ("/about", "ABOUT DATA AND HYPATIA"),
    ("/about", "Henry-Draper catalog name"),
    ("/hypatia/default/about", "/_next/static/"),
    ("/acknowledgements", "ACKNOWLEDGMENTS"),
    ("/hypatia/default/credits", "/_next/static/"),
    ("/api", "Hypatia Catalog API"),
    ("/nea", "NASA Exoplanet Archive"),
    ("/hypatia/default/nea", "/_next/static/"),
    ("/hypatia/default/table", "planet hosts"),
    # the plot pages: the page, its old address, and the data the page fetches through its route handler
    # (frontend/app/data), posted as JSON the way the page does
    ("/scatter", "/_next/static/"),
    ("/targets", "/_next/static/"),
    ("/hist", "/_next/static/"),
    ("/density", "/_next/static/"),
    ("/hypatia/default/launch", "/_next/static/"),
    ("/hypatia/default/targets", "/_next/static/"),
    ("/hypatia/default/hist", "/_next/static/"),
    ("/hypatia/default/density", "/_next/static/"),
    ("/data/scatter", "json", {"xaxis1": "Fe", "yaxis1": "Si"}),
    # changed settings change the plot: the axis label the API returns
    ("/data/scatter", "[Ca/H]", {"xaxis1": "Ca", "xaxis2": "H", "yaxis1": "Ti", "yaxis2": "H", "xaxislog": "true"}),
    # up to ten filters (three fixed rows until October 2026): the settings model lists the tenth, and a request
    # with four of them is answered
    ("/hypatia/api/frontend/settings/", "filter10_1"),
    ("/data/scatter", "json", {"xaxis1": "Fe", "yaxis1": "Si", "filter1_1": "teff", "filter1_3": "5000", "filter1_4": "6000",
                               "filter2_1": "dist", "filter2_4": "100", "filter3_1": "Fe", "filter3_3": "-1",
                               "filter4_1": "logg", "filter4_3": "4"}),
    ("/scatter?filter1_1=teff&filter1_3=5000&filter2_1=dist&filter2_4=100&filter3_1=Fe&filter3_3=-1&filter4_1=logg&filter4_3=4",
     "/_next/static/"),
    ("/data/targets", "json", {"xaxis1": "Fe", "yaxis1": "Si", "show_all": "true", "show_thin_disk": "true"}),
    ("/data/hist", "json", {"xaxis1": "Fe"}),
    ("/data/table", "star_id", {"tablecols": "names,Fe,C"}),
    # the density data: the defaults, then its own settings changed (bin sizes by keyword and by number,
    # another colour scale, the marginal histograms off)
    ("/data/density", "json", {"xaxis1": "Fe", "yaxis1": "Si", "show_xyhist": "true"}),
    ("/data/density", '"mode": "error"', {"xaxis1": "Fe", "yaxis1": "Si", "xhist_bin_size": "error", "yhist_bin_size": "0.05",
                                          "color_pallet": "Viridis", "show_xyhist": "false"}),
]

WEB2PY_CHECKS = [
    ("/", "Hypatia Catalog"),
    # each .load fragment needs the session settings its parent page makes, so the parent comes first
    ("/hypatia/default/launch", "Hypatia Catalog"),
    ("/hypatia/default/graph.load", "plotly-graph-div"),
    # the axis labels are drawn at the size the Bokeh plots used (once shipped at 2 pixels: invisible)
    ("/hypatia/default/graph.load", '"tickfont":{"size":16}'),
    ("/hypatia/default/hist", "Hypatia Catalog"),
    ("/hypatia/default/graph_hist.load", "plotly-graph-div"),
    # the histogram page's bin size: a typed width, then the default rule again
    ("/hypatia/default/graph_hist.load", "plotly-graph-div", {"hist_bin_size": "0.5"}),
    ("/hypatia/default/graph_hist.load", "plotly-graph-div", {"hist_bin_size": ""}),
    # the density page (the plotly branch): the plot is a Plotly figure; then its own settings changed
    # (bin sizes by keyword and by number, another colour scale, the marginal histograms off)
    ("/hypatia/default/density", "Hypatia Catalog"),
    ("/hypatia/default/graph_density.load", "plotly-graph-div"),
    ("/hypatia/default/graph_density.load", "plotly-graph-div",
     {"xhist_bin_size": "error", "yhist_bin_size": "0.05", "color_pallet": "Viridis", "toggle_vars": "show_xyhist"}),
    ("/hypatia/default/targets", "Hypatia Catalog"),
    ("/hypatia/default/graph_targets.load", "plotly-graph-div"),
    # the scatter and targets plots with their histograms along the axes (the toggle on, a bin size typed; the
    # top histogram is the trace on the second y axis), then off again
    ("/hypatia/default/graph.load", '"yaxis":"y2"',
     {"show_scatter_hist": "on", "xhist_bin_size": "0.1", "toggle_vars": "show_scatter_hist"}),
    ("/hypatia/default/graph.load", "plotly-graph-div", {"toggle_vars": "show_scatter_hist"}),
    ("/hypatia/default/graph_targets.load", '"yaxis":"y2"',
     {"show_targets_hist": "on", "toggle_vars": "show_targets_hist"}),
    ("/hypatia/default/graph_targets.load", "plotly-graph-div", {"toggle_vars": "show_targets_hist"}),
    ("/hypatia/default/table", "<table"),
    ("/hypatia/default/table.load", "<table"),
    ("/hypatia/default/help", "GETTING STARTED"),
    ("/hypatia/default/about", "ABOUT DATA AND HYPATIA"),
    ("/hypatia/default/credits", "ACKNOWLEDGMENTS"),
    ("/hypatia/default/nea", "NASA Exoplanet Archive"),
    ("/api", "Hypatia Catalog API"),
    # changing the plot settings (last, since the new settings stay in the session) must change the plot. Posted the way the page's jQuery does it, with
    # "; charset=UTF-8" in the content type, which some web2py versions ignored (HySite issue #32)
    # (the axis label "[Ca/H]" as Plotly's HTML writes it, with the slash escaped)
    ("/hypatia/default/graph.load", "[Ca\\u002fH]", {"xaxis1": "Ca", "xaxis2": "H", "yaxis1": "Ti", "yaxis2": "H",
                                                      "toggle_vars": "gridlines,xaxislog,yaxislog"}),
    # after a change on the scatter page, the targets page must still show its default lists (issue #40);
    # with no data the response has no plot
    ("/hypatia/default/targets", "Hypatia Catalog"),
    ("/hypatia/default/graph_targets.load", "plotly-graph-div"),
]

# the API, the same on both hosts
API_CHECKS = [
    # homepage plot, drawn from the database when the backend starts
    ("/hypatia/api/static/plots/abundances.png", "png"),
    ("/hypatia/api/", "Hypatia"),
    ("/hypatia/api/v2/solarnorm/", "json"),
    ("/hypatia/api/v2/element/", "json"),
    ("/hypatia/api/v2/catalog/", "json"),
    ("/hypatia/api/v2/nea/", "json"),
    (f"/hypatia/api/v2/star/?name={urllib.request.quote(TEST_STAR)}", "found"),
    ("/hypatia/api/v2/data/?xaxis1=Fe&yaxis1=Si", "json"),
    ("/hypatia/api/stats/histogram/", "json"),
    ("/hypatia/api/planets/", "json"),
    ("/hypatia/api/metadata/solarnorms/", "json"),
    ("/hypatia/api/db/summary/", "json"),
    ("/hypatia/api/web2py/table/?elements=Fe&elements=C", "json"),
    # the frontend API's density data (api.web2py.density): the points, the bins of each axis, the colours
    ("/hypatia/api/frontend/density/?xaxis1=Fe&yaxis1=Si", "json"),
    ("/hypatia/api/frontend/hist/?xaxis1=Fe&hist_bin_size=error", "json"),
]


def large_request_checks(frontend: str, base_url: str) -> list[tuple]:
    """The largest requests the plot and table pages make: every catalog selected, and a long pasted
    star list. web2py posts them to its own page, which passes them to the API in a URL inside the
    network (gunicorn allows any length; nginx once failed above 4 KB); the Next.js page posts them to
    its route handler, and a page URL with the same settings (a shared link) must be answered too:
    nginx and Node allow 64 KB."""
    catalog_ids = [catalog["id"] for catalog in json.loads(fetch(base_url + "/hypatia/api/v2/catalog/")[1])]
    # the test star (38 Vir) plus 999 more names: about 12 KB, a realistic paste from a target list
    star_list = "; ".join([TEST_STAR] + [f"HIP {number}" for number in range(1, 1000)])
    if frontend == "web2py":
        checkboxes = {"show_all": "on", "show_thin_disk": "on", "show_thick_disk": "on"}
        return [
            # a new visitor, so settings saved by the checks above don't change these results
            (NEW_SESSION, None),
            ("/hypatia/default/launch", "Hypatia Catalog"),
            ("/hypatia/default/graph.load", "plotly-graph-div", {"catalogs": catalog_ids, "cat_action": "only", **checkboxes}),
            # the star list is entered with the plot settings, then the table shows those stars
            ("/hypatia/default/graph.load", '$("#graph")', {"star_list": star_list, "star_action": "only", **checkboxes}),
            ("/hypatia/default/table.load", "38 Vir"),
        ]
    return [
        ("/data/scatter", "json", {"catalogs": ";".join(catalog_ids), "cat_action": "only"}),
        ("/data/scatter", "json", {"star_list": star_list, "star_action": "only"}),
        # the table of those stars
        ("/data/table", "38 Vir", {"star_list": star_list, "star_action": "only", "tablecols": "names,Fe"}),
        # the same star list in a page URL
        ("/scatter?" + urllib.parse.urlencode({"star_list": star_list, "star_action": "only"}), "/_next/static/"),
    ]


# keeps cookies (web2py's session) between requests, like a browser
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
# in the list of checks: forget the session cookie, like a new visitor
NEW_SESSION = "new session"


def new_session() -> None:
    global opener
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def fetch(url: str, data: dict | None = None) -> tuple[int, bytes]:
    request = urllib.request.Request(url)
    if data is not None and "/data/" in url:
        # the Next.js pages post their settings as JSON to their route handler
        request = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
    elif data is not None:
        request = urllib.request.Request(url, data=urllib.parse.urlencode(data, doseq=True).encode(), headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest"})
    try:
        with opener.open(request, timeout=120) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def check(base_url: str, path: str, expect: str, data: dict | None = None) -> str | None:
    """None if the check passes, otherwise what went wrong."""
    try:
        status, body = fetch(base_url + path, data)
    except (urllib.error.URLError, ConnectionError, TimeoutError) as error:
        # e.g. a redirect to an address that is not this site
        return f"no response: {error}"
    if status != 200:
        return f"HTTP {status}: {body[:200]!r}"
    if expect in ("json", "found"):
        try:
            data = json.loads(body)
        except ValueError:
            return f"not JSON: {body[:200]!r}"
        if not data:
            return "empty JSON response"
        # an unknown star still returns JSON, with "status": "not-found"
        if expect == "found" and data[0].get("status") != "found":
            return f"star not found: {body[:200]!r}"
    elif expect == "png":
        if not body.startswith(b"\x89PNG"):
            return "not a PNG image"
    elif expect.encode() not in body:
        return f"{expect!r} not found in the page"
    return None


def wait_for_site(base_url: str, seconds: int) -> bool:
    """Wait until both the frontend and the API answer; they start at different speeds."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if all(fetch(base_url + path)[0] == 200 for path in ("/", "/hypatia/api/")):
                return True
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            pass
        time.sleep(5)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Check a running HySite.")
    parser.add_argument("frontend", choices=["next", "web2py"], help="which frontend the URL serves")
    parser.add_argument("base_url", help="for example http://localhost:8081 (next) or http://localhost:8083 (web2py)")
    parser.add_argument("--wait", type=int, default=300, help="seconds to wait for the site to start")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    if not wait_for_site(base_url, args.wait):
        sys.exit(f"The site at {base_url} did not start within {args.wait} seconds")
    failures = 0
    pages = NEXT_CHECKS if args.frontend == "next" else WEB2PY_CHECKS
    checks = pages + API_CHECKS + large_request_checks(args.frontend, base_url)
    for path, expect, *data in checks:
        if path == NEW_SESSION:
            new_session()
            continue
        start = time.monotonic()
        problem = check(base_url, path, expect, *data)
        label = f"POST {path} {str(data[0])[:60]}" if data else path
        print(f"{'FAIL' if problem else 'ok  '} {time.monotonic() - start:5.1f}s  {label}")
        if problem:
            print(f"       {problem}")
            failures += 1
    total = sum(path != NEW_SESSION for path, *_ in checks)
    print(f"\n{total - failures} of {total} checks passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
