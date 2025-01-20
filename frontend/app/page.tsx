import Link from 'next/link';
import Image from 'next/image';
import {getHomeData} from "@/data/fetch_data";


const linkStyle = "text-hyred hover:text-hypurple hover:bg-hyyellow hover:underline"

export default async function Home() {
    const counts = await getHomeData();
    console.log(counts);
    return (
        <>
            <div className="flex flex-row px-8 bg-hyyellow">
                <Image
                    src="/static/hypatialogo2.png"
                    width="350"
                    height="350"
                    alt="Hyptia Catalog Logo"
                />
                <div className="flex flex-col justify-center">
                    <h1 className="text-6xl font-bold text-hypurple">Hypatia Catalog Database</h1>
                    <p>
                        Explore stellar abundance data
                        for <b> {counts['stars'].toLocaleString()} </b> stars,
                        <b> {counts['stars_with_planets'].toLocaleString()} </b> of which host planets
                        and <b>{counts['stars_multistar'].toLocaleString()}</b> of which are in multistar systems,
                        <b> {counts['elements'].toLocaleString()} </b> elements and species,
                        <b> {counts['catalogs'].toLocaleString()} </b> catalogs, and
                        <b> {counts['abundances'].toLocaleString()} </b> abundance measurements.</p>
                    <p>
                        <Link className={linkStyle} href="/scatter">Get Started »</Link>
                    </p>
                </div>
            </div>
            <div className="bg-blue-100">
                <p className='text-hygrey'>
                    The Hypatia Catalog is a multidimensional,
                    amalgamate dataset comprised of stellar elemental abundance measurements
                    for FGKM-type stars within 500 pc of the Sun
                    and all exoplanet host stars regardless of distance.
                    All stellar abundances have been carefully selected
                    from literature sources that measured [Fe/H]
                    and at least one other element.
                    The Hypatia Catalog Database features an interactive table
                    and multiple plotting interfaces that allow easy access
                    and exploration of data within the Hypatia Catalog.
                    In addition, stellar properties and planetary properties,
                    where applicable, have been made available.
                    Data can be downloaded either through the website
                    or through the terminal via <a href="/api">our API</a>
                    for use in external plotting routines and data analysis.
                </p>
                <br/>
                <p className='text-hygrey'>
                    Help and documentation about the plots, tables,
                    and advanced controls within the Hypatia Catalog Database
                    can be found on the
                    <Link href="/help" className={linkStyle}> Help </Link>
                    page in the top right corner.
                    More detailed information about the data, properties,
                    individual literature sources, and decisions within the Hypatia Catalog
                    are featured on the
                    <Link href="/about" className={linkStyle}> About </Link>
                    page. Thank yous and acknowledgments to be included in published papers can be found under
                    <Link href="/acknowledgements" className={linkStyle}> Acknowledgements </Link>.
                    Finally, for any website or data updates, issues, or corrections, please email
                    <Link href="mailto:hypatiacatalog@gmail.com" className={linkStyle}> hypatiacatalog@gmail.com </Link>.
                </p>
                <br/>
                <p className="text-hygrey">
                    A detailed description of the Hypatia Catalog can be found in
                    <Link href="http://adsabs.harvard.edu/abs/2014AJ....148...54H" className={linkStyle}> Hinkel et al. (2014)</Link>.
                    The Hypatia Catalog and Hypatia Catalog Database will continue to be routinely updated
                    in order to incorporate the most recent stellar abundance data published within the literature.
                </p>
                <div className="relative h-[28rem] w-full">
                    <Image
                        src="/static/abundances.png"
                        fill={true}
                        alt="Histogram of the element abundances in the Hypatia Catalog and the number of stars for which each element has been measured."
                    />
                </div>
                <p className="text-hygrey">
                    Number of stars for which each element abundance has been measured as of June 2022.
                    Every star in the Hypatia Catalog has at least [Fe/H] and one other element.
                </p>
            </div>
        </>
    );
}
