// Where the pages get their data. Both settings are read when the server runs (compose.yaml), not
// when the site is built, so one image serves the test stack and production alike.
export const DEBUG = process.env.DEBUG === 'true'
// how long a fetched API response is reused before it is fetched again
export const revalidate_seconds = 120

export function findBaseURL() {
    if (typeof window === 'undefined') {
        // on the server: the API container directly (API_BASE_SERVER), or a local stack through nginx
        return process.env.API_BASE_SERVER ?? "http://localhost/";
    }
    // in the browser: the same origin as the page; nginx routes /hypatia/api/ to the API
    return "/";
}

// General API locations
export function apiBaseURL() {
    const baseURL = findBaseURL() + "hypatia/api/frontend/";
    if (DEBUG) {
        console.log("Using API base URL:", baseURL);
    }
    return baseURL;
}

// Specific API locations for the Hypatia Catalog pages
export function homeAPI() {
    return apiBaseURL() + "home/";
}

// the homepage plot, drawn from the database when the API container starts
export const abundances_plot_url = "/hypatia/api/static/plots/abundances.png";

const url_prefix = "/hypatia/default";
export const scatter_url = url_prefix + "/launch";
export const targets_url = url_prefix + "/targets";
export const hist_url = url_prefix + "/hist";
export const help_url =  url_prefix + "/help";
export const about_url =  url_prefix + "/about";
export const credits_url =  url_prefix + "/credits";
export const about_api_url = "/api";
