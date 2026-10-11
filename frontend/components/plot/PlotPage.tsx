'use client';
// A plot page: the settings form, the figure and the data table. The settings are the page's state and
// its URL (a shareable link); every change asks the API for the plot and the table again.
import React, {useCallback, useEffect, useMemo, useRef, useState} from "react";
import type {PlotSelectionEvent, PlotlyHTMLElement} from "plotly.js";
import type {Summary} from "@/data/summary";
import type {Settings, SettingsSchema} from "@/data/settings";
import {isOn, listOf, searchParamsFromSettings, compactFilters, isFilterSetting, activeFilters, maxFilters} from "@/data/settings";
import {fetchData, type ScatterData, type TargetsData, type HistData, type DensityData} from "@/data/plot_types";
import {scatterFigure, targetsFigure, histFigure, densityFigure, type Figure, PLOT_WIDTH, PLOT_HEIGHT} from "@/components/plot/figures";
import PlotlyFigure from "@/components/plot/PlotlyFigure";
import HoverLabels from "@/components/plot/HoverLabels";
import DataTable from "@/components/table/DataTable";
import Notices from "@/components/settings/Notices";
import {Toggle} from "@/components/settings/controls";
import {FilterRows, AxisRow, SolarNormRow, StatisticRow, CatalogsRow, StarsRow, TargetSetsRow, DensityRows, SubmitRow} from "@/components/settings/rows";
import {Label} from "@/components/settings/controls";

export type PlotKind = "scatter" | "targets" | "hist" | "density";

// what the current settings apply beyond the axes, in a line under the plot: a changed catalog or star
// list often leaves the star count as it was, so this says that the request carried it
function applied(settings: Settings, summary: Summary, schema: SettingsSchema): string {
    const parts: Array<string> = [];
    const catalogs = listOf(settings, "catalogs").length;
    if (catalogs) parts.push(`${catalogs} catalog${catalogs > 1 ? "s" : ""} ${settings.cat_action === "only" ? "allowed only" : "excluded"}`);
    const stars = listOf(settings, "star_list").length;
    if (stars) parts.push(`${stars} star${stars > 1 ? "s" : ""} ${settings.star_action === "only" ? "allowed only" : "excluded"}`);
    const filters = activeFilters(settings, maxFilters(schema)).length;
    if (filters) parts.push(`${filters} filter${filters > 1 ? "s" : ""}`);
    const norm = summary.solarnorms.find((item) => item.id === settings.solarnorm);
    parts.push(norm ? `${norm.author}${norm.year ? ` (${norm.year})` : ""} normalization` : `${settings.solarnorm} normalization`);
    parts.push(settings.statistic === "mean" ? "mean of the catalogs" : "median of the catalogs");
    return parts.join("; ");
}

type Props = {kind: PlotKind, schema: SettingsSchema, summary: Summary, initialSettings: Settings};

