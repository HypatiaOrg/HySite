import type {NextConfig} from "next";

// The pages' addresses on the web2py frontend (until October 2026, nginx/default.conf for the hosts),
// redirected to the pages here; a plot page's settings in the query come along
const oldPages: Array<[string, string]> = [
    ["help", "/help"],
    ["about", "/about"],
    ["credits", "/acknowledgements"],
    ["nea", "/nea"],
    ["launch", "/launch"],
    ["targets", "/targets"],
    ["hist", "/hist"],
    ["density", "/density"],
];

const nextConfig: NextConfig = {
    async redirects() {
        return [
            ...oldPages.map(([old, destination]) => ({
                source: `/hypatia/default/${old}`,
                destination,
                permanent: true,
            })),
            // anything else of the old frontend's: the home page
            {source: "/hypatia/default/:path*", destination: "/", permanent: true},
            {source: "/hypatia", destination: "/", permanent: true},
        ];
    },
    // the server and only the files it needs, for the Docker image (Dockerfile)
    output: "standalone",
};

export default nextConfig;
