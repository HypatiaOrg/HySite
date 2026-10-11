// The settings of the plot and table pages: the API's model (settings/) decides the names, defaults,
// kinds and choices; a page holds its current values as strings, exactly as the API and the page URL
// take them. Toggles are "true" or "false"; a list is its items joined by ";" (the table columns by ",").

export type FieldKind = "choice" | "number" | "toggle" | "list" | "text";

export type SettingsField = {
    kind: FieldKind,
    about: string,
    choices?: Array<string>,
    keywords?: Array<string>,
    default?: string | boolean | Array<string>,
};

export type SettingsSchema = {
    defaults: Record<string, string | boolean | Array<string>>,
    toggles: Array<string>,
    session_keys: Array<string>,
    fields: Record<string, SettingsField>,
    max_filters?: number,
};

// the most filters a request may carry (filter1 .. filterN), as the API's model says
export const maxFilters = (schema: SettingsSchema) => schema.max_filters ?? 3;

// the parts of a filter: the parameter, the denominator, the low and high ends, the inverse toggle
const FILTER_PARTS = ["1", "2", "3", "4", "inv"];
export const isFilterSetting = (name: string) => /^filter\d+_(1|2|3|4|inv)$/.test(name);

// the indexes of the filters that name a parameter
export function activeFilters(settings: Settings, max: number): Array<number> {
    const indexes: Array<number> = [];
    for (let index = 1; index <= max; index++) {
        if (settings[`filter${index}_1`] && settings[`filter${index}_1`] !== "none") indexes.push(index);
    }
    return indexes;
}

// the filters in use renumbered 1, 2, 3 ... with the others at their defaults, so a cleared filter leaves
// no gap and the page URL stays short
export function compactFilters(schema: SettingsSchema, settings: Settings): Settings {
    const defaults = defaultSettings(schema), max = maxFilters(schema);
    const active = activeFilters(settings, max);
    const result = {...settings};
    for (let index = 1; index <= max; index++) {
        const source = active[index - 1];
        for (const part of FILTER_PARTS) {
            const target = `filter${index}_${part}`;
            result[target] = source ? settings[`filter${source}_${part}`] : defaults[target];
        }
    }
    return result;
}

export type Settings = Record<string, string>;

const LIST_SEPARATOR: Record<string, string> = {tablecols: ","};
export const listSeparator = (name: string) => LIST_SEPARATOR[name] ?? ";";

function asString(name: string, value: string | boolean | Array<string> | undefined): string {
    if (value === undefined || value === null) return "";
    if (typeof value === "boolean") return value ? "true" : "false";
    if (Array.isArray(value)) return value.join(listSeparator(name));
    return String(value);
}

// what a fresh page starts with
export function defaultSettings(schema: SettingsSchema): Settings {
    const settings: Settings = {};
    for (const name of schema.toggles) settings[name] = "false";
    for (const [name, value] of Object.entries(schema.defaults)) settings[name] = asString(name, value);
    return settings;
}

export const isOn = (settings: Settings, name: string) => settings[name] === "true";
export const listOf = (settings: Settings, name: string) =>
    (settings[name] ?? "").split(listSeparator(name)).map((item) => item.trim()).filter((item) => item);

// the settings a page URL carries: only what differs from the defaults, under the API's own names
export function settingsFromSearchParams(schema: SettingsSchema, params: URLSearchParams): Settings {
    const settings = defaultSettings(schema);
    for (const [name, value] of params.entries()) {
        if (!(name in settings)) continue;
        settings[name] = schema.toggles.includes(name) ? String(["true", "1", "on"].includes(value.toLowerCase())) : value;
    }
    return settings;
}

export function searchParamsFromSettings(schema: SettingsSchema, settings: Settings): URLSearchParams {
    const defaults = defaultSettings(schema);
    const params = new URLSearchParams();
    for (const [name, value] of Object.entries(settings)) {
        if (name in defaults && value !== defaults[name]) params.set(name, value);
    }
    return params;
}

// an element id starts with a capital letter (Fe, Fe_II); a stellar or planet property does not
export const isElement = (name: string) => /^[A-Z]/.test(name);
