// What every plot page does on the server: fetch the settings model and the catalog summary, read the
// settings from the page URL, and hand them to the page component
import type {Metadata} from "next";
import {getSettingsSchema, getSummary} from "@/lib/api.server";
import {settingsFromSearchParams} from "@/lib/settings";
import PlotPage, {type PlotKind} from "@/components/plot/PlotPage";

export type SearchParams = Promise<Record<string, string | Array<string> | undefined>>;

export function plotMetadata(title: string, description: string): Metadata {
    return {title: `${title} | Hypatia Catalog`, description};
}

export async function renderPlotPage(kind: PlotKind, searchParams: SearchParams) {
    const [schema, summary, params] = await Promise.all([getSettingsSchema(), getSummary(), searchParams]);
    const query = new URLSearchParams();
    for (const [name, value] of Object.entries(params)) {
        if (typeof value === "string") query.set(name, value);
    }
    return (
        <PlotPage
            kind={kind}
            schema={schema}
            summary={summary}
            initialSettings={settingsFromSearchParams(schema, query)}
        />
    );
}
