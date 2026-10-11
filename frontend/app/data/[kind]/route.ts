// The route the pages fetch their data through: the browser sends a page's settings here, and this asks
// the API inside the network (API_BASE_SERVER), where a long query is allowed. The public nginx only lets
// GET through to the API, and a star list can make the settings longer than a URL, so the browser POSTs.
import {NextRequest} from "next/server";
import {apiBaseURL} from "@/lib/config";

// the API's frontend endpoints a page may ask for
const PLOT_KINDS = new Set(["scatter", "targets", "hist", "density"]);
const FORM_KINDS = new Set(["table"]);

export async function POST(request: NextRequest, context: {params: Promise<{kind: string}>}) {
    const {kind} = await context.params;
    if (!PLOT_KINDS.has(kind) && !FORM_KINDS.has(kind)) {
        return new Response("Unknown data kind", {status: 404});
    }
    let settings: Record<string, string>;
    try {
        settings = await request.json();
    } catch {
        return new Response("The settings must be a JSON object", {status: 400});
    }
    const form = new URLSearchParams();
    for (const [name, value] of Object.entries(settings)) {
        if (typeof value === "string") form.set(name, value);
    }
    const url = apiBaseURL() + kind + "/";
    // the plot endpoints take their settings as a query (gunicorn allows any length); the table takes a form
    const upstream = PLOT_KINDS.has(kind)
        ? await fetch(url + "?" + form.toString(), {cache: "no-store"})
        : await fetch(url, {method: "POST", body: form, cache: "no-store"});
    const headers = new Headers({"Content-Type": upstream.headers.get("Content-Type") ?? "application/json"});
    // a table download comes back as the file it is
    const disposition = upstream.headers.get("Content-Disposition");
    if (disposition) headers.set("Content-Disposition", disposition);
    return new Response(upstream.body, {status: upstream.status, headers});
}
