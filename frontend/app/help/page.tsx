import type {Metadata} from "next";
import {Page, H1, H2, P, Ul, Ext, In} from "@/components/Text";
import {aboutURL, neaURL} from "@/lib/urls";

export const metadata: Metadata = {
    title: "Help | Hypatia Catalog",
    description: "How to use the plots, the table and the advanced controls of the Hypatia Catalog.",
};

export default function HelpPage() {
    return (
        <Page>
            <H1 id="getting-started">GETTING STARTED</H1>
            <P>
                Stellar abundance information provides one of the primary tools for understanding everything from
                the evolution of the Milky Way galaxy to the structure and mineralogy of exoplanets. The Hypatia
                Catalog is a composite stellar abundance catalog that is comprised of multiple literature sources of
                high-resolution, spectroscopic data which was originally introduced in Hinkel et al.
                (<Ext href="https://ui.adsabs.harvard.edu/abs/2014AJ....148...54H">2014</Ext>) and subsequently
                updated in Hinkel et al. (<Ext href="https://ui.adsabs.harvard.edu/abs/2016ApJS..226....4H">2016</Ext>,{' '}
                <Ext href="https://ui.adsabs.harvard.edu/abs/2017ApJ...848...34H/abstract">2017</Ext>). A breakdown
                of all the included catalogs (with {'>'} 20 stars), including information regarding their telescopes,
                models, and techniques, is given in{' '}
                <Ext href="https://drive.google.com/file/d/0B6JubEpe8-76YjlBakJydy1OaXM/view?usp=sharing&resourcekey=0-PGfV-0IqRvm6a9Xw5dNCXw">this table,</Ext>{' '}
                where a description of the columns can be found at the bottom of the{' '}
                <In href={aboutURL}>About</In> page. The NASA Exoplanet Archive data{' '}
                <In href={neaURL}>data page is here.</In>
            </P>

            <H2 id="filtering">Filtering</H2>
            <P>
                The plot and table can be filtered using the filter rows on the right, each with a minimum and a
                maximum value (either can be left blank in place of infinity); up to ten filters can be set, and
                a new row appears as each one is filled. Changes are enacted by pausing for a
                few seconds (it is no longer necessary to click the “Submit” button at the bottom of the plot).
                Options for the filter criteria can be accessed by clicking on the dropdown menu that says “none” as
                default. From the dropdown menu, if an element is chosen from the Periodic Table, the filter changes
                to become an X/Y ratio where both the numerator and denominator can be specified. In addition to the
                neutral state of the element, if the singly ionized element has been measured, the “II” next to the
                element can be selected (see the <In href={aboutURL}>About</In> page).
                Stellar properties are listed along the bottom of the drop down menu in addition to planetary
                properties. If any of planetary properties are chosen, then the graph will show only planet hosting
                stars. To look at those stars that have planets without a filter, simply click on “planet letter” in
                one of the filters (without having to add anything into the “min” or “max” regions). The graph will
                then plot all of the planets, regardless of whether another planet property has been selected for
                the x-, y-, or z-axes, such that a star that hosts multiple planets will be plotted multiple times.
                The table will also update to include NEA names. The X and Y axes can plot any of the element
                ratios, stellar properties, or planet properties. Additionally, the Z-axis, or color, can be
                initialized to show another dimension.
            </P>
            <P>
                To move, adjust, zoom, or generally change the properties of the plot, the tools listed vertically
                along the right side of the plot can be toggled to make the appropriate adjustments. Additionally,
                the figure can be saved by clicking the “Save” button near the bottom.
            </P>

            <H1 as="h2" id="plots">PLOTS</H1>
            <H2 as="h3" id="scatter">Scatter</H2>
            <P>
                The Scatter plot is the most basic plot on the Hypatia website, allowing the user to plot nearly any
                parameter with respect to another. The scatter plot has extremely high functionality and
                flexibility. The X and Y axes can plot any of the element ratios, stellar properties, or planet
                properties. Additionally, the Z-axis, or color, can be initialized to show another dimension.
            </P>

            <H2 as="h3" id="target-lists">Target Lists</H2>
            <P>
                The Target Lists plot is similar to the Scatter plot in functionality, but it also includes a number
                of pre-defined lists. The available target sets currently include:
            </P>
            <Ul>
                <li>
                    the Habitable Worlds Observatory (HWO) Tier 1 and Tier 2 target lists as compiled by the Target
                    Stars and Systems (TSS) working group. The 2025 TSS list includes 164 highest priority Tier 1
                    stars that are most accessible for exoEarth direct imaging as well as the 495 Tier 2 stars that
                    could plausibly be observed by HWO designs. See{' '}
                    <Ext href="https://ui.adsabs.harvard.edu/abs/2025PASP..137j4402T/abstract">Tuchow et al. (2025),</Ext>{' '}
                    for more details.
                </li>
                <li>
                    thin disk and thick disk stars based purely on kinematics as defined by{' '}
                    <Ext href="https://ui.adsabs.harvard.edu/abs/2003A%26A...410..527B/abstract">Bensby et al. (2003)</Ext>{' '}
                    and discussed in the main Hypatia paper:{' '}
                    <Ext href="https://ui.adsabs.harvard.edu/abs/2014AJ....148...54H/abstract">Hinkel et al. (2014)</Ext>, and
                </li>
                <li>
                    host exoplanets, or any star that has a confirmed planet per the NASA Exoplanet Archive.
                </li>
            </Ul>
            <P>
                A user may plot multiple target lists at once, either individually or using &quot;union&quot; logic
                to show which stars are in multiple target lists. The user may also plot the rest of the Hypatia
                Catalog stars that are not in any of the target lists selected.
            </P>

            <H2 as="h3" id="histogram">Histogram</H2>
            <P>
                While the plot showing “Elements and Properties” enables a user to look at <em>either</em> planet
                hosting stars or stars that are not currently known to have planets, we wanted to provide the ability
                to look at the two populations simultaneously. Therefore, we have provided a 1D histogram that shows
                both stars with and without planets. Similar to the other plot, the filter bar can be used to make
                cuts on those stars analyzed. Additionally, the histogram can be viewed either in terms of total
                number of stars in a bin or normalized (by checking the “Normalize the histogram” toggle) according
                to the bin with most number of stars, which has a height of 1 by definition.
            </P>

            <H1 as="h2" id="advanced-controls">ADVANCED CONTROLS &amp; INFO</H1>
            <P>
                For those users wishing to change some of the more nuanced aspects of the stellar abundances within
                the Hypatia Catalog, we provide the ability to make adjustments. In order to ensure that all of the
                stellar abundances within Hypatia are on the same baseline, all individual catalogs have been
                renormalized to the same solar normalization. The default is Lodders et al. (2009). As part of the
                database, the user can change the solar normalization to be with respect to Asplund et al. (2009),
                Grevesse et al. (2007), Asplund et al. (2005), Grevesse &amp; Sauval (1998), and Anders &amp;
                Grevesse (1989). If the user would like to view the stellar abundances with respect to the solar
                normalization employed by each of the catalogs individually, the “Original” option can be chosen.
                We note that abundances originally published in absolute A(X) notation cannot be shown when the
                “Original” normalization is selected, since no solar normalization was specified by the authors at
                the time of publication. However, when a solar normalization is chosen by the Hypatia Catalog user,
                then all abundances -- [X/H], [X/Fe], or A(X) -- are placed on the same solar scale. The absolute
                abundances, namely without a solar normalization, can be viewed by choosing “Absolute.” If an
                element is selected (with respect to H or Fe) and the plot returns “No data points to display,” the
                original data may be only available as absolute. See{' '}
                <Ext href="https://ui.adsabs.harvard.edu/abs/2022AJ....164..256H/abstract">Hinkel, Young, &amp; Wheeler (2022)</Ext>{' '}
                for more details.
            </P>
            <P>
                The Hypatia Catalog is a multidimensional database, which utilizes all stellar abundances
                measurements made for an element within a star by 360+ catalogs (see details on the{' '}
                <In href="/">Home page</In>). Therefore, to provide a 2-dimensional table,
                those measurements must be collapsed or reduced. The toggle “If an element ratio is in multiple
                catalogs” changes the reduction method to either take the median (default) or mean of all
                measurements of an element in a star. We note that the stellar abundance dex notation is inherently
                in log-space, which is explained in{' '}
                <Ext href="https://ui.adsabs.harvard.edu/abs/2022AJ....164..256H/abstract">Hinkel, Young, &amp; Wheeler (2022)</Ext>.
                Therefore, to accurately determine the mean value, all of the abundances must first be converted to
                linear-space, the average taken, and then converted back to log-space. As a result, the mean values
                will appear slightly more positive than the log-space average. In addition, when viewing the
                references in the table (by selecting the “Reference” button), only those references that went into
                the final calculation are provided. Namely, all references are shown when taking the mean, while
                only the middle one or two references are shown when taking the median.
            </P>
            <P>
                Users may note that some [Fe/H] column values are repeated by the same first author or group across
                multiple papers, who often draw upon their previous stellar parameters calculations when determining
                new element abundances for the same set of stars. Any data entered into the Hypatia Catalog is
                required to have [Fe/H] data, to ensure that any [X/H] to [X/Fe] conversion is accurate. This means
                that the same [Fe/H] values are inherently repeated in the [Fe/H] column, ultimately impacting the
                median or mean calculation. Unfortunately, this is not an issue that can be easily corrected within
                the Hypatia Catalog database, but we hope that the accessibility of all of the references will allow
                each user to make the best decision for their science.
            </P>
            <P>
                Finally, while the Hypatia Catalog is unbiased in its inclusion of datasets, we recognize that the
                user may wish to look exclusively at particular catalogs. We have provided a toggle that allows the
                user to switch between “Excluding” or “Allowing” individual catalogs as they see fit.
            </P>

            <H1 as="h2" id="table">TABLE</H1>
            <P>
                The table is filtered using the filter bars at the top. The columns that are shown in the table can
                be adjusted using the “Add/remove columns” button, which gives the user the ability to include
                individual elements (shown as [X/H] unless the Absolute solar normalization is chosen). Additionally,
                all stellar properties (RA, Dec, XYZ position, distance, disk, spectral type, V mag, B-V, UVW
                galactic velocity, Teff, and logg) and all planetary properties (planet letter, period, planet mass,
                eccentricity, and semimajor axis, where applicable) can be shown in the table (see the{' '}
                <In href={aboutURL}>About</In> page).
            </P>
            <P>
                The user can also view the spread (or error) in the stellar abundances. Per the original Hypatia
                Catalog paper (<Ext href="http://adsabs.harvard.edu/abs/2014AJ....148...54H">Hinkel et al. 2014</Ext>),
                the spread is defined as the range in the stellar abundance measurements when determined by different
                groups measuring that same element within that same star. The spread is an exceptionally useful tool
                to truly define how consistently an element is measured within the star between different datasets,
                which is why we utilize it as the overall abundance precision, see{' '}
                <Ext href="https://ui.adsabs.harvard.edu/abs/2016ApJS..226....4H">Hinkel et al. (2016)</Ext> for
                more details.
            </P>
        </Page>
    );
}
