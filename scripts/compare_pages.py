#!/usr/bin/env python3
"""Capture every page and API response of a running HySite, and compare two captures.

    python3 scripts/compare_pages.py capture http://localhost:8081 before.json
    ...change something, or deploy...
    python3 scripts/compare_pages.py capture http://localhost:8081 after.json
    python3 scripts/compare_pages.py compare before.json after.json

Evidence that a change (an upgrade, a refactor, a deploy) changed nothing it should not have: every
frontend page, every API endpoint, the table and its CSV export, the largest requests the pages make
(every catalog selected, a 1000-star list), all in one browser-like session. The parts that differ on
every request anyway (session keys, form keys, web2py component ids, dates, the host name) are
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
STAR_LIST = "; ".join([TEST_STAR] + [f"HIP {number}" for number in range(1, 1000)])

# a path, or (path, form data to POST); "catalogs": None is replaced by every catalog id
REQUESTS = [
    # frontend pages
    "/", "/hypatia/default/help", "/hypatia/default/about", "/hypatia/default/nea", "/hypatia/default/credits",
    "/hypatia/default/launch", "/hypatia/default/graph.load",
    "/hypatia/default/dropdown.load?id=xaxis&value1=Fe&value2=H&log=True",
    "/hypatia/default/hist", "/hypatia/default/graph_hist.load",
    "/hypatia/default/targets", "/hypatia/default/graph_targets.load",
    "/hypatia/default/table", "/hypatia/default/table.load",
    "/hypatia/default/table.csv/hypatia.csv?download=true", "/hypatia/default/table.tsv/hypatia.tsv?download=true",
    ("/hypatia/default/graph.load", PLOT_SETTINGS), "/hypatia/default/table.load",
    # after a scatter change, the targets plot must still have data (issue #40)
    "/hypatia/default/targets", "/hypatia/default/graph_targets.load",
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
    NEW_SESSION, "/hypatia/default/launch",
    ("/hypatia/default/graph.load", {"cat_action": "only", **CHECKBOXES, "catalogs": None}),
    ("/hypatia/default/graph.load", {"star_list": STAR_LIST, "star_action": "only", **CHECKBOXES}),
    "/hypatia/default/table.load",
]
DROPPED_HEADERS = {"date", "set-cookie", "content-length", "expires", "last-modified", "etag", "server",
                   "connection", "keep-alive", "transfer-encoding"}


def normalise(text: str) -> str:
    text = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "<uuid>", text)
    text = re.sub(r'"p\d+"', '"<id>"', text)                            # Bokeh model ids
    text = re.sub(r'(_formkey|session_id_\w+)[^"&\s]*', r"\1<x>", text)  # web2py form and session keys
    text = re.sub(r'id="c\d{10,}"', 'id="c<id>"', text)                 # web2py component ids
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
                form["catalogs"] = catalog_ids
            data = urllib.parse.urlencode(form, doseq=True).encode()
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                   "X-Requested-With": "XMLHttpRequest"} if data else {}
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


def compare(path_a: str, path_b: str, context_lines: int = 12) -> int:
    with open(path_a) as file_a, open(path_b) as file_b:
        a, b = json.load(file_a), json.load(file_b)
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
