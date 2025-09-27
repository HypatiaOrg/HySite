import { PHASE_PRODUCTION_BUILD } from 'next/constants';

export const DEBUG = process.env.DEBUG === 'true'
export const revalidate_seconds = 120


export function findBaseURL() {
    if (process.env.NEXT_PHASE === PHASE_PRODUCTION_BUILD) {
        // The application is building for production (force it to use the cache, building inside a docker container).
        return "http://localhost/";
    } else if (typeof window === 'undefined') {
        // The application is running on the server
        return process.env.API_BASE_SERVER;
    } else {
        // The application is running on the client
        return process.env.NEXT_PUBLIC_API_BASE_CLIENT;
    }
}

// General API locations
export function apiBaseURL() {
    const baseURL = findBaseURL() + "hypatia/api/web2py/";
    if (DEBUG) {
        console.log("Using API base URL:", baseURL);
    }
    return baseURL;
}

// Specific API locations for the Hypatia Catalog pages
export function homeAPI() {
    return apiBaseURL() + "home/";
}


const url_prefix = "/hypatia/default";
export const scatter_url = url_prefix + "/launch";
export const targets_url = url_prefix + "/targets";
export const hist_url = url_prefix + "/hist";
export const help_url =  url_prefix + "/help";
export const about_url =  url_prefix + "/about";
export const credits_url =  url_prefix + "/credits";
export const about_api_url = "/api";
