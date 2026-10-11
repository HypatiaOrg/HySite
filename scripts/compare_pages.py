#!/usr/bin/env python3
"""Capture every page and API response of a running HySite, and compare two captures.

    python3 scripts/compare_pages.py capture http://localhost:8081 before.json
    ...change something, or deploy...
    python3 scripts/compare_pages.py capture http://localhost:8081 after.json
    python3 scripts/compare_pages.py compare before.json after.json

Evidence that a change (an upgrade, a refactor, a deploy) changed nothing it should not have: every
frontend page, every API endpoint, the table and its CSV export, the largest requests the pages make
(every catalog selected, a 1000-star list), all in one browser-like session. The parts that differ on
every request anyway (ids, dates, the host name) are
normalised before saving, so two captures of the same site are identical. Standard library only.

A capture is about 45 requests, including heavy ones; it takes a minute or two and the file is large
(hundreds of MB against the full database). Against the live site, the HTTPS wrapper's rate limit allows it.
"""
import argparse
import difflib
import http.cookiejar
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

# a star kept in the sample database (38 Vir), so the capture works on the test stack too
TEST_STAR = "HIP 62875"
NEW_SESSION = "new session"
PLOT_SETTINGS = {"xaxis1": "Ca", "xaxis2": "H", "yaxis1": "Ti", "yaxis2": "H", "zaxis1": "Fe", "zaxis2": "H"}
CHECKBOXES = {"show_all": "on", "show_thin_disk": "on", "show_thick_disk": "on"}
# the density page's own settings: a keyword and a number as bin sizes, another colour scale, and the
# marginal histograms switched off (a toggle listed in toggle_vars but not sent). Nothing the other pages share.
DENSITY_SETTINGS = {"xhist_bin_size": "error", "yhist_bin_size": "0.05", "color_pallet": "Viridis",
                    "show_xyhist": "false", "gridlines": "true"}
STAR_LIST = "; ".join([TEST_STAR] + [f"HIP {number}" for number in range(1, 1000)])

# a path, or (path, form data to POST); "catalogs": None is replaced by every catalog id
REQUESTS = [
    # frontend pages
    "/", "/help", "/about", "/nea", "/acknowledgements",
    # the Next.js plot pages (2026-10-11) and the data they fetch through their route handler (a JSON POST)
    "/scatter", "/targets", "/hist", "/launch?mode=hist", "/hypatia/default/launch",
    ("/data/scatter", {}), ("/data/scatter", PLOT_SETTINGS), ("/data/targets", CHECKBOXES), ("/data/hist", {}),
    # four filters (three fixed rows until October 2026)
    ("/data/scatter", {"filter1_1": "teff", "filter1_3": "5000", "filter1_4": "6000", "filter2_1": "dist", "filter2_4": "100",
                       "filter3_1": "Fe", "filter3_3": "-1", "filter4_1": "logg", "filter4_3": "4"}),
    ("/data/table", {"tablecols": "Fe,C,O,Mg,Si,S,Ca,Ti"}), ("/data/table", {"tablecols": "names,Fe", "format": "csv", "download": "true"}),
    # the density page: the default data, then its own settings changed
    "/density", ("/data/density", {"show_xyhist": "true"}), ("/data/density", DENSITY_SETTINGS),
    "/hypatia/default/not_a_page",
    # API
    "/hypatia/api/", "/hypatia/api/v2/solarnorm/", "/hypatia/api/v2/element/", "/hypatia/api/v2/catalog/",
    "/hypatia/api/v2/nea/", f"/hypatia/api/v2/star/?name={urllib.parse.quote(TEST_STAR)}",
    f"/hypatia/api/v2/composition/?name={urllib.parse.quote(TEST_STAR)}&element=Fe&element=C",
    "/hypatia/api/v2/data/?xaxis1=Fe&yaxis1=Si", "/hypatia/api/v2/data/?xaxis1=Fe&yaxis1=Si&zaxis1=C",
    "/hypatia/api/stats/histogram/", "/hypatia/api/planets/", "/hypatia/api/metadata/solarnorms/",
    "/hypatia/api/db/summary/", "/hypatia/api/web2py/table/?elements=Fe&elements=C",
    "/hypatia/api/web2py/table/?elements=Fe&elements=C&elements=O&elements=Mg&elements=Si&elements=Ti&elements=Ni",
    # the largest requests the pages make: every catalog, a long star list, then the table of those stars
    ("/data/scatter", {"cat_action": "only", "catalogs": None}),
    ("/data/scatter", {"star_list": STAR_LIST, "star_action": "only"}),
    ("/data/table", {"star_list": STAR_LIST, "star_action": "only", "tablecols": "names,Fe"}),
    # the table built by the API (api.web2py.table): every column kind, a targets table, a sort, a download
    "/hypatia/api/web2py/table/?tablecols=names,names_all,planet,stellar,spread,ref,Fe,Fe_II,C,Li"
    "&show_targets=true&show_hwo_tier1=true&sort=Fe&reverse=true&statistic=median&solarnorm=lodders09",
    "/hypatia/api/web2py/table/?tablecols=Fe,C,O,Mg,Si,S,Ca,Ti&format=csv",
    # the density data (api.web2py.density): the defaults, then every bin size rule, the heatmap alone,
    # an element ratio and a stellar parameter as the axes, and a log axis
    "/hypatia/api/frontend/density/?xaxis1=Fe&yaxis1=Si",
    "/hypatia/api/frontend/density/?xaxis1=Fe&xaxis2=C&yaxis1=teff&xhist_bin_size=error&yhist_bin_size=0.05"
    "&color_pallet=Viridis&yaxislog=true",
    # the settings model (api.web2py.settings), under the frontend API's name and its old one
    "/hypatia/api/web2py/settings/",
    "/hypatia/api/frontend/settings/",
    # the API explanation page
    "/api",
]
DROPPED_HEADERS = {"date", "set-cookie", "content-length", "expires", "last-modified", "etag", "server",
                   "connection", "keep-alive", "transfer-encoding"}


