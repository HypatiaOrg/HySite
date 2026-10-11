import type {Metadata} from "next";
import {Page, H1, H2, P, Ext, In} from "@/components/text";
import {columns, simbad} from "@/data/about_columns";
import {nea_url} from "@/data/api_targets";

export const metadata: Metadata = {
    title: "About | Hypatia Catalog",
    description: "The columns of the Hypatia Catalog, their units and data sources, and how the catalog handles ionization states and binary stars.",
};

// a row of the column table: label and unit side by side on a phone, with the description beneath;
// three columns on a wider screen
const rowStyle = "grid grid-cols-[auto_1fr] md:grid-cols-[10rem_7rem_1fr] gap-x-6 gap-y-1 py-3 border-b border-hyblue";
const labelStyle = "font-semibold text-hypurple";
const unitStyle = "text-hygrey text-sm md:text-base md:pt-0.5";
const descriptionStyle = "col-span-2 md:col-span-1 text-hygrey";

export default function AboutPage() {
    return (
        <Page>
            <H1 id="about">ABOUT DATA AND HYPATIA</H1>
            <P>
                Below is a table of the column labels used in the Hypatia Catalog, the associated units, and a
                description of the data source, where applicable. (The NASA Exoplanet Archive data{' '}
                <In href={nea_url}>page is here</In>).
            </P>

            <div className="text-lg md:text-xl mb-8" role="table" aria-label="The columns of the Hypatia Catalog">
                <div className={rowStyle + " sticky top-0 bg-white border-b-2 border-hypurple"} role="row">
                    <div className={labelStyle} role="columnheader">Label</div>
                    <div className={unitStyle + " font-semibold"} role="columnheader">Unit</div>
                    <div className={descriptionStyle + " font-semibold hidden md:block"} role="columnheader">Description</div>
                </div>
                {columns.map((column, index) => (
                    <div className={rowStyle} role="row" key={index}>
                        <div className={labelStyle} role="cell">{column.label}</div>
                        <div className={unitStyle} role="cell">{column.unit ?? "—"}</div>
                        <div className={descriptionStyle} role="cell">{column.description}</div>
                    </div>
                ))}
            </div>

            <H2 id="catalogs">The catalogs</H2>
            <P>
                For a complete breakdown of all catalogs (with {'>'} 20 stars) included in the Hypatia Catalog,
                please download{' '}
                <Ext href="https://drive.google.com/file/d/0B6JubEpe8-76YjlBakJydy1OaXM/view?usp=sharing&resourcekey=0-PGfV-0IqRvm6a9Xw5dNCXw">this file</Ext>,
                the components of which can be found in Hinkel et al.
                (<Ext href="https://ui.adsabs.harvard.edu/abs/2014AJ....148...54H/">2014</Ext>,{' '}
                <Ext href="https://ui.adsabs.harvard.edu/abs/2016ApJS..226....4H/">2016</Ext>, and{' '}
                <Ext href="https://ui.adsabs.harvard.edu/abs/2017ApJ...848...34H/">2017</Ext>). In the header,
                “S/N” is signal-to-noise report by the literature source, “λ Range” is the wavelength coverage,
                “Stellar Atmo” is the stellar atmospheric model, “Eq. Width” is the package used to determine the
                equivalent width, “CoG or SF” designates whether the group used a curve-of-growth or spectral
                fitting technique where the package is specified in the former case, the “Solar Scale” is the solar
                normalization used by that group (differential analysis is cited where applicable), and “Num. of
                Fe I/II lines” lists the number of Fe I and Fe II lines. While this accumulation of telescope
                information, reduction packages, and overall technique was done with the best intentions, errors
                may arise so please check the original source for verification. Please email{' '}
                <Ext href="mailto:hypatiacatalog@gmail.com">hypatiacatalog@gmail.com</Ext> with any questions or
                concerns.
            </P>

            <H2 id="ionization-states">Ionization states</H2>
            <P>
                Per the ionization states, while some catalogs measured only one ionization state when reporting
                an abundance determination, a number of catalogs combined the abundances from multiple ionization
                states. In Hypatia, an abundance of [X/Fe] means that a catalog measured the neutral state, a
                combination of neutral and ionized state(s), or it was not specified. Whenever a catalog
                specifically mentioned it was only measuring the singly ionized state, we demarcate it as [X II/Fe].
            </P>

            <H2 id="binary-stars">Binary stars</H2>
            <P>
                The handling of binary stellar systems has been updated (Oct 2021). Now, if each component has a
                unique {simbad} name and separable stellar spectra, then the abundances from both stars can be
                found within the Hypatia Catalog.
            </P>

            <H2 id="the-name">Hypatia of Alexandria</H2>
            <P>
                Finally, the Hypatia Catalog was named for Hypatia of Alexandria, one of the first known female
                astronomers. She was strong-minded, independent, and well respected by both the people and local
                officials. Socrates Scholasticus once said of her, “For all men on account of her extraordinary
                dignity and virtue admired her the more.” For more information, please go to{' '}
                <Ext href="https://www.nataliehinkel.com/hypatia-catalog.html">this page,</Ext> where more
                resources can be found.
            </P>
        </Page>
    );
}
