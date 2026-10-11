import {renderPlotPage, plotMetadata, type SearchParams} from "@/components/plot/plot_page_server";

export const metadata = plotMetadata("Histogram", "A histogram of any element ratio or property, for all Hypatia Catalog stars and for the planet hosts.");
export const dynamic = 'force-dynamic';

export default function HistPage({searchParams}: {searchParams: SearchParams}) {
    return renderPlotPage("hist", searchParams);
}
