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
    # the Next.js frontend: the home page, with the counts from the API (the sample database has planet hosts)
    ("/", "Hypatia Catalog"),
    ("/", "/_next/static/"),
    ("/", "planet hosts"),
    # the Help page (ported 2026-10-11), and its old web2py address, which nginx redirects to it
    ("/help", "GETTING STARTED"),
    ("/help", "/_next/static/"),
    ("/hypatia/default/help", "/_next/static/"),
    # the About page (ported 2026-10-11): the column table and the old address
    ("/about", "ABOUT DATA AND HYPATIA"),
    ("/about", "Henry-Draper catalog name"),
    ("/hypatia/default/about", "/_next/static/"),
    # the Acknowledgements and API pages (ported 2026-10-11); /api was web2py's, now it is Next.js's
    ("/acknowledgements", "ACKNOWLEDGMENTS"),
    ("/hypatia/default/credits", "/_next/static/"),
    ("/api", "Hypatia Catalog API"),
    ("/api", "/_next/static/"),
    # the plot pages (ported 2026-10-11): the page, its old address, and the data the page fetches through
    # its route handler (frontend/app/data), posted as JSON the way the page does
    ("/scatter", "/_next/static/"),
    ("/targets", "/_next/static/"),
    ("/hist", "/_next/static/"),
    ("/hypatia/default/launch", "/_next/static/"),
    ("/hypatia/default/targets", "/_next/static/"),
    ("/hypatia/default/hist", "/_next/static/"),
    ("/data/scatter", "json", {"xaxis1": "Fe", "yaxis1": "Si"}),
    # changed settings change the plot: the axis label the API returns
    ("/data/scatter", "[Ca/H]", {"xaxis1": "Ca", "xaxis2": "H", "yaxis1": "Ti", "yaxis2": "H", "xaxislog": "true"}),
    ("/data/targets", "json", {"xaxis1": "Fe", "yaxis1": "Si", "show_all": "true", "show_thin_disk": "true"}),
    ("/data/hist", "json", {"xaxis1": "Fe"}),
    ("/data/table", "star_id", {"tablecols": "names,Fe,C"}),
    # the density page: the default data, then its own settings changed (bin sizes by keyword and by number,
    # another colour scale, the marginal histograms off)
    ("/density", "/_next/static/"),
    ("/hypatia/default/density", "/_next/static/"),
    ("/data/density", "json", {"xaxis1": "Fe", "yaxis1": "Si", "show_xyhist": "true"}),
    ("/data/density", '"mode": "error"', {"xaxis1": "Fe", "yaxis1": "Si", "xhist_bin_size": "error", "yhist_bin_size": "0.05",
                                          "color_pallet": "Viridis", "show_xyhist": "false"}),
    # the NEA page (ported 2026-10-11), the last web2py page
    ("/nea", "NASA Exoplanet Archive"),
    ("/hypatia/default/nea", "/_next/static/"),
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
    # the frontend API's density data (api.web2py.density): the points, the bins of each axis, the colours
    ("/hypatia/api/frontend/density/?xaxis1=Fe&yaxis1=Si", "json"),
]


def large_request_checks(base_url: str) -> list[tuple]:
    """The largest requests the plot and table pages make: every catalog selected, and a long pasted
    star list. The page posts these to its route handler, which passes them to the API in a URL inside
    the network (gunicorn allows any length; nginx once failed above 4 KB). A page URL with the same
    settings (a shared link) must be answered too: nginx and Node allow 64 KB."""
    catalog_ids = [catalog["id"] for catalog in json.loads(fetch(base_url + "/hypatia/api/v2/catalog/")[1])]
    # the test star (38 Vir) plus 999 more names: about 12 KB, a realistic paste from a target list
    star_list = "; ".join([TEST_STAR] + [f"HIP {number}" for number in range(1, 1000)])
    return [
        ("/data/scatter", "json", {"catalogs": ";".join(catalog_ids), "cat_action": "only"}),
        ("/data/scatter", "json", {"star_list": star_list, "star_action": "only"}),
        # the table of those stars
        ("/data/table", "38 Vir", {"star_list": star_list, "star_action": "only", "tablecols": "names,Fe"}),
        # the same star list in a page URL
        ("/scatter?" + urllib.parse.urlencode({"star_list": star_list, "star_action": "only"}), "/_next/static/"),
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
