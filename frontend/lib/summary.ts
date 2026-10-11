// The catalog summary the API serves at summary/: what the forms, the plots and the table are built from

export type ColumnInfo = {label: string; hover: string; units?: string; decimals?: number};

export type Catalog = {id: string; author: string; year: number | null; original_norm_id?: string};

export type SolarNorm = {id: string; author: string; year: number | null; notes?: string};

export type ElementInfo = {element_id: string; element_name: string; abbreviation: string};

export type TargetList = {
    handle: string;
    title: string;
    description: string;
    ref: string;
    color: string;
    fill_alpha: number;
    line_alpha: number;
    marker: string;
    has_names: boolean;
    version?: string;
    date?: string;
};

export type Summary = {
    units_and_fields: Record<string, ColumnInfo>;
    stellar_param_types: Array<string>;
    planet_param_types: Array<string>;
    ranked_string_params: Record<string, string>;
    catalogs: Array<Catalog>;
    solarnorms: Array<SolarNorm>;
    element_data: Array<ElementInfo>;
    representative_error: Record<string, number>;
    targets: Record<string, TargetList>;
};

// the name to show for a parameter, element or column handle
export function labelOf(summary: Summary, handle: string): string {
    if (handle === "none") return "none";
    const column = summary.units_and_fields[handle];
    if (column) return column.label;
    const element = summary.element_data.find((item) => item.element_id === handle);
    if (element) return element.abbreviation.replace("_", " ");
    return handle.replace("_", " ");
}

export function hoverOf(summary: Summary, handle: string): string {
    const column = summary.units_and_fields[handle];
    if (column) return column.hover;
    const element = summary.element_data.find((item) => item.element_id === handle);
    if (element) return element.element_name;
    return handle;
}