def normalise(text: str) -> str:
    text = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "<uuid>", text)
    text = re.sub(r'"p\d+"', '"<id>"', text)                            # Bokeh model ids (captures before 2026-10-11)
    text = re.sub(r"\?_=\d+|\b1[6-9]\d{8}\b", "<time>", text)           # cache busters, unix times
    text = re.sub(r"\b20\d\d-\d\d-\d\d\b|\b\d\d/\d\d/20\d\d\b", "<date>", text)
    text = re.sub(r"https?://[^/\s\"']+/", "http://<host>/", text)
    return text


def capture(base_url: str, out_path: str) -> None:
    opener = new_session()
    catalog_ids = None
    result = {}
    for index, item in enumerate(REQUESTS):
        if item == NEW_SESSION:
            opener = new_session()
            continue
        path, form = (item, None) if isinstance(item, str) else item
        data = None
        if form is not None:
            form = dict(form)
            if "catalogs" in form:
                if catalog_ids is None:
                    catalog_ids = [c["id"] for c in json.loads(opener.open(base_url + "/hypatia/api/v2/catalog/").read())]
                form["catalogs"] = ";".join(catalog_ids)
            if path.startswith("/data/"):
                # the Next.js pages post their settings as JSON to their route handler
                data = json.dumps(form).encode()
            else:
                data = urllib.parse.urlencode(form, doseq=True).encode()
        headers = ({"Content-Type": "application/json"} if path.startswith("/data/") else
                   {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest"}) if data else {}
        request = urllib.request.Request(base_url + path, data=data, headers=headers)
        try:
            with opener.open(request, timeout=600) as response:
                status, body, response_headers = response.status, response.read(), response.headers
        except urllib.error.HTTPError as error:
            status, body, response_headers = error.code, error.read(), error.headers
        key = f"{index:02d} {'POST ' if data else ''}{path}" + (f" {sorted(form)}" if form else "")
        result[key] = {
            "status": status,
            "headers": {k: v for k, v in response_headers.items() if k.lower() not in DROPPED_HEADERS},
            "body": normalise(body.decode(errors="replace")),
        }
        print(f"{status} {key[3:]}", flush=True)
    with open(out_path, "w") as file:
        json.dump(result, file, indent=1, sort_keys=True)
    print(f"{len(result)} responses saved to {out_path}")


def new_session() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def by_request(capture: dict) -> dict:
    """The capture keyed by request instead of position (a repeated request gets a count), so adding a
    request to REQUESTS does not make every later response look different."""
    seen = {}
    result = {}
    for key in sorted(capture):
        request = re.sub(r"^\d+ ", "", key)
        seen[request] = seen.get(request, 0) + 1
        result[request if seen[request] == 1 else f"{request} ({seen[request]})"] = capture[key]
    return result


def compare(path_a: str, path_b: str, context_lines: int = 12) -> int:
    with open(path_a) as file_a, open(path_b) as file_b:
        a, b = by_request(json.load(file_a)), by_request(json.load(file_b))
    same = different = 0
    for key in sorted(set(a) | set(b)):
        x, y = a.get(key), b.get(key)
        if x is not None and y is not None and all(x[k] == y[k] for k in ("status", "headers", "body")):
            same += 1
            continue
        different += 1
        print(f"DIFF {key}: status {x and x['status']} vs {y and y['status']}, "
              f"{x and len(x['body'])} vs {y and len(y['body'])} chars")
        if x is None or y is None:
            continue
        changed_headers = {k: (x["headers"].get(k), y["headers"].get(k))
                           for k in set(x["headers"]) | set(y["headers"]) if x["headers"].get(k) != y["headers"].get(k)}
        if changed_headers:
            print(f"  headers: {changed_headers}")
        diff = difflib.unified_diff(x["body"].splitlines(), y["body"].splitlines(), lineterm="", n=0)
        for line in list(diff)[2:2 + context_lines]:
            print("  " + line[:200])
    print(f"{same} identical, {different} different")
    return 1 if different else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    cap = commands.add_parser("capture", help="fetch every page and save the normalised responses")
    cap.add_argument("base_url", help="for example http://localhost:8081 or https://hypatiacatalog.com")
    cap.add_argument("out_path", help="JSON file to write")
    cmp_ = commands.add_parser("compare", help="compare two captures; exits 1 if they differ")
    cmp_.add_argument("path_a")
    cmp_.add_argument("path_b")
    cmp_.add_argument("--lines", type=int, default=12, help="diff lines to show per differing response")
    args = parser.parse_args()
    if args.command == "capture":
        capture(args.base_url.rstrip("/"), args.out_path)
    else:
        sys.exit(compare(args.path_a, args.path_b, args.lines))


if __name__ == "__main__":
    main()