export default function PlotPage({kind, schema, summary, initialSettings}: Props) {
    const [settings, setSettings] = useState<Settings>(initialSettings);
    // what the API answered, and for which settings: the plot is loading while they are not the current ones
    const [answer, setAnswer] = useState<{settings: Settings, data: ScatterData | TargetsData | HistData | DensityData | null, error: string | null} | null>(null);
    const data = answer?.data ?? null, error = answer?.error ?? null;
    const loading = answer?.settings !== settings;
    const [plot, setPlot] = useState<PlotlyHTMLElement | null>(null);
    const request = useRef(0);

    const change = useCallback((changes: Record<string, string>) => {
        setSettings((current) => {
            const next = {...current, ...changes};
            // a cleared or added filter: the filters in use are renumbered from 1
            return Object.keys(changes).some(isFilterSetting) ? compactFilters(schema, next) : next;
        });
    }, [schema]);

    // the page URL follows the settings, so the plot is a link to share
    useEffect(() => {
        const query = searchParamsFromSettings(schema, settings).toString();
        const url = window.location.pathname + (query ? "?" + query : "");
        if (url !== window.location.pathname + window.location.search) window.history.replaceState(null, "", url);
    }, [schema, settings]);

    // the plot's data, asked for a moment after the last change
    useEffect(() => {
        const id = ++request.current;
        const timer = setTimeout(() => {
            fetchData<ScatterData | TargetsData | HistData | DensityData>(kind, settings)
                .then((result) => { if (id === request.current) setAnswer({settings, data: result, error: null}); })
                .catch((problem: Error) => { if (id === request.current) setAnswer((current) => ({settings, data: current?.data ?? null, error: problem.message})); });
        }, 300);
        return () => clearTimeout(timer);
    }, [kind, settings]);

    const gridlines = isOn(settings, "gridlines");
    const figure: Figure | null = useMemo(() => {
        if (!data) return null;
        if (kind === "scatter") return scatterFigure(data as ScatterData, gridlines);
        if (kind === "targets") return targetsFigure(data as TargetsData, gridlines);
        if (kind === "density") return densityFigure(data as DensityData, gridlines);
        return histFigure(data as HistData, isOn(settings, "normalize"), isOn(settings, "xaxisinv"), gridlines);
    }, [kind, data, gridlines, settings]);

    // a box or lasso selection puts the selected stars into the star list
    const onSelected = useCallback((event: PlotSelectionEvent | undefined) => {
        if (!event || !plot) return;
        const traces = (plot as unknown as {data: Array<{text?: Array<string>}>}).data;
        const names = event.points.map((point) => traces[point.curveNumber]?.text?.[point.pointNumber]).filter((name): name is string => Boolean(name));
        if (names.length) change({star_list: names.join(";"), star_action: "only"});
    }, [plot, change]);

    const forceRefresh = () => setSettings((current) => ({...current}));

    return (
        <div className="px-4 pb-8">
            <div className="flex flex-wrap gap-6 justify-center">
                <div style={{width: PLOT_WIDTH, maxWidth: "100%"}}>
                <div className={"relative flex items-center justify-center bg-hygrey/20 transition-opacity " + (loading ? "opacity-50" : "")}
                     style={{height: kind === "density" ? 650 : PLOT_HEIGHT}}>
                    {error && <div className="text-hyred text-xl font-semibold p-4">The plot could not be loaded: {error}</div>}
                    {!error && data && !figure && <div className="text-xl font-semibold text-hygrey">No data points to display</div>}
                    {!error && !data && <div className="text-xl font-semibold text-hygrey">Loading...</div>}
                    {figure && (
                        <div className="bg-white">
                            <PlotlyFigure data={figure.data} layout={figure.layout} onSelected={onSelected} onDrawn={setPlot}/>
                            {figure.hoverLabels && <HoverLabels plot={plot} labels={figure.hoverLabels}/>}
                        </div>
                    )}
                </div>
                {/* what the plot was made with, beyond its axes */}
                <p className={"text-center text-sm text-hygrey mt-2 " + (loading ? "opacity-50" : "")} aria-live="polite">
                    {loading ? "Updating: " : "Showing: "}{applied(settings, summary, schema)}
                </p>
                </div>

                <form className="w-[29rem] max-w-full" onSubmit={(event) => { event.preventDefault(); forceRefresh(); }}>
                    <Notices settings={settings}/>
                    <FilterRows schema={schema} summary={summary} settings={settings} onChange={change}/>
                    <AxisRow axis="x" label="X-axis:" summary={summary} settings={settings} onChange={change} allowLog={kind !== "hist"}/>
                    {kind !== "hist" && <AxisRow axis="y" label="Y-axis:" summary={summary} settings={settings} onChange={change}/>}
                    {kind === "scatter" && <AxisRow axis="z" label="Z-axis (color):" summary={summary} settings={settings} onChange={change} allowNone/>}
                    {kind === "hist" && (
                        <div className="mb-3"><Toggle name="normalize" label="Normalize the histogram" checked={isOn(settings, "normalize")} onChange={(on) => change({normalize: String(on)})}/></div>
                    )}
                    {kind === "targets" && <TargetSetsRow summary={summary} settings={settings} onChange={change}/>}
                    {kind === "density" && <DensityRows schema={schema} settings={settings} onChange={change}/>}
                    <SolarNormRow summary={summary} settings={settings} onChange={change}/>
                    <StatisticRow settings={settings} onChange={change}/>
                    <CatalogsRow summary={summary} settings={settings} onChange={change}/>
                    <StarsRow settings={settings} onChange={change}/>
                    <div className="mb-3"><Toggle name="gridlines" label="Show gridlines" checked={gridlines} onChange={(on) => change({gridlines: String(on)})}/></div>
                    <SubmitRow onSubmit={forceRefresh}/>
                </form>
            </div>

            <DataTable summary={summary} settings={settings} onChange={change} showTargets={kind === "targets"}/>
        </div>
    );
}
