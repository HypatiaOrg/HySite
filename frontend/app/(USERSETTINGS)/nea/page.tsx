import type {Metadata} from "next";
import Image from "next/image";
import {Page, H1, H2, P, Ext, In} from "@/components/text";
import {scatter_url, help_url, about_url} from "@/data/api_targets";
import dexTable from "@/public/dex-table.png";

export const metadata: Metadata = {
    title: "NASA Exoplanet Archive | Hypatia Catalog",
    description: "What the Hypatia Catalog's stellar abundances on the NASA Exoplanet Archive are, how abundances are measured and normalized, and what metallicity means.",
};

const hyw2022 = "https://ui.adsabs.harvard.edu/abs/2022AJ....164..256H/abstract";

export default function NeaPage() {
    return (
        <Page>
            <H1 id="nea">Hypatia Catalog Data on the NASA Exoplanet Archive</H1>
            <P>Stellar elemental abundances are determined using spectroscopy to measure the amount of a particular element in the photosphere of a star.</P>
            <P>
                The <In href="/">Hypatia Catalog</In> is a database of stellar elemental abundances that have been measured
                from hundreds of different <In href="/">literature sources</In> within +11,000 stars. Stars are included
                within the database if they are FGKM-type stars (effective temperature = 2300-7500 K), within 500 pc of the
                Sun, and if the literature source measured [Fe/H] and at least one other element. We note that all exoplanet
                host stars are included regardless of distance. Also, in an effort to focus predominantly on{' '}
                <Ext href="https://drive.google.com/file/d/0B6JubEpe8-76YjlBakJydy1OaXM/view?usp=sharing&resourcekey=0-PGfV-0IqRvm6a9Xw5dNCXw">high resolution data,</Ext>{' '}
                we do not often include abundance data from large surveys such as RAVE, WEAVE, GALAH, or APOGEE.
            </P>
            <P>
                The Hypatia Catalog is a multidimensional database, such that multiple literature sources have measured the
                same element within the same star. For the results on the NASA Exoplanet Archive website, the median value
                of all measurements is provided, where the range or spread in those measurements is given as the error.
                The <In href={scatter_url}>main Hypatia Catalog page</In> is available to determine the mean abundance value
                or toggle which literature sources are included/excluded, with an accompanying{' '}
                <In href={help_url}>explanation on the Help page.</In>
            </P>

            <H2 id="abundance-math">Breaking Down Stellar Abundance Math</H2>
            <P>
                The math underlying stellar abundances is anything but simple – for a full overview and helpful walkthrough
                example, we suggest reading <Ext href={hyw2022}>Hinkel, Young, &amp; Wheeler (2022).</Ext> In general,
                elemental abundances are usually measured for a generic element Q, which has been scaled to 10<sup>12</sup>{' '}
                hydrogen atoms, and is often represented as a logged ratio with respect to H or Fe, that is normalized to the
                Sun. The unit for element abundances is “dex”, short for “decadic logarithmic unit”, with a log base 10 –
                similar to the decibel scale. And because stellar abundances are normalized to the Sun, the solar value is
                always at 0.0 dex.
            </P>
            <P>
                With that in mind, the Sun is the nearest and therefore most studied star, which has meant that there are
                dozens of solar abundance determinations. In order to ensure that the stellar abundances within Hypatia are
                on the same baseline, all literature sources have been renormalized to the same solar normalization, where{' '}
                <Ext href="https://ui.adsabs.harvard.edu/abs/2009LanB...4B..712L/abstract">Lodders et al. (2009)</Ext> was
                used for data presented on the NASA Exoplanet Archive. For those wishing to employ a different solar
                normalization or revert to the original normalization, that function is available on the{' '}
                <In href={scatter_url}>main Hypatia Catalog page</In> and described on the <In href={help_url}>Help page.</In>
            </P>
            <P>
                For conversions between absolute and normalized abundances, to different solar normalizations, abundance
                ratio denominators, and molar ratios (plus error propagation), below is helpful table from{' '}
                <Ext href={hyw2022}>Hinkel, Young, &amp; Wheeler (2022).</Ext> In the given notation, * indicates the star
                and ⊙ represents the Sun, although we recommend reading the text for more detail:
            </P>
            <Image src={dexTable} className="w-full h-auto mb-6" sizes="(max-width: 1024px) 100vw, 1024px"
                   alt="A section of Table 2 from Hinkel, Young, & Wheeler (2022) giving the relevant equations and alternate notations/notes for converting from [Q/H] to A(Q*) using the solar composition, renormalizing to different solar compositions, changing the abundance ratio denominator, calculating molar ratios, and propagating errors to molar ratios."/>
            <P>
                There are a variety of additional complications when it comes to stellar elemental abundances, such as the
                handling of binary stars, lines from different ionization states (e.g., neutral vs singly ionized), as well
                as the abundance methodologies used by each literature source. For a more thorough breakdown, we recommend
                reading the bottom of the <In href={about_url}>About</In> page,{' '}
                <Ext href="http://adsabs.harvard.edu/abs/2014AJ....148...54H">Hinkel et al. (2014)</Ext>,{' '}
                <Ext href="https://ui.adsabs.harvard.edu/abs/2016ApJS..226....4H/abstract">Hinkel et al. (2016)</Ext>, and{' '}
                <Ext href="https://ui.adsabs.harvard.edu/abs/2019ARA%26A..57..571J/abstract">Jofre, Heiter, &amp; Soubiran (2019).</Ext>
            </P>

            <H2 id="metallicity">Confusion About &quot;Metallicity&quot;</H2>
            <P>
                We note that there is often some confusion around the term “metallicity.” By definition, metallicity is the
                abundance of elements within a star that are heavier than H or He, often represented as [M/H]. However, it
                has become common practice within the field to use metallicity and [Fe/H] interchangeably. This is primarily
                a historical convenience, since up until the last ~20 years, most stars only had measurements of [Fe/H].
                Therefore, it was assumed that all elements behaved the same, such that the scaling of Fe would give the
                scaling for the total [M/H] metallicity. Through improved instrumentation and stellar models, it has become
                clear that abundance ratios <em>can vary substantially</em> between stars with the same [Fe/H] -- so [M/H]
                must be treated as a distinct quantity. Still, it is common to see references in the literature discuss a
                star’s “metallicity” when they are really only referring to the star’s iron content, [Fe/H].
            </P>
        </Page>
    );
}
