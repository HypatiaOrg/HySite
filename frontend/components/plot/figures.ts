// The figures, as Plotly data and layout, from what the API returns. The API decided the data, the
// target layers, the histogram series and the axes; this only draws, as models/plot_plotly.py did.
import type {Data, Layout} from "plotly.js";
import type {ScatterData, TargetsData, HistData} from "@/data/plot_types";

export const HYPATIA_PURPLE = "#4E11B7";
export const PLOT_WIDTH = 750;
export const PLOT_HEIGHT = 625;
const AXIS_FONT_SIZE = 16;  // pixels: the 12pt of the Bokeh plots
const MARGIN = 0.10;        // of the data range, on each side
// the Bokeh marker names of the catalog summary's target metadata, as Plotly symbols
const MARKERS: Record<string, string> = {
    circle: "circle", square: "square", diamond: "diamond", triangle: "triangle-up", inverted_triangle: "triangle-down",
    plus: "cross", cross: "cross", x: "x", star: "star", asterisk: "asterisk", square_pin: "square", hex: "hexagon",
    dot: "circle", dash: "line-ew",
};

export type Figure = {data: Array<Data>, layout: Partial<Layout>, hoverLabels?: Record<string, string>};

// the range and type of an axis: the data with a margin on each side; a log axis starts at the smallest
// positive value (its range in powers of ten, as Plotly wants it) and is linear when no value is positive
export function axisRange(values: Array<number>, doLog = false, inverse = false, lowMargin = MARGIN, highMargin = MARGIN):
    {range: [number, number], type: "linear" | "log"} {
    let vMin = Infinity, vMax = -Infinity;
    for (const value of values) { if (value < vMin) vMin = value; if (value > vMax) vMax = value; }
    if (!Number.isFinite(vMin)) { vMin = 0; vMax = 0; }
    if (vMin === vMax) { vMin -= 1; vMax += 1; }
    const diff = vMax - vMin;
    let low = vMin - lowMargin * diff, high = vMax + highMargin * diff;
    let type: "linear" | "log" = "linear";
    if (doLog) {
        let minPositive = Infinity, maxPositive = -Infinity;
        for (const value of values) if (value > 0) { if (value < minPositive) minPositive = value; if (value > maxPositive) maxPositive = value; }
        if (Number.isFinite(minPositive)) {
            low = Math.log10(minPositive);
            high = Math.log10(Math.max(high, maxPositive));
            type = "log";
        }
    }
    return {range: inverse ? [high, low] : [low, high], type};
}

// what every axis gets: the label (underscores as spaces), the font size, the gridlines toggle
export function axisStyle(label: string | null, gridlines: boolean) {
    return {
        title: {text: label ? label.replace(/_/g, " ") : undefined, font: {size: AXIS_FONT_SIZE}},
        tickfont: {size: AXIS_FONT_SIZE}, showgrid: gridlines, gridcolor: "#e5e5e5", zeroline: false,
        showline: true, linecolor: "black", ticks: "outside" as const,
    };
}

// the "Hypatia Catalog <date>" note in the bottom left corner
export function citation() {
    const date = new Date().toISOString().slice(0, 10);
    return {text: "Hypatia Catalog " + date, xref: "paper" as const, yref: "paper" as const, x: 0, y: 0,
            xanchor: "left" as const, yanchor: "bottom" as const, xshift: 10, yshift: 10, showarrow: false, opacity: 0.5};
}

const baseLayout = (): Partial<Layout> => ({
    width: PLOT_WIDTH, height: PLOT_HEIGHT, paper_bgcolor: "white", plot_bgcolor: "white",
    margin: {l: 70, r: 30, t: 50, b: 60},
});

