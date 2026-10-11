// What the hover labels and the selection need from a drawn Plotly figure. Plotly keeps the drawn axes
// (data to pixel) and the traces' arrays on the element without types; the casts are here and nowhere else.
import type {PlotlyHTMLElement} from "plotly.js";

type DrawnAxis = {d2p: (value: number) => number};
type Trace = {x: ArrayLike<number>, y: ArrayLike<number>, customdata?: ArrayLike<number>, text?: Array<string>};
type Drawn = {
    _fullLayout?: {xaxis?: DrawnAxis, yaxis?: DrawnAxis, _size?: {l: number, t: number, w: number, h: number}},
    _fullData?: Array<{visible: boolean | string}>,
    data: Array<Trace>,
};

const drawn = (plot: PlotlyHTMLElement) => plot as unknown as HTMLElement & Drawn;

// the plot area on the page, with the axes that turn a value into a pixel; null until the figure is drawn
export function plotArea(plot: PlotlyHTMLElement): {left: number, top: number, width: number, height: number, xaxis: DrawnAxis, yaxis: DrawnAxis} | null {
    const layout = drawn(plot)._fullLayout;
    if (!layout?.xaxis?.d2p || !layout.yaxis?.d2p || !layout._size) return null;
    const box = plot.getBoundingClientRect();
    return {left: box.left + layout._size.l, top: box.top + layout._size.t, width: layout._size.w, height: layout._size.h,
            xaxis: layout.xaxis, yaxis: layout.yaxis};
}

// the traces' arrays, as given to Plotly
export const traces = (plot: PlotlyHTMLElement): Array<Trace> => drawn(plot).data;

// false for a layer hidden from the legend
export const traceVisible = (plot: PlotlyHTMLElement, curve: number): boolean =>
    drawn(plot)._fullData?.[curve] ? drawn(plot)._fullData![curve].visible === true : true;

// the star's name behind a point
export const pointName = (plot: PlotlyHTMLElement, curve: number, point: number): string | undefined =>
    drawn(plot).data[curve]?.text?.[point];
