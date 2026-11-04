"use client";
// The rows of the plot settings form: a filter, an axis, the catalogs, the stars, the target sets
import React, {useMemo, useRef, useState} from "react";
import type {Summary} from "@/lib/summary";
import type {Settings, SettingsSchema} from "@/lib/settings";
import {isOn, listOf, activeFilters, maxFilters} from "@/lib/settings";
import ParameterPicker from "@/components/settings/ParameterPicker";
import {Ext} from "@/components/Text";
import {Toggle, Select, TextField, Label, labelStyle, inputStyle, buttonStyle} from "@/components/settings/Controls";

export type Change = (changes: Record<string, string>) => void;

export function FilterRow({
    index,
    summary,
    settings,
    onChange,
    onRemove,
}: {
    index: number;
    summary: Summary;
    settings: Settings;
    onChange: Change;
    onRemove?: () => void;
}) {
    const prefix = `filter${index}_`;
    // one line per filter, as the web2py page laid it out: the parameter menu, the two limits (150 pixels each),
    // inverse, and after it a way to clear the row
    return (
        <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] sm:grid-cols-[auto_150px_150px_auto] gap-x-1 gap-y-2 items-center mb-2 sm:mb-[5px]">
            {/* on a small screen (two lines): the parameter and inverse, then the range beneath */}
            <div className="col-span-2 sm:col-span-1 min-w-0 order-1">
                <ParameterPicker
                    summary={summary}
                    name={prefix + "1"}
                    value={settings[prefix + "1"]}
                    denominator={settings[prefix + "2"]}
                    allowNone
                    compact
                    label={`Filter ${index} parameter`}
                    onChange={(value, denominator) =>
                        onChange({[prefix + "1"]: value, ...(denominator ? {[prefix + "2"]: denominator} : {})})
                    }
                />
            </div>
            <TextField
                name={prefix + "3"}
                value={settings[prefix + "3"]}
                placeholder="minimum"
                className="w-full order-3 sm:order-2"
                ariaLabel={`Filter ${index} minimum`}
                onCommit={(value) => onChange({[prefix + "3"]: value})}
            />
            <TextField
                name={prefix + "4"}
                value={settings[prefix + "4"]}
                placeholder="maximum"
                className="w-full order-4 sm:order-3"
                ariaLabel={`Filter ${index} maximum`}
                onCommit={(value) => onChange({[prefix + "4"]: value})}
            />
            <div className="order-2 sm:order-4 sm:ml-1.5 flex items-center gap-1.5">
                <Toggle
                    name={prefix + "inv"}
                    label="inverse"
                    checked={isOn(settings, prefix + "inv")}
                    onChange={(on) => onChange({[prefix + "inv"]: String(on)})}
                />
                {onRemove && (
                    <button
                        type="button"
                        onClick={onRemove}
                        title="Remove this filter"
                        aria-label={`Remove filter ${index}`}
                        className="text-[#999] hover:text-[#333] text-lg leading-none"
                    >
                        ×
                    </button>
                )}
            </div>
        </div>
    );
}

// the filters: those in use, each with a remove button, then one empty row until the API's limit
export function FilterRows({
    schema,
    summary,
    settings,
    onChange,
}: {
    schema: SettingsSchema;
    summary: Summary;
    settings: Settings;
    onChange: Change;
}) {
    const max = maxFilters(schema);
    const active = activeFilters(settings, max);
    // the rows shown: the three the web2py page always had, and past them one empty row until the API's limit
    const shown = Math.min(max, Math.max(3, active.length + 1));
    const rows = Array.from({length: shown}, (_, i) => i + 1);
    return (
        <div className="mb-5">
            <Label>Filter:</Label>
            {rows.map((index) => (
                <FilterRow
                    key={index}
                    index={index}
                    summary={summary}
                    settings={settings}
                    onChange={onChange}
                    onRemove={active.includes(index) ? () => onChange({[`filter${index}_1`]: "none"}) : undefined}
                />
            ))}
        </div>
    );
}