// the scatter plot; with a z axis, the points are coloured on a Viridis scale with a colour bar
export function scatterFigure(data: ScatterData, gridlines: boolean): Figure | null {
    const x = data.outputs.xaxis ?? [], y = data.outputs.yaxis ?? [], names = data.outputs.name ?? [];
    if (!x.length) return null;
    const axes = data.axes;
    const labels: Record<string, string> = {x: axes.xaxis.label || "X Axis", y: axes.yaxis.label || "Y Axis"};
    const z = data.outputs.zaxis ?? [];
    const hasZ = Boolean(axes.zaxis) && z.length > 0;
    const marker: Record<string, unknown> = {size: 8, color: HYPATIA_PURPLE, opacity: 0.5, line: {color: HYPATIA_PURPLE, width: 1}};
    let customdata: Array<number> | undefined;
    if (hasZ && axes.zaxis) {
        labels.z = axes.zaxis.label || "Z Axis";
        customdata = z;
        const colorbar: Record<string, unknown> = {title: {text: labels.z.replace(/_/g, " "), side: "right"}, len: 0.4, thickness: 15,
                                                   outlinecolor: "#cccccc", outlinewidth: 1};
        let color: Array<number> = z;
        // a log colour scale: the colours follow log10 of the value, the colour bar's ticks show the values
        if (axes.zaxis.log && z.every((value) => value > 0)) {
            color = z.map((value) => Math.log10(value));
            const powers: Array<number> = [];
            for (let power = Math.ceil(Math.min(...color)); power <= Math.floor(Math.max(...color)); power++) powers.push(power);
            colorbar.tickvals = powers;
            colorbar.ticktext = powers.map((power) => String(10 ** power));
        }
        Object.assign(marker, {color, colorscale: "Viridis", reversescale: axes.zaxis.inverse, showscale: true, colorbar, line: {width: 0}});
    }
    // WebGL points: an SVG plot of ten thousand markers is slow to draw and to hover over
    const trace = {type: "scattergl", x, y, mode: "markers", marker, text: names, customdata, hoverinfo: "skip", showlegend: false} as unknown as Data;
    const xr = axisRange(x, axes.xaxis.log, axes.xaxis.inverse), yr = axisRange(y, axes.yaxis.log, axes.yaxis.inverse);
    const title = data.planet_count !== null && data.planet_count !== undefined
        ? `${data.planet_count} planets selected from ${data.star_count} stars`
        : `${data.star_count} stars selected`;
    const layout: Partial<Layout> = {
        ...baseLayout(), hovermode: false,
        xaxis: {range: xr.range, type: xr.type, ...axisStyle(labels.x, gridlines)},
        yaxis: {range: yr.range, type: yr.type, ...axisStyle(labels.y, gridlines)},
        title: {text: title, x: 0.5, xanchor: "center"}, annotations: [citation()],
    };
    return {data: [trace], layout, hoverLabels: labels};
}

// the targets plot: one trace per layer the API made, with a legend entry each; a click on an entry hides its layer
export function targetsFigure(data: TargetsData, gridlines: boolean): Figure | null {
    if (!data.layers?.length) return null;
    const axes = data.axes;
    const labels: Record<string, string> = {x: axes.xaxis.label || "X Axis", y: axes.yaxis.label || "Y Axis"};
    const traces = data.layers.map((layer) => ({
        type: "scattergl", x: layer.x, y: layer.y, mode: "markers", name: layer.label, text: layer.names, hoverinfo: "skip",
        marker: {symbol: MARKERS[layer.marker] ?? "circle", size: 8, color: layer.color, opacity: layer.fill_alpha, line: {color: layer.color, width: 1}},
    } as unknown as Data));
    const x = data.outputs.xaxis ?? [], y = data.outputs.yaxis ?? [];
    // room below the points for the legend, as the Bokeh plot had
    const xr = axisRange(x, axes.xaxis.log, axes.xaxis.inverse), yr = axisRange(y, axes.yaxis.log, axes.yaxis.inverse, 3 * MARGIN);
    const layout: Partial<Layout> = {
        ...baseLayout(), hovermode: false,
        xaxis: {range: xr.range, type: xr.type, ...axisStyle(labels.x, gridlines)},
        yaxis: {range: yr.range, type: yr.type, ...axisStyle(labels.y, gridlines)},
        title: {text: `${data.number_of_targets} Targets selected`, x: 0.5, xanchor: "center"},
        legend: {orientation: "h", x: 1, xanchor: "right", y: 0, yanchor: "bottom", bgcolor: "rgba(255,255,255,0.3)",
                 itemclick: "toggle", itemdoubleclick: "toggleothers"},
        annotations: [citation()],
    };
    return {data: traces, layout, hoverLabels: labels};
}

// the histogram: one bar series per entry the API made, over the API's bin edges
export function histFigure(data: HistData, normalize: boolean, inverse: boolean, gridlines: boolean): Figure | null {
    if (!data.x_range || !data.series?.length) return null;
    const edges = data.edges;
    const centres = edges.slice(0, -1).map((edge, index) => (edge + edges[index + 1]) / 2);
    const widths = edges.slice(0, -1).map((edge, index) => edges[index + 1] - edge);
    const xLabel = data.labels.xaxis || "X Axis";
    const yLabel = normalize ? "Relative Frequency" : "Number of Stellar Systems";
    const opacity = normalize ? 0.5 : 1.0;
    const maxAll = Math.max(...data.series[0].counts);
    const traces = data.series.map((series) => ({
        type: "bar", x: centres, y: series.counts, width: widths, name: series.label, opacity,
        marker: {color: series.color, line: {color: "black", width: 1}},
        customdata: edges.slice(0, -1).map((edge, index) => [edge, edges[index + 1]]),
        hovertemplate: `${xLabel} %{customdata[0]:.2f} to %{customdata[1]:.2f}<br>%{y}<extra>%{fullData.name}</extra>`,
    } as unknown as Data));
    const range = inverse ? [data.x_range[1], data.x_range[0]] : [data.x_range[0], data.x_range[1]];
    const layout: Partial<Layout> = {
        ...baseLayout(),
        xaxis: {range, ...axisStyle(xLabel, gridlines)},
        yaxis: {range: [0, maxAll * 1.2], ...axisStyle(yLabel, gridlines)},
        barmode: "overlay", bargap: 0, annotations: [citation()],
    };
    return {data: traces, layout};
}
