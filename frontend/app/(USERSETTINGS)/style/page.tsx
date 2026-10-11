// The style page: every piece of the site on one page, to review and try colors (components/palette.tsx).
// Not linked from the menu. It answers only while DEBUG is true (compose.yaml); to remove it for good,
// delete this folder and components/palette.tsx.
import type {Metadata} from "next";
import Link from "next/link";
import {notFound} from "next/navigation";
import {DEBUG} from "@/data/api_targets";
import {Page, H1, H2, P, Ul, Ext, In, DefinitionTable} from "@/components/text";
import {Palette} from "@/components/palette";
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

            <H1 id="caption">Caption</H1>
            <P>The caption under the home page&apos;s histogram: light blue on purple.</P>
            <p className="text-hyblue bg-hypurple indent-12 pt-2 pb-2 pl-6 pr-6 mb-8">
                Number of stars for which each element abundance has been measured.
            </p>
        </Page>
    );
}
