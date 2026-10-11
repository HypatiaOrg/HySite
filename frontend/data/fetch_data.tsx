// What the pages fetch from the API on the server, reused for revalidate_seconds
import {DEBUG, revalidate_seconds, apiBaseURL} from "@/data/api_targets";
import type {SettingsSchema} from "@/data/settings";
import type {Summary} from "@/data/summary";

async function getJSON<T>(path: string): Promise<T> {
    const fetchURL = apiBaseURL() + path;
    if (DEBUG) {
        console.log("Fetch from:", fetchURL);
    }
    const res = await fetch(fetchURL, {next: {revalidate: revalidate_seconds}});
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
