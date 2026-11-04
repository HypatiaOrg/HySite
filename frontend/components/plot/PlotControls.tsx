"use client";
// The plot's own controls, under the plot: the histograms toggle, the bin size boxes and (density map) the colour
// scale, laid out as the web2py page had them. The bin size boxes of the scatter and targets pages only matter to
// the histograms the toggle shows, so they show and hide with it; the density map's bins are its cells, so its
// boxes stay. A box's warnings come from the API's bins (api.web2py.density: the "error" rule with a parameter
// that has no error) and from the figure (a logarithmic axis: Plotly chooses the bins); a width the API changed
// to fit the plotted range shows in its box.
import React from "react";
import type {Settings, SettingsSchema} from "@/lib/settings";
import {isOn} from "@/lib/settings";
import type {AxesBins} from "@/lib/plotTypes";
import type {AxisTypes} from "@/components/plot/figures";
import {PLOT_MARGIN_LEFT} from "@/components/plot/figures";
import {TextField} from "@/components/settings/Controls";
import type {PlotKind} from "@/components/plot/PlotPage";

// the bin size boxes of a page and the axis whose bins the API makes for each one
const BIN_BOXES_XY: Array<[string, "xaxis" | "yaxis", string]> = [
    ["xhist_bin_size", "xaxis", "X bin size"],
    ["yhist_bin_size", "yaxis", "Y bin size"],
];
const BIN_BOXES_HIST: Array<[string, "xaxis" | "yaxis", string]> = [["hist_bin_size", "xaxis", "Bin size"]];
// the toggle of each page's histograms along the axes
const TOGGLES: Partial<Record<PlotKind, string>> = {
    scatter: "show_scatter_hist",
    targets: "show_targets_hist",
    density: "show_xyhist",
};
// the rows are one width: a label and a control; the toggle's row holds the checkbox at its left and the palette
// menu at its right, so the menu ends where the bin size boxes below end
const LABEL_WIDTH = 85,
    CONTROL_WIDTH = 340,
    ROW_WIDTH = LABEL_WIDTH + 8 + CONTROL_WIDTH;

// a width as the box shows it: up to six significant digits, as the API's {size:g}
export const widthText = (size: number) => String(Number(size.toPrecision(6)));

type Props = {
    kind: PlotKind;
    schema: SettingsSchema;
    settings: Settings;
    bins: AxesBins | null | undefined;
    axisTypes: AxisTypes | undefined;
    onChange: (changes: Record<string, string>) => void;
};

export default function PlotControls({kind, schema, settings, bins, axisTypes, onChange}: Props) {
    const toggle = TOGGLES[kind];
    const boxes = kind === "hist" ? BIN_BOXES_HIST : BIN_BOXES_XY;
    const binsWithToggle = kind === "scatter" || kind === "targets";
    const binsShown = !binsWithToggle || (toggle !== undefined && isOn(settings, toggle));
    const keywords = schema.fields.xhist_bin_size?.keywords ?? [];
    const hint = `Float or keywords: (${keywords[0]} [default], ${keywords.slice(1).join(", ")})`;
    const logWarning = schema.words?.log_bins_warning ?? "Logged bins chosen automatically";

    // the warnings beside each box: the API's, then the figure's for a logarithmic axis (not on the density map,
    // whose axes are never logarithmic, nor on the histogram page)
    const warnings: Record<string, string> = {};
    for (const [box, axis] of boxes) {
        const notes: Array<string> = [];
        const warning = bins?.[axis]?.warning;
        if (warning) notes.push(warning);
        if (binsWithToggle && axisTypes?.[axis] === "log") notes.push(logWarning);
        if (notes.length) warnings[box] = notes.join(" ");
    }

    // a width the API changed to fit the plotted range shows in its box (the settings keep what was typed: the
    // API gives the same answer for it, so a shared link draws the same plot, and the note stays by the box)
    const shown = (box: string, axis: "xaxis" | "yaxis") => {
        const axisBins = bins?.[axis];
        return axisBins?.adjusted ? widthText(axisBins.size) : (settings[box] ?? "");
    };

    return (
        <form
            className="plot-controls text-sm max-w-full max-sm:!ml-0"
            style={{marginLeft: PLOT_MARGIN_LEFT, marginTop: -5, marginBottom: 20}}
            onSubmit={(event) => event.preventDefault()}
        >
            {(toggle || kind === "density") && (
                <div className="flex items-center justify-between mb-2 max-w-full" style={{width: ROW_WIDTH}}>
                    {toggle && (
                        <label className="inline-flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                id={toggle}
                                name={toggle}
                                checked={isOn(settings, toggle)}
                                onChange={(event) => onChange({[toggle]: String(event.target.checked)})}
                            />
                            <span>Show X and Y histograms</span>
                        </label>
                    )}
                    {kind === "density" && (
                        <span className="inline-flex items-center">
                            <label htmlFor="color_palette" className="font-bold mr-1.5">
                                Color palette
                            </label>
                            <select
                                id="color_palette"
                                name="color_palette"
                                value={settings.color_palette}
                                onChange={(event) => onChange({color_palette: event.target.value})}
                                className="form-control form-control-inline"
                            >
                                {(schema.fields.color_palette?.choices ?? []).map((choice) => (
                                    <option key={choice} value={choice}>
                                        {choice}
                                    </option>
                                ))}
                            </select>
                        </span>
                    )}
                </div>
            )}
            {boxes.map(([box, axis, label]) => (
                <div key={box} className="bin-size items-center mb-2" style={{display: binsShown ? "flex" : "none"}}>
                    <div className="flex items-center max-w-full" style={{width: ROW_WIDTH}}>
                        <label
                            htmlFor={box}
                            className="font-bold text-[#333] mr-2 flex-none"
                            style={{width: LABEL_WIDTH}}
                        >
                            {label}
                        </label>
                        <TextField
                            name={box}
                            value={shown(box, axis)}
                            placeholder={hint}
                            className="form-control flex-1"
                            onCommit={(value) => onChange({[box]: value})}
                        />
                    </div>
                    {warnings[box] && (
                        <span className="bin-warning text-[#a94442] ml-2.5" role="status">
                            {warnings[box]}
                        </span>
                    )}
                </div>
            ))}
        </form>
    );
}
