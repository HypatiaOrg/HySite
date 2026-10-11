import {renderPlotPage, plotMetadata, type SearchParams} from "@/components/plot/renderPlotPage";

export const metadata = plotMetadata(
    "Target Lists",
    "The Hypatia Catalog's stars in the HWO, thin disk, thick disk and exoplanet host target lists.",
);
export const dynamic = "force-dynamic";

export default function TargetsPage({searchParams}: {searchParams: SearchParams}) {
    return renderPlotPage("targets", searchParams);
}
