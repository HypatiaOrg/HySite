import Link from 'next/link';
import Image from 'next/image';
import {getHomeData} from "@/data/fetch_data";
import {DEBUG} from "@/data/api_targets";
import hypatiaLogo from "@/public/hypatialogo2.png";
import {AbundancesHist} from "@/components/image";
import {scatter_url, help_url, about_url, credits_url, about_api_url} from "@/data/api_targets";


const linkStyle = "text-hyred hover:text-hypurple hover:bg-hyyellow hover:underline"
const homeGrid = "bg-white grid grid-cols-16";
const paragraphStyle = "text-hygrey col-span-14 col-start-2 indent-12 pt-4";

export default async function Home() {
    const counts = await getHomeData();
    if (DEBUG) {
        console.log("Home page counts:", counts);
    }
    return (
        <>
            <div className="px-8 bg-radial-[at_50%_75%] from-hyyellow via-yellow-500 to-yellow-600 to-90%">
                <div className="max-w-6xl mx-auto py-4 w-full md:flex flex-row md:items-center md:justify-between">
                    <div className="flex flex-row justify-center items-center">
                        <Image
                            src={hypatiaLogo}
                            width="350"
                            height="350"
                            alt="Hyptia Catalog Logo"
                        />
                    </div>
                    <div className="flex flex-col items-center text-center md:justify-center md:items-start md:text-left">
                        <h1 className="text-6xl font-bold text-hypurple">Hypatia Catalog Database</h1>
                        <h2 className="text-2xl font-semibold text-hyred">
                            Explore stellar abundance data for
                        </h2>
                        <ul className="list-inside list-inline ml-4">
                            <li><b> {counts['stars'].toLocaleString()} </b> stars,</li>
                            <li><b> {counts['stars_with_planets'].toLocaleString()} </b> of which host planets and </li>
                            <li><b> {counts['stars_multistar'].toLocaleString()} </b> of which are in multistar systems, </li>
                            <li><b> {counts['elements'].toLocaleString()} </b> elements and species, </li>
                            <li><b> {counts['catalogs'].toLocaleString()} </b> catalogs, and </li>
                            <li><b> {counts['abundances'].toLocaleString()} </b> abundance measurements. </li>
                        </ul>
                        <div className="text-hyred  border-hyred border-solid border-2 rounded-lg p-4 mt-4 text-2xl hover:bg-hygrey hover:border-hypurple hover:text-hyyellow">
                            <Link href={scatter_url}>Get Started »</Link>
                        </div>
                    </div>
                </div>
            </div>
            <div className={homeGrid}>
                <div className={paragraphStyle}>
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
                    or through the terminal via
                    <Link href={about_api_url}>our API</Link>
                    for use in external plotting routines and data analysis.
                </div>
                <p className={paragraphStyle}>
                    Help and documentation about the plots, tables,
                    and advanced controls within the Hypatia Catalog Database
                    can be found on the
                    <Link href={help_url} className={linkStyle}> Help </Link>
                    page in the top right corner.
                    More detailed information about the data, properties,
                    individual literature sources, and decisions within the Hypatia Catalog
                    are featured on the
                    <Link href={about_url} className={linkStyle}> About </Link>
                    page. Thank yous and acknowledgments to be included in published papers can be found under
                    <Link href={credits_url} className={linkStyle}> Acknowledgements</Link>.
                    Finally, for any website or data updates, issues, or corrections, please email
                    <Link href="mailto:hypatiacatalog@gmail.com" className={linkStyle}> hypatiacatalog@gmail.com</Link>.
                </p>
                <br/>
                <p className={paragraphStyle}>
                    A detailed description of the Hypatia Catalog can be found in
                    <Link href="http://adsabs.harvard.edu/abs/2014AJ....148...54H" className={linkStyle}> Hinkel et al. (2014)</Link>.
                    The Hypatia Catalog and Hypatia Catalog Database will continue to be routinely updated
                    in order to incorporate the most recent stellar abundance data published within the literature.
                </p>
            </div>
            <div>
                <div className="relative h-[28rem] w-full">
                    <AbundancesHist/>
                </div>
                <div className={homeGrid}>
                    <p className="text-hyblue bg-hypurple col-span-14 col-start-2 indent-12 pt-4">
                        Number of stars for which each element abundance has been measured as of June 2022.
                        Every star in the Hypatia Catalog has at least [Fe/H] and one other element.
                    </p>
                </div>
            </div>
        </>
    );
}
