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
    return findBaseURL() + "hypatia/api/web2py/";
}

// Specific API locations for the Hypatia Catalog pages
export function homeAPI() {
    return apiBaseURL() + "home/";
}

