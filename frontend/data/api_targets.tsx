// Where the pages get their data. Both settings are read when the server runs (compose.yaml), not
// when the site is built, so one image serves the test stack and production alike.
export const DEBUG = process.env.DEBUG === 'true'
// how long a fetched API response is reused before it is fetched again
export const revalidate_seconds = 120

// the API, from the server: the API container directly (API_BASE_SERVER), or a local stack through nginx
export function apiBaseURL() {
    const baseURL = (process.env.API_BASE_SERVER ?? "http://localhost/") + "hypatia/api/frontend/";
    if (DEBUG) {
        console.log("Using API base URL:", baseURL);
    }
    return baseURL;
}

// the homepage plot, drawn from the database when the API container starts
export const abundances_plot_url = "/hypatia/api/static/plots/abundances.png";

// The pages. Those still served by web2py are under /hypatia/default; a page moves to its own
// path when it is ported here, and nginx redirects the old path (nginx/default.conf).
const url_prefix = "/hypatia/default";
export const scatter_url = "/scatter";
export const targets_url = "/targets";
export const hist_url = "/hist";
export const plot_urls = [scatter_url, targets_url, hist_url];
export const density_url = url_prefix + "/density";
export const help_url = "/help";
export const about_url = "/about";
export const nea_url =  url_prefix + "/nea";
export const credits_url = "/acknowledgements";
export const about_api_url = "/api";
