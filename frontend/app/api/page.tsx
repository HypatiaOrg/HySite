import type {Metadata} from "next";
import {Page, H1, Ext, In} from "@/components/Text";
import {Callout, Definitions, Entry, Fields, Field, Note, Request, Python, Result, Pre} from "@/components/ApiDocs";
import {scatterURL, histURL} from "@/lib/urls";

export const metadata: Metadata = {
    title: "API | Hypatia Catalog",
    description: "The Hypatia Catalog API: solar normalizations, elements, catalogs, stars, compositions and plot data as JSON, with Python examples.",
};

const simbad = <Ext href="https://simbad.u-strasbg.fr/simbad/">SIMBAD</Ext>;
const nea = <Ext href="https://exoplanetarchive.ipac.caltech.edu/">NASA Exoplanet Archive</Ext>;

const endpoints = [
    ["solarnorm", "the solar normalizations"],
    ["element", "the elements"],
    ["catalog", "the abundance catalogs"],
    ["star", "a star's properties and planets"],
    ["composition", "a star's abundance of an element"],
    ["data", "the scatter plot and histogram data"],
];

export default function ApiPage() {
    return (
        <Page>
            <H1 id="api">Hypatia Catalog API v2.2.0</H1>
            <Callout kind="info"><b>Data access no longer requires an API Key.</b></Callout>
            <Callout kind="note">
                <p className="mb-3">
                    <b>Version 2.2 of the API uses a <Ext href="https://www.djangoproject.com/">Django</Ext>-Python
                    framework with data access and query powered by a <Ext href="https://www.mongodb.com/">MongoDB</Ext> database.</b>
                </p>
                <ul className="list-disc pl-8 space-y-2">
                    <li>If this update broke your existing pipeline, please reach out.</li>
                    <li>
                        We intend to freeze the current version/views of this API; the purpose of this API is to support
                        existing pipelines since our current framework allows us to include new additional views as
                        necessary. For future APIs, we are considering simplified interfaces, thoughtful defaults, and
                        more output formats to enable first-time partners. At the same time, we want to build towards
                        on-demand support for other databases as well as data-science and machine learning operations.
                        Please reach out for any features that would support your science.
                    </li>
                    <li>
                        Unused fields that were associated with abundance catalogs and solar normalization data objects
                        (returned in <b>solarnorm, catalog, composition</b> queries) were removed.
                    </li>
                    <li>
                        Hypatia Catalog now supports more star names and has a powerful matching tools, as a basis we
                        include every name available from {simbad} for all Hypatia stars. This means that you can use any
                        SIMBAD name to check availability in the Hypatia Catalog.
                    </li>
                    <li>
                        This update included significant performance enhancements. We, at the Hypatia Catalog, are proud
                        to invest in our infrastructure to better enable the next generation of partners (like you!) and
                        scientists around the world.
                    </li>
                </ul>
            </Callout>

            <Definitions>
            <Entry id="what-is-an-api" label="What is an API?">
                An application programming interface (API) allows you to write code that interacts with websites.
                Most major websites provide an API as a courtesy to developers everywhere. For instance,{' '}
                <Ext href="https://developer.spotify.com/documentation/web-api/">here is what the API for Spotify looks like.</Ext>
            </Entry>
            <Entry id="what-is-this" label="What is this?">
                The Hypatia Catalog API allows you to write programs that access the Hypatia Catalog outside a web
                browser. Suppose that you&apos;ve written a program in Python to do computational work for your next
                abundance-related discovery, and it takes data from the Hypatia Catalog as input. You could manually
                download the table via the link under the plot or copy-and-paste data from table, then get your
                program to parse the data -- but that can become tedious over many iterations. Instead, with a few
                simple commands, you can use the API to request the data within your program and it will come to you
                in an easy-to-use, machine-readable format.
            </Entry>
            <Entry id="should-i-use-this" label="Should I use this?">
                Many researchers (and the Hypatia Catalog!) depend on APIs like this one for their work because it
                allows their code to access or update online data automatically, without going by hand to the web
                interface. The Hypatia Catalog API will allow you to access properties of the star, element
                abundances, catalog data, and scatter/histogram plots from the command line (outlined below). If
                you&apos;re not planning on writing code, or if you only need a few stellar abundances for a
                particular star, you may wish to use the <In href={scatterURL}>interactive plotting tool</In> instead.
            </Entry>
            <Entry id="how-do-i-try-it-out" label="How do I try it out?">
                <Note>
                    Many programming languages have libraries that can access web-based APIs. We will focus on the{' '}
                    <Ext href="http://www.python.org/">Python programming language</Ext> and the{' '}
                    <Ext href="https://pypi.org/project/requests/">Requests library</Ext> for interfacing with APIs.
                </Note>
                <Note>
                    When you have Python and the Python-package requests installed, you can put the code snippets below
                    into a Python script or the Python interpreter.
                </Note>
                <p className="bg-hyyellow/30 border border-hyyellow rounded-lg p-3 text-black">
                    We&apos;ve highlighted some text in yellow like this; as you go through the documentation,
                    copy-and-paste the commands provided to connect to the Hypatia Catalog API.
                </p>
            </Entry>
            <Entry id="access-control" label="Access Control">
                We require any single query to have unique star names fewer than 10,000+ the current number of stars
                in the Hypatia Catalog, where repeated names do not add computation costs to the database query. The
                previous versions of this API (v&lt;2.2.0) had rate limits and access controls to throttle the
                computational effort of the API. With improved efficiency in the API throttling is no longer required,
                so we are moving to an on-demand model to further enable our users.
            </Entry>
            </Definitions>

            <Callout kind="info">
                <b>See below for supported query, example code, and example outputs.</b>
                <ul className="list-disc pl-8 pt-2 font-normal">
                    {endpoints.map(([name, what]) => (
                        <li key={name}><In href={`#${name}`}>GET {name}</In>: {what}</li>
                    ))}
                </ul>
            </Callout>

            <Definitions>
            <Entry id="solarnorm" label="GET solarnorm" heading>
                <Note>Returns a list of solar normalizations used by Hypatia.</Note>
                <Fields title="Inputs">none</Fields>
                <Fields title="Outputs">
                    <Field name="author">Author(s) of the paper referencing the solar normalization.</Field>
                    <Field name="year">Year of the paper referencing the solar normalization.</Field>
                    <Field name="notes">Additional notes as needed.</Field>
                    <Field name="id">Used to identify the solar normalization in later API commands (e.g. GET composition).</Field>
                    <Field name="values">If the solar normalization is not absolute or original, this is an object with element keys pair to the values used to normalize the data.</Field>
                </Fields>
                <Request url="/hypatia/api/v2/solarnorm/"/>
                <Python>{`
import requests
entry = requests.get("https://hypatiacatalog.com/hypatia/api/v2/solarnorm")
print(entry.json())
`}</Python>
                <Result>{`
[
  {
    "id": "absolute",
    "notes": "This key provides data that is in absolute scale and is not normalized to the Sun.",
    "year": null,
    "author": "Absolute",
    "values": null,
  },
  {
    "id": "lodders09",
    "notes": "This key provides data that is normalized to the Sun using values from Lodders et al. (2009).",
    "year": 2009,
    "author": "Lodders et al. (2009)",
    "values": {
      "H": 12.0,
      "He": 10.93,
      "Li": 3.28,
      "Be": 1.38,
      ...
    },
  },
  ...
]
`}</Result>
            </Entry>

            <Entry id="element" label="GET element" heading>
                <Note>Returns a list of elements used by Hypatia.</Note>
                <Fields title="Inputs">none</Fields>
                <Fields title="Outputs">
                    An array of available elements (including ionized species) with abundances in Hypatia Catalog in Periodic Table order.
                </Fields>
                <Request url="/hypatia/api/v2/element/"/>
                <Python>{`
import requests
entry = requests.get("https://hypatiacatalog.com/hypatia/api/v2/element")
print(entry.json())
`}</Python>
                <Result>{`
[
  "Li",
  "Be",
  "Be_II",
  "C",
  "N",
  "O",
  ...
  "Fe",
  "Co",
  "Co_II",
  ...
]
`}</Result>
            </Entry>

            <Entry id="catalog" label="GET catalog" heading>
                <Note>Returns a list of elemental abundance catalogs available in the Hypatia Catalog database.</Note>
                <Fields title="Inputs">none</Fields>
                <Fields title="Outputs">
                    <Field name="author">Author(s) of the catalog&apos;s paper.</Field>
                    <Field name="year">Year of the catalog&apos;s paper.</Field>
                    <Field name="id">Used to identify the catalog in later API commands (e.g. GET data).</Field>
                    <Field name="original_norm_id">The Hypatia Catalog identifier for the original solar normalization that was originally applied to the data from this catalog (does not apply to data originally reported in terms of absolute abundance).</Field>
                </Fields>
                <Request url="/hypatia/api/v2/catalog/"/>
                <Python>{`
import requests
entry = requests.get("https://hypatiacatalog.com/hypatia/api/v2/catalog")
print(entry.json())
`}</Python>
                <Result>{`
[
  {
    "author": "Abia et al. (2020)",
    "year": 2020,
    "id": "abia20",
    "original_norm_id": "abia20"
  },
  {
    "author": "Adamczak et al. (2013)",
    "year": 2013,
    "id": "adamczak13",
    "original_norm_id": "asplund09"
  },
  {
    "author": "Adamow et al. (2014)",
    "year": 2014,
    "id": "adamow14",
    "original_norm_id": "adamow14"
  },
  ...
]
`}</Result>
            </Entry>

            <Entry id="star" label="GET star" heading>
                <Note>
                    Returns data for each star in the Hypatia database as well as its planets. Multiple stars can be
                    submitted at once. <b>Warning: input-field name changed in version 2.2.0</b>: The Hypatia Catalog
                    has a new star name-engine that is based on names available on {simbad}. As a result, the inputs
                    had been simplified to accept any combination of string names for a space-removed and
                    case-insensitive search; feel free to use any SIMBAD name to check availability in the Hypatia
                    Catalog. Since the Hypatia Catalog database does not check names that are available on SIMBAD in
                    real-time, star names are expired and rechecked from SIMBAD periodically. Names will also be
                    updated stochastically as new abundance data is made available.
                </Note>
                <Fields title="Inputs">
                    <Field name="name">
                        A star name that is recognized by {simbad} database. This does a case-insensitive search of all
                        stars available in the Hypatia Catalog using all known names from SIMBAD,{' '}
                        <Ext href="https://exoplanetarchive.ipac.caltech.edu/">NASA Exoplanet Archive (NEA)</Ext>, and
                        various other aliases found in the primary literature for Hypatia Catalog&apos;s elemental
                        abundances and stellar parameters.
                    </Field>
                </Fields>
                <Fields title="Outputs">
                    <Field name="status">Returns &quot;found&quot; if the star is found and &quot;not-found&quot; if the star is not found.</Field>
                    <Field name="name">
                        The preferred name for the star, in the order of these available: HIP, HD, 2MASS, Gaia DR2, WDS, other names.
                        Name fields: <code>hip,hd,bd,dist,2mass,gaia_dr2,tyc,other_names</code>.
                        Stellar Properties fields: <code>spec,vmag,bv,ra,dec,x,y,z,disk,u,v,w,teff,logg,2MASS,ra_proper_motion,dec_proper_motion,bmag</code>.
                    </Field>
                    <Field name="planets">
                        Returns null or a list of objects, one for each planet hosted by the star. For each planet we get these variables:{' '}
                        <code>name,p,p_min_err,p_max_err,m_p,m_p_min_err,m_p_max_err,e,e_min_err,e_max_err,a,a_min_err,a_max_err</code>.
                        Changed in v2, see notes.
                    </Field>
                    <Field name="requested_name">This is the name used in the query; any URL safe characters have been converted to human-readable characters.</Field>
                </Fields>
                <Pre>{`
Any star name on SIMBAD can be used.
Spaces and letter case are ignored star names searches.
However, if you want to use spaces, substitute '%20' for the space, which is the
URL safe-version of the plus operator '+' to append the two components in the URL path.
For example, 'HIP 12345' should be 'HIP%2012345'.
Join multiple stars with '&' like so: 'HIP%2012345&2MASS%20J19154511-1623157&HIP%20113044'.
`}</Pre>
                <Request url="/hypatia/api/v2/star/?HIP12345&2MASSJ19154511-1623157&HIP113044"/>
                <Note>or with spaces, the same as above:</Note>
                <Request url="/hypatia/api/v2/star/?HIP%2012345&2MASSJ19154511-1623157&HIP%20113044"/>
                <Note>
                    If the SIMBAD star name you want to use in not parseable into a URL safe string, see the example
                    below for how to use the &apos;name&apos; parameter.
                </Note>
                <Python>{`
import requests
params = {"name": ["HIP 12345","2MASS J19154511-1623157","HIP 113044"]}
entry = requests.get("https://hypatiacatalog.com/hypatia/api/v2/star", params=params)
print(entry.json())
`}</Python>
                <Note>For the stars names in this example:</Note>
                <Pre>{`
HIP 12345 is not in Hypatia and will not be found
2MASS J19154511-1623157 will be found and has no planets, so far...
HIP 113044 will found and has one planet, so far...
`}</Pre>
                <Result>{`
[
  {
    "status": "not-found",
    "hip": null,
    "hd": null,
    "bd": null,
    "spec": null,
    "vmag": null,
    "bv": null,
    "dist": null,
    "ra": null,
    "dec": null,
    "x": null,
    "y": null,
    "z": null,
    "disk": null,
    "u": null,
    "v": null,
    "w": null,
    "teff": null,
    "logg": null,
    "2MASS": null,
    "ra_proper_motion": null,
    "dec_proper_motion": null,
    "bmag": null,
    "planets": null,
    "requested_name": "HIP 12345"
  },
  {
    "status": "found",
    "hip": null,
    "hd": null,
    "bd": null,
    "spec": null,
    "vmag": null,
    "bv": null,
    "dist": 303.76,
    "ra": 288.937982083333,
    "dec": -16.3877119444444,
    "x": 94.579,
    "y": -275.645,
    "z": -85.702,
    "disk": "N/A",
    "u": null,
    "v": null,
    "w": null,
    "teff": 5835.15,
    "logg": 4.25,
    "2MASS": null,
    "ra_proper_motion": -1.275,
    "dec_proper_motion": -26.6299,
    "bmag": null,
    "planets": null,
    "requested_name": "2MASS J19154511-1623157",
    "name": "TYC 6296-654-1",
    "2mass": "2MASS J19154511-1623157",
    "tyc": "TYC 6296-654-1",
    "other_names": [
      "2MASS J19154511-1623157",
      "EPIC 219581534",
      "GALAH 170828002201178",
      "Gaia DR1 4087860502658323712",
      "Gaia DR2 4087860506965490560",
      "Gaia DR3 4087860506965490560",
      "TIC 130278180",
      "TYC 6296-654-1",
      "[CWW2013] 71"
    ]
  },
  {
    "status": "found",
    "hip": "HIP 113044",
    "hd": "HD 216435",
    "bd": null,
    "spec": "G0V",
    "vmag": 6.04,
    "bv": 0.621,
    "dist": 33.032,
    "ra": 343.40805125,
    "dec": -48.5982841666667,
    "x": 20.936,
    "y": -6.238,
    "z": -24.777,
    "disk": "thin",
    "u": -27,
    "v": -21.3,
    "w": -10.2,
    "teff": 6047,
    "logg": 4.16,
    "2MASS": null,
    "ra_proper_motion": 217.9429,
    "dec_proper_motion": -81.0128,
    "bmag": 6.66,
    "planets": [
      {
        "name": "b",
        "m_p": 1.26,
        "m_p_min_err": -0.13,
        "m_p_max_err": 0.13,
        "p": 1311,
        "p_min_err": -49,
        "p_max_err": 49,
        "e": 0.07,
        "e_min_err": -0.078,
        "e_max_err": 0.078,
        "a": 2.56,
        "a_min_err": -0.17,
        "a_max_err": 0.17
      }
    ],
    "requested_name": "HIP 113044",
    "name": "* tau01 Gru",
    "2mass": "2MASS J22533792-4835539",
    "tyc": "TYC 8450-1093-1",
    "other_names": [
      "* tau01 Gru",
      "2MASS J22533792-4835539",
      "AKARI-IRC-V1 J2253381-483554",
      "CD-49 13988",
      "CPC  0 20170",
      "CPD-49 11672",
      "GC 31913",
      "GCRV 73592",
      "GEN# +1.00216435",
      "GJ 9802",
      "Gaia DR2 6515731817739456256",
      "Gaia DR3 6515731817739456256",
      "HD 216435",
      "HIC 113044",
      "HIP 113044",
      "HR  8700",
      "IRAS 22507-4851",
      "LTT  9249",
      "N30 5037",
      "NLTT 55141",
      "PLX 5543",
      "PLX 5543.00",
      "PPM 328720",
      "SAO 231343",
      "SKY# 43488",
      "SPOCS  987",
      "TD1 29424",
      "TIC 161314759",
      "TYC 8450-1093-1",
      "UBV   19602",
      "UBV M  26682",
      "uvby98 100216435"
    ]
  }
]
`}</Result>
            </Entry>

            <Entry id="composition" label="GET composition" heading>
                <Note>
                    Returns a list of compositions for a given element, star, and solar normalization, and computes
                    the median and mean value for that group. More than one group can be supplied by submitting each
                    group one after the other: element, star, solar normalization, element, star, solar
                    normalization, etc.
                </Note>
                <Fields title="Inputs">
                    <Field name="element">
                        Name of the element, case-insensitive. We encourage you to omit the trailing H used in dex
                        notation, although the element-name parser attempts to remove this after parsing ionization states.
                    </Field>
                    <Field name="name">
                        Searches all names for a star (e.g. <code>name=HIP 57</code>). Search is case-insensitive. Any
                        SIMBAD star name can be used, not just the preferred name returned by Hypatia.
                    </Field>
                    <Field name="solarnorm">
                        (Omit this input to use the Lodders et al. 2009 solar-normalization) Identifier for the solar
                        normalization. See <b>GET solarnorm</b> for solar normalization identifiers.
                    </Field>
                </Fields>
                <Note>
                    <b>Note:</b> There should be the same number of elements, stars, and (if included) solar
                    normalizations. If solar normalizations are omitted, Lodders et al. 2009 is assumed for all compositions.
                </Note>
                <Fields title="Outputs">
                    <Field name="mean">The mean value of all abundances for this star, element, and solar normalization.</Field>
                    <Field name="max">The maximum value of all abundances for this star, element, and solar normalization.</Field>
                    <Field name="min">The minimum value of all abundances for this star, element, and solar normalization.</Field>
                    <Field name="plusminus">
                        When two or more abundance values are present, this is half of the absolute range of all values
                        for this star, element, and solar normalization. Otherwise, this is a representative error for the element.
                    </Field>
                    <Field name="std">
                        When three or more abundance values are present, this is the standard deviation of all abundances
                        for this star, element, and solar normalization. Otherwise, this is null.
                    </Field>
                    <Field name="name">The preferred name for the star in the Hypatia Catalog</Field>
                    <Field name="median_value">
                        The median value of all abundances for this star, element, and solar normalization. This is
                        always a single float value and is an average of the two middle values if there is an even number of values.
                    </Field>
                    <Field name="all_names">All names for the star that are known in the Hypatia Catalog.</Field>
                    <Field name="nea_name">
                        The Hypatia Catalog cross-matches with the <Ext href="https://exoplanetarchive.ipac.caltech.edu/">NEA</Ext>;
                        if this star is a known host of exoplanets, this is the name used in the NEA. Otherwise, this is the string &quot;unknown&quot;.
                    </Field>
                    <Field name="solarnorm">The preferred solar normalization name used by that Hypatia Catalog to return this data.</Field>
                    <Field name="element">The preferred element name used by the Hypatia Catalog to return this data.</Field>
                    <Field name="all_values">A list of objects with values referencing specific abundance catalog literature.</Field>
                    <Field name="median">
                        A list of objects with the median values referencing specific abundance catalog literature. One
                        object for an odd number of values and two objects for an even number of values.
                    </Field>
                    <Field name="match_name">The name used in the Hypatia Catalog to match the star name in the query, lowercase with no spaces.</Field>
                    <Field name="requested_name">The name used in the query; any URL safe characters have been converted to human-readable characters.</Field>
                    <Field name="requested_element">The element used in the query.</Field>
                </Fields>
                <Pre>{`
Any star name on SIMBAD can be used.
Spaces and letter case are ignored star names searches.
However, if you want to use spaces, substitute '%20' for the space, which is the
URL safe-version of the plus operator '+' to append the two components in the URL path.
For example, 'HIP 32970' should be 'HIP%2032970'.
`}</Pre>
                <Request url="/hypatia/api/v2/composition?name=HIP32970&element=ca&solarnorm=asplund09"/>
                <Python>{`
import requests
params = {"name": ["HIP 32970"], "element": ["ca"], "solarnorm": ["asp05"]}
entry = requests.get("https://hypatiacatalog.com/hypatia/api/v2/composition", params=params)
print(entry.json())
`}</Python>
                <Result>{`
[
  {
    "mean": 0.294,
    "max": 0.33,
    "min": 0.257,
    "plusminus": 0.04,
    "std": 0.0261,
    "name": "HD  50499",
    "median_value": 0.295,
    "all_names": [
      "2MASS J06520202-3354559",
      "CD-33  3304",
      "CPC 17  3013",
      "CPD-33  1302",
      "GC  9010",
      "GEN# +1.00050499",
      "GSC 07096-00565",
      "Gaia DR1 5579783569778334464",
      "Gaia DR2 5579783574073770112",
      "Gaia DR3 5579783574073770112",
      "HD  50499",
      "HD 050499",
      "HIC  32970",
      "HIP 32970",
      "PPM 283214",
      "SAO 197294",
      "SKY# 12155",
      "SPOCS  325",
      "TIC 53175558",
      "TYC 7096-565-1",
      "uvby98 100050499"
    ],
    "nea_name": "HD 50499",
    "solarnorm": "asplund09",
    "element": "Ca",
    "all_values": [
      {
        "value": 0.29,
        "catalog": {
          "author": "Brewer et al. (2016)",
          "year": 2016,
          "id": "brewer16_01_of_02_unique_20_04_2023",
          "original_norm_id": "grevesse07"
        }
      },
      {
        "value": 0.257,
        "catalog": {
          "author": "Gonzalez et al. (2010b)",
          "year": 2010,
          "id": "gonzalez10b_01_of_02_unique_20_06_2020",
          "original_norm_id": "asplund09"
        }
      },
      {
        "value": 0.3,
        "catalog": {
          "author": "Maldonado et al. (2015)",
          "year": 2015,
          "id": "maldonado15",
          "original_norm_id": "maldonado15"
        }
      },
      {
        "value": 0.33,
        "catalog": {
          "author": "Maldonado et al. (2018)",
          "year": 2018,
          "id": "maldonado18",
          "original_norm_id": "maldonado15"
        }
      }
    ],
    "median": [
      {
        "value": 0.29,
        "catalog": {
          "author": "Brewer et al. (2016)",
          "year": 2016,
          "id": "brewer16_01_of_02_unique_20_04_2023",
          "original_norm_id": "grevesse07"
        }
      },
      {
        "value": 0.3,
        "catalog": {
          "author": "Maldonado et al. (2015)",
          "year": 2015,
          "id": "maldonado15",
          "original_norm_id": "maldonado15"
        }
      }
    ],
    "match_name": "hip32970",
    "requested_name": "HIP32970",
    "requested_element": "ca",
    "requested_solarnorm": "asplund09"
  }
]
`}</Result>
                <Note>
                    <b>Note:</b> If you are using the Python requests package, multiple sets of elements, stars and
                    solar normalizations are defined using arrays like this:
                </Note>
                <Pre>{`
params = {"name": ["HIP 32970", "HIP 32970"], "element": ["fe", "ca"], "solarnorm": ["asp05", "asp05"]}
`}</Pre>
                <Note>You may omit the solar normalization, in which case Lodders et al. 2009 is assumed:</Note>
                <Pre>{`
params = {"name": ["HIP 32970", "HIP 32970"], "element": ["fe", "ca"]}
`}</Pre>
            </Entry>

            <Entry id="data" label="GET data" heading>
                <Note>
                    Returns scatter plot or histogram raw data shown in the plots of the Hypatia Catalog. Default
                    parameters are used when not specified. The default mode will return the values for the scatter
                    plot shown in the <In href={scatterURL}>Scatter</In> page. If you submit <code>mode=hist</code>,
                    you will receive the histogram shown in the <In href={histURL}>Histogram</In> page.
                </Note>
                <Fields title="Inputs">
                    <Field name="mode">(optional) If mode is set to hist, returns a histogram provided by <In href={histURL}>Histogram</In>.</Field>
                    <Field name="filter1_1">
                        (optional) The first filter. This field can be a stellar property, planet property, or numerator
                        for the element ratio. Stellar and planet properties are listed in GET star. Element ratios are
                        listed in GET element; it is case sensitive and the trailing H should be omitted.
                    </Field>
                    <Field name="filter1_2">(optional) The denominator element to complete an element ratio with filter1_1 (H if omitted)</Field>
                    <Field name="filter1_3">(optional) Minimum value for the filter.</Field>
                    <Field name="filter1_4">(optional) Maximum value for the filter.</Field>
                    <Field name="filter2...">(optional) Same for the second filter.</Field>
                    <Field name="filter3...">(optional) Same for the third filter.</Field>
                    <Field name="xaxis1">(recommended) X axis for the scatter plot or histogram (Fe if omitted).</Field>
                    <Field name="xaxis2">(optional) The denominator element to complete a X axis ratio with xaxis1 (H if omitted)</Field>
                    <Field name="yaxis1">(recommended) Y axis for the scatter plot (Si if omitted).</Field>
                    <Field name="yaxis2">(optional) The denominator element to complete a Y axis ratio with yaxis1 (H if omitted)</Field>
                    <Field name="zaxis1">(optional) Z axis for the scatter plot (null if omitted).</Field>
                    <Field name="zaxis2">(optional) The denominator element to complete a Z axis ratio with zaxis1 (H if omitted)</Field>
                    <Field name="statistic">(optional) Choose whether to return the <code>median</code> or the <code>mean</code>. If omitted, the median is assumed.</Field>
                    <Field name="cat_action">(optional) Choose to <code>allow</code> or <code>exclude</code> given catalogs. If omitted, exclude is assumed.</Field>
                    <Field name="catalogs">
                        (optional) Catalog IDs to allow or exclude specific catalogs from data calculations. Separate
                        multiple catalogs with the semicolon character &quot;;&quot; See GET catalog to choose catalog IDs.
                    </Field>
                    <Field name="star_action">(optional) Choose to <code>allow</code> or <code>exclude</code> given stars. If omitted, exclude is assumed.</Field>
                    <Field name="star_list">
                        (optional) Stars to allow or exclude. Any name can be given, and names are case-insensitive and
                        spaces are removed. Separate multiple stars with the semicolon character &quot;;&quot;
                    </Field>
                    <Field name="normalize">(optional) Normalizes the histogram.</Field>
                    <Field name="solarnorm">
                        (optional) Solar normalization identifier. See GET solarnorm to choose a solar normalization.
                        If omitted, Lodders et al. 2009 is assumed.
                    </Field>
                    <Field name="return_nea_name">
                        (optional) if set to &quot;true&quot;, the scatter plot will have an additional field for the NEA
                        name if one was found by the Hypatia Catalog.
                    </Field>
                </Fields>
                <Fields title="Outputs">
                    <Field name="count">Number of stars or planets in the query.</Field>
                    <Field name="labels">Labels for each axis in the query.</Field>
                    <Field name="solarnorm">Information about the given solarnorm.</Field>
                    <Field name="values">(scatter only) An array of objects with name field and each the data under the fields xaxis, yaxis, (zaxis).</Field>
                    <Field name="all_hypatia">(histogram only) An array of values for each bin for all Hypatia stars.</Field>
                    <Field name="exo_hosts">(histogram only) An array of values for each bin for only the Hypatia stars that host planets.</Field>
                    <Field name="edges">(histogram only) The bin edges for each histogram array.</Field>
                </Fields>
                <Request url="/hypatia/api/v2/data/?xaxis1=Fe&yaxis1=Si"/>
                <Python>{`
import requests
entry = requests.get("https://hypatiacatalog.com/hypatia/api/v2/data/", params={"xaxis1":"Fe","yaxis1":"Si"})
print(entry.json())
`}</Python>
                <Result>{`
{
  "count": 5584,
  "labels": {
    "xaxis": "[Fe/H]",
    "yaxis": "[Si/H]"
  },
  "solarnorm": {
    "year": 2009,
    "author": "Lodders et al.",
    "values": {
      "H": 12,
      "He": 10.93,
      ...
      "Th_II": 0.08
    }
  },
  "values": [
    {
      "name": "HD 145417",
      "yaxis": -1.05,
      "xaxis": -1.22
    },
    {
      "name": "BD-08  4501",
      "yaxis": -1.28,
      "xaxis": -1.395
    },
    ...
  ]
}
`}</Result>
                <Request url="/hypatia/api/v2/data?mode=hist"/>
                <Python>{`
import requests
params = {"mode":"hist"}
entry = requests.get("https://hypatiacatalog.com/hypatia/api/v2/data", params=params)
print(entry.json())
`}</Python>
                <Result>{`
{
  "count": 11250,
  "labels": {
    "xaxis": "[Fe/H]",
    "yaxis": "Number of Stellar Systems"
  },
  "all_hypatia": [2, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 17, 47, 81, 131, 254, 1140, 6497, 3065, 12],
  "exo_hosts": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 51, 830, 699, 4],
  "edges": [-8.56, -8.0795, -7.599, -7.1185, -6.638, -6.1575, -5.677, -5.1965, -4.716, -4.2355, -3.755, -3.2745, -2.794, -2.3135, -1.833, -1.3525, -0.872, -0.391500000000001, 0.0890000000000004, 0.5695, 1.05]
}
`}</Result>
            </Entry>

            <Entry id="version-history" label="Version history" heading>
                <Field name="2.2.0">
                    August 15, 2024 - Major database engine and pipeline upgrades promoted a review and changes this
                    API model. However, we are committed to supporting our users and have worked to deliver the
                    improvements of the new database services to the framework of the existing API. Data is now
                    available on-demand and is no longer rate limiting or controlling access. Some of the field names
                    for this API have been changed to be more scientifically accurate; fields that were misleading or
                    never-implemented have been removed. If we broke something you were using, please let us know and
                    we will do our best to support you. We are building a new API to support other databases as well
                    as data-science and machine learning operations, and other application-specific API endpoints that
                    enable science will be considered.
                </Field>
                <Field name="2.1.1">
                    October 31, 2023 - <code>plusminus_error</code> is now a returned field for <code>composition</code> queries.
                    For stars with multiple abundance values, this is half of the absolute range of the data, for stars
                    with a single abundance value this is a representative error.
                </Field>
                <Field name="2.1.0">
                    April 21, 2023 - The &apos;composition&apos; API query has been redesigned to return data more quickly
                    and to efficiently use the server&apos;s resources. The format of the query parameters and returned
                    JSON are exactly the same.
                </Field>
                <Field name="2.0.2">Added support for {nea}. Fixed median value in GET composition.</Field>
                <Field name="2.0.1">Fixed <code>star_list</code> in GET data. Entering a Hipparcos or HD number by itself should return the correct star.</Field>
                <Field name="2.0.0">
                    A major update to the API to handle stars without Hipparcos IDs, asymmetrical errors in planet
                    properties, and non-numeric Henry Draper IDs. See above for full details.
                </Field>
                <Field name="1.0.1">Added clarification to GET element regarding multiple set requests.</Field>
                <Field name="1.0.0">Initial release.</Field>
            </Entry>

            <Entry id="reference" label="Reference" heading>
                This API is modeled on the <Ext href="https://github.com/toggl/toggl_api_docs/">Toggl API</Ext>.
                Further reference: <Ext href="https://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api">here</Ext> and{' '}
                <Ext href="https://semver.org/">here.</Ext>
            </Entry>
            </Definitions>
        </Page>
    );
}
