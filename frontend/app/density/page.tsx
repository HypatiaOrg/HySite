import {renderPlotPage, plotMetadata, type SearchParams} from "@/components/plot/renderPlotPage";

export const metadata = plotMetadata("Density Map", "A density map of any two element ratios or properties of the Hypatia Catalog, with histograms along the axes.");
export const dynamic = 'force-dynamic';

export default function DensityPage({searchParams}: {searchParams: SearchParams}) {
    return renderPlotPage("density", searchParams);
}
