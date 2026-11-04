// What the API's plot and table endpoints return (api.web2py.plots, api.web2py.table)

export type AxisInfo = {label: string; log: boolean; inverse: boolean};

// one axis's histogram bins (api.web2py.density.axis_bins): the range, the width and how it was chosen; a
// warning when the "error" rule had no error to use, and "widened" or "cut" when the width was changed to
// fit the range (the page puts the width used into the bin size box)
export type Bins = {start: number; end: number; size: number; mode: string; warning?: string; adjusted?: string};
export type AxesBins = {xaxis: Bins; yaxis: Bins};

export type ScatterData = {
    outputs: {name?: Array<string>; xaxis?: Array<number>; yaxis?: Array<number>; zaxis?: Array<number>};
    labels: Record<string, string>;
    axes: {xaxis: AxisInfo; yaxis: AxisInfo; zaxis?: AxisInfo};
    star_count: number | null;
    planet_count: number | null;
    is_loggable: Record<string, boolean>;
    // the bins of the optional histograms along the axes
    bins?: AxesBins | null;
};

export type Layer = {
    group: string;
    label: string;
    color: string;
    fill_alpha: number;
    line_alpha: number;
    marker: string;
    x: Array<number>;
    y: Array<number>;
    names: Array<string>;
    handles: Array<Array<string>>;
};

export type TargetsData = ScatterData & {layers: Array<Layer>; number_of_targets: number};

export type HistData = {
    labels: {xaxis: string; yaxis: string};
    series: Array<{id: string; label: string; color: string; counts: Array<number>}>;
    edges: Array<number>;
    x_range: Array<number> | null;
    bins?: Bins | null;
};

export type DensityData = ScatterData & {
    bins: AxesBins | null;
    show_xyhist: boolean;
    color_palette: string;
    color_scale: Array<[number, string]> | string;
    histogram_color: string;
    bin_tags: Array<string>;
};

export type TableData = {
    columns: Array<string>;
    rows: Array<Array<string | Array<string>>>;
    hover: Array<Array<string | null>>;
    status: string;
    totalRows: number;
    moreRows: boolean;
    canLoadAll: boolean;
    star_count: number | null;
    planet_count: number | null;
};