export function AxisRow({
    axis,
    label,
    summary,
    settings,
    onChange,
    allowLog = true,
    allowNone = false,
}: {
    axis: "x" | "y" | "z";
    label: string;
    summary: Summary;
    settings: Settings;
    onChange: Change;
    allowLog?: boolean;
    allowNone?: boolean;
}) {
    const name = `${axis}axis`;
    return (
        <div className="mb-5">
            <Label>{label}</Label>
            <div className="flex flex-wrap items-center gap-x-2.5">
                <ParameterPicker
                    summary={summary}
                    name={name + "1"}
                    value={settings[name + "1"]}
                    denominator={settings[name + "2"]}
                    allowNone={allowNone}
                    planetHandles={summary.axis_planet_param_types}
                    label={`${label.replace(/:$/, "")} parameter`}
                    onChange={(value, denominator) =>
                        onChange({[name + "1"]: value, ...(denominator ? {[name + "2"]: denominator} : {})})
                    }
                />
                {allowLog && (
                    <Toggle
                        name={name + "log"}
                        label="log"
                        checked={isOn(settings, name + "log")}
                        onChange={(on) => onChange({[name + "log"]: String(on)})}
                    />
                )}
                <Toggle
                    name={name + "inv"}
                    label="inverse"
                    checked={isOn(settings, name + "inv")}
                    onChange={(on) => onChange({[name + "inv"]: String(on)})}
                />
            </div>
        </div>
    );
}

export function SolarNormRow({summary, settings, onChange}: {summary: Summary; settings: Settings; onChange: Change}) {
    return (
        <div className="mb-5">
            <Label htmlFor="solarnorm">Solar normalization:</Label>
            <Select
                name="solarnorm"
                value={settings.solarnorm}
                onChange={(value) => onChange({solarnorm: value})}
                className="w-full"
            >
                {summary.solarnorms.map((norm) => (
                    <option key={norm.id} value={norm.id}>
                        {norm.author}
                        {norm.year ? ` (${norm.year})` : ""}
                    </option>
                ))}
            </Select>
        </div>
    );
}

export function StatisticRow({settings, onChange}: {settings: Settings; onChange: Change}) {
    return (
        <div className="mb-5">
            <Label htmlFor="statistic">If element ratio is in multiple catalogs:</Label>
            <Select
                name="statistic"
                value={settings.statistic}
                onChange={(value) => onChange({statistic: value})}
                className="w-full"
            >
                <option value="median">Use the median</option>
                <option value="mean">Use the mean</option>
            </Select>
        </div>
    );
}

// the catalogs to exclude or allow: a box like the old select2 control, the chosen catalogs as tags in it and a
// search field; the list of catalogs opens under it while the field has the focus, a click on a catalog adds it
export function CatalogsRow({summary, settings, onChange}: {summary: Summary; settings: Settings; onChange: Change}) {
    const [search, setSearch] = useState("");
    const [open, setOpen] = useState(false);
    const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    const chosen = useMemo(() => new Set(listOf(settings, "catalogs")), [settings]);
    const byId = useMemo(() => new Map(summary.catalogs.map((catalog) => [catalog.id, catalog])), [summary]);
    const shown = useMemo(() => {
        const needle = search.trim().toLowerCase();
        return summary.catalogs.filter(
            (catalog) => !chosen.has(catalog.id) && (!needle || catalog.author.toLowerCase().includes(needle)),
        );
    }, [summary, search, chosen]);
    const toggle = (id: string) => {
        const next = new Set(chosen);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        onChange({catalogs: [...next].join(";")});
    };
    // the list closes a moment after the field loses the focus, so a click on a catalog lands first
    const closeSoon = () => {
        closeTimer.current = setTimeout(() => setOpen(false), 150);
    };
    const stayOpen = () => {
        if (closeTimer.current) clearTimeout(closeTimer.current);
        setOpen(true);
    };
    return (
        <div className="mb-5">
            <div className={labelStyle + " flex items-center gap-1"}>
                <Select
                    name="cat_action"
                    value={settings.cat_action}
                    onChange={(value) => onChange({cat_action: value})}
                    ariaLabel="What the catalog list does"
                    className="form-control-inline !h-auto !py-0 !px-1 !shadow-none !border-[#767676] !rounded-sm !text-[#333]"
                >
                    <option value="exclude">Exclude</option>
                    <option value="only">Allow only</option>
                </Select>
                <span>catalogs:</span>
            </div>
            <div className="relative">
                <div
                    className="flex flex-wrap items-center gap-1 min-h-[32px] w-full bg-white border border-[#aaa] rounded px-1 py-0.5 cursor-text"
                    onClick={(event) =>
                        (event.currentTarget.querySelector("input") as HTMLInputElement | null)?.focus()
                    }
                >
                    {[...chosen].map((id) => (
                        <span
                            key={id}
                            className="inline-flex items-center gap-1 bg-[#e4e4e4] border border-[#aaa] rounded-sm px-1 text-[#333] leading-5"
                        >
                            <button
                                type="button"
                                onClick={() => toggle(id)}
                                aria-label={`Remove ${byId.get(id)?.author ?? id}`}
                                className="text-[#999] hover:text-[#333] font-bold leading-none"
                            >
                                ×
                            </button>
                            {byId.get(id)?.author ?? id}
                        </span>
                    ))}
                    <input
                        type="search"
                        value={search}
                        onChange={(event) => setSearch(event.target.value)}
                        onFocus={stayOpen}
                        onBlur={closeSoon}
                        onKeyDown={(event) => {
                            if (event.key === "Escape") setOpen(false);
                        }}
                        className="flex-1 min-w-[8rem] outline-none bg-transparent text-[#333] leading-5 px-1"
                        aria-label="search the catalogs"
                    />
                </div>
                {open && (
                    <ul
                        className="dropdown-panel absolute z-30 left-0 right-0 mt-0.5 max-h-48 overflow-y-auto !px-0 list-none"
                        role="listbox"
                        onMouseDown={(event) => event.preventDefault()}
                    >
                        {shown.map((catalog) => (
                            <li
                                key={catalog.id}
                                role="option"
                                aria-selected={false}
                                onClick={() => toggle(catalog.id)}
                                className="px-2 py-0.5 cursor-pointer whitespace-nowrap text-[#333] hover:bg-[#5897fb] hover:text-white"
                            >
                                {catalog.author}
                            </li>
                        ))}
                        {!shown.length && <li className="px-2 py-0.5 text-[#999]">No results found</li>}
                    </ul>
                )}
            </div>
        </div>
    );
}

