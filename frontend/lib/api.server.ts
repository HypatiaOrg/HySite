// What the pages fetch from the API on the server, reused for revalidateSeconds (server components only)
import {DEBUG, revalidateSeconds, apiBaseURL} from "@/lib/config";
import type {SettingsSchema} from "@/lib/settings";
import type {Summary} from "@/lib/summary";

async function getJSON<T>(path: string): Promise<T> {
    const fetchURL = apiBaseURL() + path;
    if (DEBUG) {
        console.log("Fetch from:", fetchURL);
    }
    const res = await fetch(fetchURL, {next: {revalidate: revalidateSeconds}});
    if (!res.ok) {
        throw new Error(`The API answered ${res.status} for ${path}`);
    }
    return res.json();
}

export const getHomeData = () => getJSON<Record<string, number>>("home/");
// the settings model: every setting's default, kind and choices (api.web2py.settings)
export const getSettingsSchema = () => getJSON<SettingsSchema>("settings/");
// the catalog summary: columns, parameters, catalogs, solar normalizations, elements, target lists
export const getSummary = () => getJSON<Summary>("summary/");
