// The columns of the Hypatia Catalog table, as described on the About page.
import React from "react";
import {Ext, definitionType} from "@/components/Text";

// the data sources the descriptions cite
const gaiaDR3 = <Ext href="https://vizier.cds.unistra.fr/viz-bin/VizieR-3?-source=I/355">Gaia DR3</Ext>;
const gaiaDR2 = <Ext href="http://vizier.u-strasbg.fr/viz-bin/VizieR?-source=I/345">Gaia DR2</Ext>;
const anderson = <Ext href="https://ui.adsabs.harvard.edu/abs/2012AstL...38..331A/">Anderson et al. 2012</Ext>;
const pastel = <Ext href="https://ui.adsabs.harvard.edu/abs/2016A%26A...591A.118S/">PASTEL</Ext>;
const nea = <Ext href="https://exoplanetarchive.ipac.caltech.edu/">NASA Exoplanet Archive</Ext>;
const tic = (
    <Ext href="https://heasarc.gsfc.nasa.gov/docs/tess/tess-input-catalog-version-8-tic-8-is-now-available-at-mast.html">
        the TESS Input Catalog
    </Ext>
);
export const simbad = <Ext href="http://simbad.u-strasbg.fr/simbad/sim-fid">SIMBAD</Ext>;

export const columns: Array<definitionType> = [
    {label: "HIP", unit: null, description: "Hipparcos name"},
    {label: "HD", unit: null, description: "Henry-Draper catalog name"},
    {label: "2MASS", unit: null, description: "2MASS name"},
    {
        label: "All Names",
        unit: null,
        description: (
            <>
                Additional names from {simbad}. Note: The prefix{" "}
                <Ext href="https://cds.unistra.fr/cgi-bin/Dic-Simbad?NAME">&quot;NAME&quot;</Ext> is used by SIMBAD to
                indicate common or historical names (e.g. NAME kapteyn&apos;s star), which we&apos;ve kept to indicate
                the name is verified.
            </>
        ),
    },
    {label: "RAdeg", unit: "deg", description: <>Right Ascension decimal degrees (J2000) from {gaiaDR3}</>},
    {label: "DEdeg", unit: "deg", description: <>Declination decimal degrees (J2000) from {gaiaDR3}</>},
    {label: "X", unit: "pc", description: "Cartesian geocentric x-coordinate from the Sun"},
    {label: "Y", unit: "pc", description: "Cartesian geocentric y-coordinate from the Sun"},
    {label: "Z", unit: "pc", description: "Cartesian geocentric z-coordinate from the Sun"},
    {
        label: "Dist",
        unit: "pc",
        description: (
            <>
                distance in pc (from {gaiaDR3}, {gaiaDR2}, {anderson})
            </>
        ),
    },
    {
        label: "pmRA",
        unit: "km/s",
        description: (
            <>
                proper motion for Right Ascension (from {gaiaDR3}, {gaiaDR2}, and {anderson})
            </>
        ),
    },
    {
        label: "pmDec",
        unit: "km/s",
        description: (
            <>
                proper motion for Declination (from {gaiaDR3}, {gaiaDR2}, and {anderson})
            </>
        ),
    },
    {
        label: "UVel",
        unit: "km/s",
        description: (
            <>
                Component of space velocity positive toward the Galactic anticenter radial (from {anderson}, null =
                9999.0)
            </>
        ),
    },
    {
        label: "VVel",
        unit: "km/s",
        description: (
            <>
                Component of space velocity positive in the direction of Galactic rotation (from {anderson}, null =
                9999.0)
            </>
        ),
    },
    {
        label: "WVel",
        unit: "km/s",
        description: (
            <>Component of space velocity positive toward the North Galactic Pole (from {anderson}, null = 9999.0)</>
        ),
    },
    {label: "Teff", unit: "K", description: <>stellar effective temperature (from {pastel})</>},
    {label: "logg", unit: "cm/s²", description: <>surface gravity of the star (from {pastel})</>},
    {
        label: "Disk",
        unit: null,
        description: 'likely origin within the disk/thin/thick based on kinematics (null = "N/A")',
    },
    {label: "SpT", unit: null, description: <>spectral type (from {anderson})</>},
    {label: "Bmag", unit: "mag", description: <>B magnitude (from {pastel})</>},
    {label: "Vmag", unit: "mag", description: <>V magnitude (from {pastel})</>},
    {label: "B-V", unit: "mag", description: <>B-V color (from {pastel})</>},
    {label: "letter", unit: null, description: <>planet letter (from {nea})</>},
    {label: "multi", unit: null, description: <>number of planets in the system (from {nea})</>},
    {label: "pmass", unit: "M_Jupiter", description: <>planetary mass (from {nea})</>},
    {label: "period", unit: "days", description: <>planetary period (from {nea})</>},
    {label: "ecc", unit: null, description: <>planetary eccentricity (from {nea})</>},
    {label: "sma", unit: "AU", description: <>planetary semimajor axis (from {nea})</>},
    {label: "smass", unit: "M_Sun", description: <>stellar mass (from {tic})</>},
    {label: "radius", unit: "R_Sun", description: <>stellar radius (from {tic})</>},
    {
        label: "X",
        unit: "dex",
        description:
            "[X/H] abundance in dex as compiled from multiple catalogs (which can be included/excluded in plots)",
    },
    {
        label: "spX",
        unit: "dex",
        description:
            "Spread in XH in dex or the range in abundance measurements as reported by multiple catalogs (which can in allowed/excluded)",
    },
];
