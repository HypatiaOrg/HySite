#!/usr/bin/env python3
"""Check that a running HySite answers its main pages and API endpoints.

    python scripts/smoke_test.py http://localhost:8081

Waits up to --wait seconds for the site to come up, then requests each URL below through nginx
and checks the status code and the content. Exits with 1 if anything fails. Standard library only.

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
CHECKS = [
    # web2py frontend pages
    ("/", "Hypatia Catalog"),
    # each .load fragment needs the session settings its parent page makes, so the parent comes first
    ("/hypatia/default/launch", "Hypatia Catalog"),
    ("/hypatia/default/graph.load", "Bokeh"),
    ("/hypatia/default/hist", "Hypatia Catalog"),
    ("/hypatia/default/graph_hist.load", "Bokeh"),
    ("/hypatia/default/targets", "Hypatia Catalog"),
    ("/hypatia/default/graph_targets.load", "Bokeh"),
    ("/hypatia/default/table", "<table"),
    ("/hypatia/default/table.load", "<table"),
    # changing the plot settings (last, since the new settings stay in the session) must change the plot. Posted the way the page's jQuery does it, with
    # "; charset=UTF-8" in the content type, which some web2py versions ignored (HySite issue #32)
    ("/hypatia/default/graph.load", "[Ca/H]", {"xaxis1": "Ca", "xaxis2": "H", "yaxis1": "Ti", "yaxis2": "H"}),
    # homepage plot, drawn from the database when the backend starts
    ("/hypatia/api/static/plots/abundances.png", "png"),
    # Django API
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
]


def large_request_checks(base_url: str) -> list[tuple]:
    """The largest requests the plot and table pages make: every catalog selected, and a long pasted
    star list. web2py passes these settings to the API in the URL, which once failed above 4 KB."""
    catalog_ids = [catalog["id"] for catalog in json.loads(fetch(base_url + "/hypatia/api/v2/catalog/")[1])]
    # the test star (38 Vir) plus 999 more names: about 12 KB, a realistic paste from a target list
    star_list = "; ".join([TEST_STAR] + [f"HIP {number}" for number in range(1, 1000)])
    checkboxes = {"show_all": "on", "show_thin_disk": "on", "show_thick_disk": "on"}
    return [
        # a new visitor, so settings saved by the checks above don't change these results
        (NEW_SESSION, None),
        ("/hypatia/default/launch", "Hypatia Catalog"),
        ("/hypatia/default/graph.load", "Bokeh", {"catalogs": catalog_ids, "cat_action": "only", **checkboxes}),
        # the star list is entered with the plot settings, then the table shows those stars
        ("/hypatia/default/graph.load", '$("#graph")', {"star_list": star_list, "star_action": "only", **checkboxes}),
        ("/hypatia/default/table.load", "38 Vir"),
    ]


# keeps the web2py session cookie between requests, like a browser
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
# in the list of checks: forget the session cookie, like a new visitor
NEW_SESSION = "new session"


def new_session() -> None:
    global opener
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def fetch(url: str, data: dict | None = None) -> tuple[int, bytes]:
    request = urllib.request.Request(url)
    if data is not None:
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
    status, body = fetch(base_url + path, data)
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
    parser.add_argument("base_url", help="for example http://localhost:8081")
    parser.add_argument("--wait", type=int, default=300, help="seconds to wait for the site to start")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    if not wait_for_site(base_url, args.wait):
        sys.exit(f"The site at {base_url} did not start within {args.wait} seconds")
    failures = 0
    checks = CHECKS + large_request_checks(base_url)
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
