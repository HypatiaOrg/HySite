'use client';
// A Plotly figure in a div. plotly.js is large, so it is loaded in the browser the first time a figure
// is drawn, never on the server or on the text pages.
import {useEffect, useRef, useState} from "react";
import type {Data, Layout, Config, PlotSelectionEvent, PlotlyHTMLElement} from "plotly.js";

type PlotlyModule = typeof import("plotly.js-dist-min");
let plotlyPromise: Promise<PlotlyModule> | null = null;
export function loadPlotly(): Promise<PlotlyModule> {
    if (!plotlyPromise) {
        plotlyPromise = import("plotly.js-dist-min").then((module) => (module.default ?? module) as unknown as PlotlyModule);
    }
    return plotlyPromise;
}

export type FigureProps = {
    data: Array<Data>,
    layout: Partial<Layout>,
    config?: Partial<Config>,
    // a box or lasso selection
    onSelected?: (event: PlotSelectionEvent | undefined) => void,
    // the drawn plot, for the hover labels
    onDrawn?: (plot: PlotlyHTMLElement | null) => void,
};

export default function PlotlyFigure({data, layout, config, onSelected, onDrawn}: FigureProps) {
    const divRef = useRef<HTMLDivElement>(null);
    const [plotly, setPlotly] = useState<PlotlyModule | null>(null);
    // the latest callbacks, without redrawing the figure when they change
    const selectedRef = useRef(onSelected);
    const drawnRef = useRef(onDrawn);
    useEffect(() => {
        selectedRef.current = onSelected;
        drawnRef.current = onDrawn;
    });

    useEffect(() => {
        let active = true;
        loadPlotly().then((module) => { if (active) setPlotly(module); });
        return () => { active = false; };
    }, []);

    useEffect(() => {
        const div = divRef.current;
        if (!plotly || !div) return;
        let drawn = false;
        plotly.react(div, data, layout, {responsive: false, displaylogo: false, ...config}).then(() => {
            drawn = true;
            const plot = div as unknown as PlotlyHTMLElement;
            plot.removeAllListeners?.("plotly_selected");
            plot.on("plotly_selected", (event) => selectedRef.current?.(event));
            drawnRef.current?.(plot);
        });
        return () => {
            if (drawn) drawnRef.current?.(null);
        };
    }, [plotly, data, layout, config]);

    useEffect(() => {
        const div = divRef.current;
        return () => { if (div && plotly) plotly.purge(div); };
    }, [plotly]);

    return <div ref={divRef} className="mx-auto"/>;
}
