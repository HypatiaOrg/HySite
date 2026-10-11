// What the API's plot and table endpoints return (api.web2py.plots, api.web2py.table)

export type AxisInfo = {label: string; log: boolean; inverse: boolean};

export type ScatterData = {
    outputs: {name?: Array<string>; xaxis?: Array<number>; yaxis?: Array<number>; zaxis?: Array<number>};
    labels: Record<string, string>;
    axes: {xaxis: AxisInfo; yaxis: AxisInfo; zaxis?: AxisInfo};
    star_count: number | null;
    planet_count: number | null;
    is_loggable: Record<string, boolean>;
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
};

export type DensityBins = {start: number; end: number; size: number; mode: string};

export type DensityData = ScatterData & {
    bins: {xaxis: DensityBins; yaxis: DensityBins} | null;
    show_xyhist: boolean;
    color_pallet: string;
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