export function StarsRow({settings, onChange}: {settings: Settings; onChange: Change}) {
    const count = listOf(settings, "star_list").length;
    return (
        <div className="mb-5">
            <div className={labelStyle + " flex items-center gap-1"}>
                <Select
                    name="star_action"
                    value={settings.star_action}
                    onChange={(value) => onChange({star_action: value})}
                    ariaLabel="What the star list does"
                    className="form-control-inline !h-auto !py-0 !px-1 !shadow-none !border-[#767676] !rounded-sm !text-[#333]"
                >
                    <option value="exclude">Exclude</option>
                    <option value="only">Allow only</option>
                </Select>
                <span>
                    stars by <em>any</em> <Ext href="https://simbad.u-strasbg.fr/simbad/">SIMBAD</Ext> name.
                </span>
            </div>
            {count > 1 && (
                <div className="alert-info !py-[7px] !px-2 !mb-1 h-[34px]">
                    Selected {count} stars.{" "}
                    <button type="button" className="font-bold bs-link" onClick={() => onChange({star_list: ""})}>
                        Clear selection
                    </button>
                </div>
            )}
            <TextField
                name="star_list"
                value={settings.star_list}
                className="w-full"
                ariaLabel="Star list, names separated by semicolons"
                placeholder="e.g. HD 122196; * 8 Lyn; HIP 114699; 2MASS J00403279-2348172"
                onCommit={(value) => onChange({star_list: value})}
            />
        </div>
    );
}

const TARGET_ORDER = ["hwo_tier1", "hwo_tier2", "thin_disk", "thick_disk", "has_exo"];

export function TargetSetsRow({summary, settings, onChange}: {summary: Summary; settings: Settings; onChange: Change}) {
    return (
        <div className="mb-5">
            <Label>Select Target Sets:</Label>
            <div>
                <Toggle
                    name="show_all"
                    label="All Hypatia Catalog"
                    checked={isOn(settings, "show_all")}
                    onChange={(on) => onChange({show_all: String(on)})}
                    plain
                />
            </div>
            <div>
                <Toggle
                    name="or_logic"
                    label='Use "Union" Logic for Multiple Target Sets'
                    checked={isOn(settings, "or_logic")}
                    onChange={(on) => onChange({or_logic: String(on)})}
                    plain
                />
            </div>
            <div className="mt-5 text-[#333]">Available Target Sets:</div>
            {TARGET_ORDER.filter((handle) => summary.targets[handle]).map((handle) => {
                const target = summary.targets[handle];
                return (
                    <div key={handle} title={target.ref}>
                        <Toggle
                            name={"show_" + handle}
                            label={target.title}
                            title={target.description}
                            checked={isOn(settings, "show_" + handle)}
                            onChange={(on) => onChange({["show_" + handle]: String(on)})}
                            plain
                        />
                    </div>
                );
            })}
        </div>
    );
}

export function SubmitRow({onSubmit}: {onSubmit: () => void}) {
    return (
        <button type="button" onClick={onSubmit} className={buttonStyle}>
            Submit
        </button>
    );
}
