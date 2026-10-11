import type {Metadata} from "next";
import {Page, H1, P, Ext} from "@/components/text";

export const metadata: Metadata = {
    title: "Acknowledgements | Hypatia Catalog",
    description: "How to acknowledge and cite the Hypatia Catalog, and the people behind it.",
};

export default function AcknowledgementsPage() {
    return (
        <Page>
            <H1 id="acknowledgments">ACKNOWLEDGMENTS</H1>
            <P>If you have used the Hypatia Catalog in published research, please include the following acknowledgement:</P>
            {/* the acknowledgement to copy into a paper, set off from the page's own text */}
            <blockquote className="border-l-4 border-hyyellow pl-6 my-6 text-hypurple text-lg md:text-xl">
                The research shown here acknowledges use of the Hypatia Catalog, an online compilation of stellar
                abundance data as described in{' '}
                <Ext href="http://adsabs.harvard.edu/abs/2014AJ....148...54H">Hinkel et al. (2014, AJ, 148, 54)</Ext>.
            </blockquote>
            <P>
                Additionally, please cite the original Hypatia Catalog paper:{' '}
                <Ext href="https://ui.adsabs.harvard.edu/abs/2014AJ....148...54H/abstract">https://ui.adsabs.harvard.edu/abs/2014AJ....148...54H/</Ext>.
            </P>
            <hr className="border-hyblue my-8"/>
            <P>
                In the event that a small number of catalogs was used within an analysis, we highly encourage the
                citation of those individual papers. However, we still appreciate the acknowledgment of the Hypatia
                Catalog and Database, in order to give credit for the use of the website, internal algorithms, and
                availability of the data (since {'>'}50% of the catalogs were not available in machine-readable
                formats prior to this compilation).
            </P>
            <P>
                <Ext href="https://www.nataliehinkel.com">Dr. Natalie Hinkel</Ext> originally created the Hypatia
                Catalog and designed the science-data pipeline. She actively maintains the data and data compilation.
            </P>
            <P>Dr. Caleb Wheeler is the developer for the Hypatia Catalog website, database, API, and science-data pipeline.</P>
            <P>
                The original developer for the online Hypatia Catalog was Dan Burger, who was supported by Nitin
                Pasumarthy, Benjamin Knight, and Wendy Yu.
            </P>
            <P>Logo by Nahks Tr’Ehnl, who can be found at <Ext href="http://www.nahks.com">www.nahks.com</Ext>.</P>
            <P>Additional thanks to Dr. Garrett Somers.</P>
            <P>
                Please send any website or data updates, issues, or corrections to{' '}
                <Ext href="mailto:hypatiacatalog@gmail.com">hypatiacatalog@gmail.com</Ext>. You can also find us on
                Twitter via <Ext href="https://twitter.com/HypatiaCatalog">@hypatiacatalog.</Ext>
            </P>
        </Page>
    );
}
