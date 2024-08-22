import Link from 'next/link';

export default function HelpPage() {
    return (
        <div>

            <div className="col-md-3"></div>
            <div className="col-md-6">

                <h1 className="c14" id="h.lj4on8a25zbx"><span className="c7">GETTING STARTED</span></h1>
                <p className="c2"><span className="c4"></span></p>
                <p className="c3 c9"><span className="c5">Stellar abundance information provides one of the primary tools for understanding everything from the evolution of the Milky Way galaxy to the structure and mineralogy of exoplanets. </span><span
                    className="c5">The Hypatia Catalog is a composite stellar abundance catalog that is comprised of multiple literature sources of high-resolution, spectroscopic data which was originally introduced in Hinkel et al. (</span><span
                    className="c12"><a className="c6" href="https://ui.adsabs.harvard.edu/abs/2014AJ....148...54H"
                                   target="_blank">2014</a></span><span className="c5">) and subsequently updated in Hinkel et al. (</span><span
                    className="c12"><a className="c6" href="https://ui.adsabs.harvard.edu/abs/2016ApJS..226....4H"
                                   target="_blank">2016</a></span><span className="c5">, </span><span className="c12"><a
                    className="c6" href="https://ui.adsabs.harvard.edu/abs/2017ApJ...848...34H/abstract"
                    target="_blank">2017</a></span><span className="c5">). A breakdown of all the included catalogs (with {'>'} 20 stars), including information regarding their telescopes, models, and techniques, is given in </span><span
                    className="c12"><a className="c6"
                                   href="https://drive.google.com/file/d/0B6JubEpe8-76YjlBakJydy1OaXM/view?usp=sharing&resourcekey=0-PGfV-0IqRvm6a9Xw5dNCXw"
                                   target="_blank">this table,</a></span><span className="c0"> where a description of the columns can be found at the bottom of the
                    <Link className="c6" href="/hypatia/default/about">About</Link> page. The NASA Exoplanet Archive data
                    <Link href="/hypatia/default/nea" target="_blank">data page is here.</Link> </span>
                </p>
                <p className="c2"><span className="c0"></span></p>
                <p className="c2"><span className="c0"></span></p>
                <h1 className="c14" id="h.tf4ppwc01gp9"><span className="c7">PLOTS</span></h1>
                <p className="c2"><span className="c0"></span></p>
                <h2 className="c23" id="h.1dznyhutv8a8"><span className="c25">Elements &amp; Properties</span></h2>
                <p className="c3 c9"><span className="c5">The plot can be filtered using the 3 filter boxes on the top right that provide minimum and maximum values (either can be left blank in place of infinity). Changes are enacted by pausing for a few seconds (it is no longer necessary to click the &ldquo;Submit&rdquo; button at the bottom of the plot). Options for the filter criteria can be accessed by clicking on the dropdown menu that says &ldquo;none&rdquo; as default. From the dropdown menu, if an element is chosen from the Periodic Table, the filter changes to become an X/Y ratio where both the numerator and denominator can be specified. In addition to the neutral state of the element, if the singly ionized element has been measured, the &ldquo;II&rdquo; next to the element can be selected </span><span
                    className="c13">(see the <a className="c6"
                                            href="https://www.hypatiacatalog.com/hypatia/default/about">About</a> page).</span><span> </span><span
                    className="c5">Stellar properties are listed along the bottom of the drop down menu in addition to planetary properties. If any of planetary properties are chosen, then the graph will show only planet hosting stars. To look at those stars that have planets without a filter, simply click on &ldquo;planet letter&rdquo; in one of the filters (without having to add anything into the &ldquo;min&rdquo; or &ldquo;max&rdquo; regions). The graph will then plot all of the planets, regardless of whether another planet property is has been selected for the x-, y-, or z-axes, such that a star that hosts multiple planets will be plotted multiple times. The table will also update to include NEA names. </span><span
                    className="c17 c5"></span><span className="c5 c24">&nbsp;</span><span className="c0">The X and Y axes can plot any of the element ratios, stellar properties, or planet properties. Additionally, the Z-axis, or color, can be initialized to show another dimension.</span>
                </p>
                <p className="c2"><span className="c0"></span></p>
                <p className="c3 c9"><span className="c0">To move, adjust, zoom, or generally change the properties of the plot, the tools listed vertically along the right side of the plot can be toggled to make the appropriate adjustments. Additionally, the figure can be saved by clicking the &ldquo;Save&rdquo; button near the bottom. </span>
                </p>
                <p className="c2"><span className="c0"></span></p>
                <h2 className="c23" id="h.mcom9jup1wtd"><span className="c25">Stars With &amp; Without Planets</span></h2>
                <p className="c3 c9"><span className="c5">While the plot showing &ldquo;Elements and Properties&rdquo; enables a user to look at </span><span
                    className="c24 c5">either</span><span className="c5">&nbsp;planet hosting stars or stars that are not currently known to have planets, we wanted to provide the ability to look at the two populations simultaneously. Therefore, we have provided a 1D histogram that shows both stars with and without planets. Similar to the other plot, the filter bar can be used to make cuts on those stars analyzed. Additionally, the histogram can viewed either in terms of total number of stars in a bin or normalized (by checking the &ldquo;Normalize the histogram&rdquo; toggle) according to the bin with most number of stars, which has a height of 1 by definition. &nbsp;</span>
                </p>
                <p className="c2"><span className="c0"></span></p>
                <h1 className="c14" id="h.agtiyh92ekx"><span className="c7">ADVANCED CONTROLS</span></h1>
                <p className="c3 c9"><span className="c0">For those users wishing to change some of the more nuanced aspects of the stellar abundances within the Hypatia Catalog and Database, we provide the ability to make adjustments. In order to ensure that all of the stellar abundances within Hypatia are on the same baseline, all individual catalogs have been renormalized to the same solar normalization. The default is Lodders et al. (2009). As part of the database, the user can change the solar normalization to be with respect to Asplund et al. (2009), Grevesse et al. (2007), Asplund et al. (2005), Grevesse &amp; Sauval (1998), and Anders &amp; Grevesse (1989). If the user would like to view the stellar abundances with respect to the solar normalization employed by each of the catalogs individually, the &ldquo;Original&rdquo; option can be chosen. We note that abundances originally published in absolute A(X) notation cannot be shown when the "Original" normalization is selected, since no solar normalization was specified by the authors at the time of publication. However, when a solar normalization is chosen by the Hypatia Catalog Database user, then all abundances -- [X/H], [X/Fe], or A(X) -- are placed on the same solar scale. The absolute abundances, namely without a solar normalization, can be viewed by choosing &ldquo;Absolute.&rdquo; If an element is selected (with respect to H or Fe) and the plot returns "No data points to display," the original data may be only available as absolute. See <a
                    className="c6" href="https://ui.adsabs.harvard.edu/abs/2022AJ....164..256H/abstract" target="_blank">Hinkel, Young, & Wheeler (2022)</a> for more details.</span>
                </p>
                <p className="c2"><span className="c0"></span></p>
                <p className="c3 c9"><span className="c5">The Hypatia Catalog is a multidimensional database, which utilizes all stellar abundances measurements made for an element within a star by +300 catalogs (see <a
                    className="c6" href="http://adsabs.harvard.edu/abs/2014AJ....148...54H" target="_blank">Hinkel et al. 2014</a>, Fig 3). Therefore, to provide a 2-dimensional table, th</span><span
                    className="c5">ose</span><span className="c5">&nbsp;measurement</span><span className="c5">s</span><span
                    className="c0">&nbsp;must be collapsed or reduced. The toggle &ldquo;If an element ratio is in multiple catalogs&rdquo; changes the reduction method to either take the median (default) or mean of all measurements of an element in a star. </span>
                </p>
                <p className="c2"><span className="c0"></span></p>
                <p className="c3 c9"><span className="c0">Finally, while the Hypatia Catalog and Database is unbiased in its inclusion of datasets, we recognize that the user may wish to look exclusively at particular catalogs. We have provided a toggle that allows the user to switch between &ldquo;Excluding&rdquo; or &ldquo;Allowing&rdquo; individual catalogs as they see fit. </span>
                </p>
                <p className="c2"><span className="c0"></span></p>
                <p className="c2"><span className="c0"></span></p>
                <h1 className="c14" id="h.2f69whuql8by"><span className="c7">TABLE</span></h1>
                <p className="c3 c9"><span
                    className="c5 c17">The table is filtered using the filter bars at the top. </span><span className="c5">The columns that are shown in the table can be adjusted using the &ldquo;Add/remove columns&rdquo; button, which gives the user the ability to include individual elements (shown as [X/H] unless the Absolute solar normalization is chosen). Additionally, all stellar properties (RA, Dec, XYZ position, distance, disk, spectral type, V mag, B-V, UVW galactic velocity, Teff, and logg) and all planetary properties (planet letter, period, planet mass, eccentricity, and semimajor axis, where applicable) can be shown in the table </span><span
                    className="c13">(see the <a className="c6"
                                            href="https://www.hypatiacatalog.com/hypatia/default/about">About</a> page).</span><span
                    className="c0"></span></p>
                <p className="c2"><span className="c0"></span></p>
                <p className="c3 c9"><span className="c5 c17">The user can also view the spread (or error) in the stellar abundances. Per the original Hypatia Catalog paper (<a
                    className="c6" href="http://adsabs.harvard.edu/abs/2014AJ....148...54H" target="_blank">Hinkel et al. 2014</a>), the spread is defined as the range in the stellar abundance measurements when determined by different groups measuring that same element within that same star. The spread is an exceptionally useful tool to truly define how consistently an element is measured within the star between different datasets, which is why we utilize it as the overall abundance precision, see <a
                    className="c6" href="https://ui.adsabs.harvard.edu/abs/2016ApJS..226....4H" target="_blank">Hinkel et al. (2016)</a> for more details. </span>
                </p>
                <p className="c2"><span className="c0"></span></p>
                <p className="c2"><span className="c0"></span></p>
                <p className="c2"><span className="c0"></span></p>
                <p className="c2"><span className="c0"></span></p>
                <p className="c2"><span className="c0"></span></p>
                <p className="c2"><span className="c0"></span></p>
                <p className="c2"><span className="c0"></span></p>
                <p className="c2"><span className="c0"></span></p>
                <p className="c2"><span className="c0"></span></p>
            </div>
        </div>
    );
}