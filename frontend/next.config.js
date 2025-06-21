module.exports = {
    async redirects() {
        return [
            // Basic redirect
            {
                source: '/hypatia/default/about',
                destination: '/about',
                permanent: true,
            },
            {
                source: '/hypatia/default/credits',
                destination: '/acknowledgements',
                permanent: true,
            },
            {
                source: '/hypatia/default/help',
                destination: '/help',
                permanent: true,
            },
            {
                source: '/hypatia/default/nea',
                destination: '/nea',
                permanent: true,
            },
            //Wildcard path matching
            {
                source: '/hypatia/default/:launch',
                destination: '/:launch',
                permanent: true,
            },
            {
                source: '/hypatia',
                destination: '/',
                permanent: true,
            },
        ]
    },
    output: 'standalone',
}
