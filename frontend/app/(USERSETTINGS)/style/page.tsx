// The style page: every piece of the site on one page, to review and try colors (components/palette.tsx).
// Not linked from the menu. It answers only while DEBUG is true (compose.yaml); to remove it for good,
// delete this folder and components/palette.tsx.
import type {Metadata} from "next";
import Link from "next/link";
import {notFound} from "next/navigation";
import {DEBUG} from "@/data/api_targets";
import {Page, H1, H2, P, Ul, Ext, In, DefinitionTable} from "@/components/text";
import {Palette} from "@/components/palette";
import StyleSamples from "@/components/style_samples";
import {columns} from "@/data/about_columns";

export const metadata: Metadata = {title: "Style | Hypatia Catalog"};
// DEBUG is read when the server runs, so the page is decided per request, not at build time
export const dynamic = 'force-dynamic';

export default function StylePage() {
    if (!DEBUG) {
        notFound();
    }
    return (
        <Page>
            <H1 id="colors">Colors</H1>
            <P>The six named colors of the site, from the theme in <code>app/globals.css</code>.</P>
            <Palette/>

            <H1 id="text">Text</H1>
            <P>
                A main heading above (purple), a subheading below (red), and this paragraph (grey) are the pieces
                every text page is built from. A link to <In href="/help">a page of this site</In> and a link to{' '}
                <Ext href="https://ui.adsabs.harvard.edu/abs/2014AJ....148...54H">another website</Ext> look the
                same; the second opens in a new tab.
            </P>
            <H2 id="subheading">A subheading</H2>
            <P>
                Stellar abundance information provides one of the primary tools for understanding everything from
                the evolution of the Milky Way galaxy to the structure and mineralogy of exoplanets. Lines of body
                text run no wider than this column so they stay easy to read.
            </P>
            <Ul>
                <li>a list item, in the paragraph style,</li>
                <li>and another, with <In href="/about">a link</In>.</li>
            </Ul>

            <H1 id="buttons">Buttons</H1>
            <P>The home page&apos;s call to action, in its resting and hover colors.</P>
            <div className="inline-block text-hyred border-hyred border-solid border-2 rounded-lg p-4 mb-8 text-2xl hover:bg-hygrey hover:border-hypurple hover:text-hyyellow">
                <Link href="/">Get Started »</Link>
            </div>

            <H1 id="table">Table</H1>
            <P>The first rows of the About page&apos;s column table. The header stays in view while the rows scroll.</P>
            <DefinitionTable rows={columns.slice(0, 6)} name="Sample rows of the column table"/>

            <H1 id="controls">Plot page controls</H1>
            <P>The pieces of the scatter, target lists, density and histogram pages: the parameter picker (click it), a
                choice, a text field, a toggle, the buttons in their three states, a notice, and the hover labels.</P>
            <StyleSamples/>

            <H1 id="caption">Caption</H1>
            <P>The caption under the home page&apos;s histogram: light blue on purple.</P>
            <p className="text-hyblue bg-hypurple indent-12 pt-2 pb-2 pl-6 pr-6 mb-8">
                Number of stars for which each element abundance has been measured.
            </p>

            <H1 id="decisions">Decisions to review</H1>
            <P>Choices made while porting the pages from web2py (October 2026), for review. Each says where it is changed.</P>
            <Ul>
                <li><b>Body text grey.</b> The theme&apos;s grey (#8A8A8A) on white measures 3.45:1; WCAG AA asks 4.5:1 for
                    normal text, so every page is below it, more so on the yellow and grey blocks. A darker grey such as
                    #6E6E6E passes at about 4.9:1. Try it with the picker above. Changed in <code>app/globals.css</code>.</li>
                <li><b>Two kinds of &quot;on&quot;.</b> A parameter picked for an axis or filter is purple on white; a column
                    that is in the data table is green (the theme&apos;s green, otherwise unused). The old site used
                    Bootstrap&apos;s blue and green. Changed in <code>components/settings/controls.tsx</code>.</li>
                <li><b>Headings and links share red.</b> Main headings are purple, subheadings and links are red, so a red
                    word in a paragraph is a link and a red line on its own is a subheading. Changed in{' '}
                    <code>components/text.tsx</code>.</li>
                <li><b>Callouts.</b> Light blue with a purple rule for a notice to know about (the API page, the form
                    notices); pale yellow for the Python to copy and the version notes, carrying on the old page&apos;s
                    yellow highlights. Changed in <code>components/api_docs.tsx</code> and <code>controls.tsx</code>.</li>
                <li><b>The plot page layout.</b> The figure keeps its 750 by 625 size with the form beside it, as before,
                    and the form drops below the figure on a narrow window. The grey box behind a loading plot, and the
                    half-opacity while it refreshes, are the old page&apos;s. Changed in <code>components/plot/PlotPage.tsx</code>.</li>
                <li><b>The parameter picker.</b> A panel under its button, leftwards over the plot like the old dropdown,
                    with the periodic table (an element and its ionized species side by side), then the stellar and
                    planet properties. The catalog list has a search box in place of the old select2 control.</li>
                <li><b>The data table.</b> Alternate rows tinted light blue, a header that stays in view, the sorted
                    column&apos;s name in red with an arrow, a star&apos;s SIMBAD link as an arrow after its name, and the
                    catalog values behind a cell as a tooltip. Changed in <code>components/table/DataTable.tsx</code>.</li>
                <li><b>The menu.</b> The current page is a white pill with purple text, as the old menu marked it; between
                    the plot pages the links carry the plot settings along. Changed in <code>components/nav_link.tsx</code>.</li>
                <li><b>The acknowledgement to copy</b> is set off as a quotation with a yellow rule. Changed in{' '}
                    <code>app/(USERSETTINGS)/acknowledgements/page.tsx</code>.</li>
                <li><b>Typeface.</b> Inter, from the Next.js site&apos;s original setup, for everything; the old site used
                    Bootstrap&apos;s Helvetica stack. Changed in <code>app/layout.tsx</code>.</li>
            </Ul>
        </Page>
    );
}
