import {renderPlotPage, plotMetadata, type SearchParams} from "@/components/plot/renderPlotPage";

export const metadata = plotMetadata(
    "Scatter",
    "Plot any element ratio, stellar property or planet property of the Hypatia Catalog against another.",
);
// the settings are in the page URL, read for every request
export const dynamic = "force-dynamic";

export default function ScatterPage({searchParams}: {searchParams: SearchParams}) {
    return renderPlotPage("scatter", searchParams);
}
