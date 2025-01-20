import {DEBUG, revalidate_seconds, homeAPI} from "@/data/api_targets";

export const getHomeData = async () => {
    const fetchURL = homeAPI()
    if (DEBUG) {
        console.log("Database Stats Fetch from:", fetchURL)
    }
    const res = await fetch(fetchURL,  { next: { revalidate: revalidate_seconds } })
    const json = await res.json()
    if (DEBUG) {
        console.log("Homepage database counts:", json)
    }
    return json
}