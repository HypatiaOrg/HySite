'use client';
// The hover labels of the points plots: the stars within a few pixels of the cursor, stacked in columns
// that fill the window's height, as Bokeh's hover tool stacked them; the nearest 25, headed by
// "Showing 25 of N Stars" when there are more. Plotly's own hover shows one point per trace, so the
// figure has hovermode off and this searches the traces' arrays instead, once per animation frame.
import React, {useEffect, useRef, useState} from "react";
import type {PlotlyHTMLElement} from "plotly.js";

const MAX_LABELS = 25;
const RADIUS = 4;  // pixels: a marker's radius (size 8)

type Found = {name: string, text: string};
type Shown = {items: Array<Found>, total: number, x: number, y: number};

// Plotly's drawn axes, with their data-to-pixel functions
type FullLayout = {
    xaxis?: {d2p: (value: number) => number}, yaxis?: {d2p: (value: number) => number},
    _size?: {l: number, t: number, w: number, h: number},
};
type Trace = {x: ArrayLike<number>, y: ArrayLike<number>, customdata?: ArrayLike<number>, text?: Array<string>};

export default function HoverLabels({plot, labels}: {plot: PlotlyHTMLElement | null, labels: Record<string, string>}) {
    const [shown, setShown] = useState<Shown | null>(null);
    const boxRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!plot) return;
        const element = plot as unknown as HTMLElement & {_fullLayout?: FullLayout, _fullData?: Array<{visible: boolean | string}>, data: Array<Trace>};
        let pending: MouseEvent | null = null;
        const hide = () => setShown(null);
        const show = (event: {clientX: number, clientY: number}) => {
            const layout = element._fullLayout;
            if (!layout?.xaxis?.d2p || !layout.yaxis?.d2p || !layout._size) { hide(); return; }
            const box = element.getBoundingClientRect();
            const px = event.clientX - box.left - layout._size.l, py = event.clientY - box.top - layout._size.t;
            if (px < 0 || py < 0 || px > layout._size.w || py > layout._size.h) { hide(); return; }
            const found: Array<[number, number, number]> = [];
            for (let c = 0; c < element.data.length; c++) {
                if (element._fullData?.[c] && element._fullData[c].visible !== true) continue;  // hidden from the legend
                const trace = element.data[c];
                for (let i = 0; i < trace.x.length; i++) {
                    const dx = layout.xaxis.d2p(trace.x[i]) - px, dy = layout.yaxis.d2p(trace.y[i]) - py, d = dx * dx + dy * dy;
                    if (d <= RADIUS * RADIUS) found.push([d, c, i]);
                }
            }
            if (!found.length) { hide(); return; }
            found.sort((a, b) => a[0] - b[0]);
            const items = found.slice(0, MAX_LABELS).map(([, c, i]) => {
                const trace = element.data[c];
                let text = `${labels.x} = ${Number(trace.x[i]).toFixed(2)}, ${labels.y} = ${Number(trace.y[i]).toFixed(2)}`;
                if (trace.customdata && labels.z) text += `, ${labels.z} = ${Number(trace.customdata[i]).toFixed(2)}`;
                return {name: trace.text?.[i] ?? "", text};
            });
            setShown({items, total: found.length, x: event.clientX, y: event.clientY});
        };
        const onMove = (event: MouseEvent) => {
            pending = event;
            window.requestAnimationFrame(() => { if (pending) { show(pending); pending = null; } });
        };
        // a tap on a touch screen shows the labels too, until the next tap (Plotly takes the touch events
        // for its own dragging, so the tap is read as the touch ends, not as a click)
        const onTouch = (event: TouchEvent) => {
            const touch = event.changedTouches[0];
            if (touch) show({clientX: touch.clientX, clientY: touch.clientY});
        };
        element.addEventListener("mousemove", onMove);
        element.addEventListener("mouseleave", hide);
        element.addEventListener("touchend", onTouch);
        return () => {
            element.removeEventListener("mousemove", onMove);
            element.removeEventListener("mouseleave", hide);
            element.removeEventListener("touchend", onTouch);
        };
    }, [plot, labels]);

    // next to the cursor, kept inside the window; the labels in columns that fill the window's height
    useEffect(() => {
        const box = boxRef.current;
        if (!box || !shown) return;
        const top = Math.max(4, Math.min(shown.y + 12, window.innerHeight - box.offsetHeight - 4));
        let left = shown.x + 12;
        if (left + box.offsetWidth > window.innerWidth) left = Math.max(4, shown.x - 12 - box.offsetWidth);
        box.style.top = `${top}px`;
        box.style.left = `${left}px`;
    }, [shown]);

    if (!shown) return null;
    const itemHeight = 34;
    const perColumn = Math.max(1, Math.floor((window.innerHeight - 24) / itemHeight));
    const columns: Array<Array<Found>> = [];
    for (let start = 0; start < shown.items.length; start += perColumn) columns.push(shown.items.slice(start, start + perColumn));
    return (
        <div ref={boxRef} className="fixed z-50 pointer-events-none bg-white/95 border border-hygrey rounded px-1.5 py-0.5 text-xs text-left whitespace-nowrap leading-tight text-[#222]">
            {shown.total > MAX_LABELS && <div className="py-0.5 text-hygrey">Showing {MAX_LABELS} of {shown.total} Stars</div>}
            {columns.map((column, index) => (
                <div key={index} className="inline-block align-top px-1.5">
                    {column.map((item, i) => (
                        <div key={i} className="py-0.5 border-t border-[#ddd]"><b>{item.name}</b><br/>{item.text}</div>
                    ))}
                </div>
            ))}
        </div>
    );
}
