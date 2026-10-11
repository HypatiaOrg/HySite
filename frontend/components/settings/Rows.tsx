'use client';
// The rows of the plot settings form: a filter, an axis, the catalogs, the stars, the target sets
import React, {useMemo, useState} from "react";
import type {Summary} from "@/lib/summary";
import type {Settings, SettingsSchema} from "@/lib/settings";
import {isOn, listOf, activeFilters, maxFilters} from "@/lib/settings";
import ParameterPicker from "@/components/settings/ParameterPicker";
import {Toggle, Select, TextField, Label, labelStyle, inputStyle, buttonStyle} from "@/components/settings/Controls";

export type Change = (changes: Record<string, string>) => void;

export function FilterRow({index, summary, settings, onChange, onRemove}:
                          {index: number, summary: Summary, settings: Settings, onChange: Change, onRemove?: () => void}) {
    const prefix = `filter${index}_`;
    // one line per filter: the parameter (its name shortened rather than wrapping), the range, inverse, remove
    return (
        <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto_1rem] sm:grid-cols-[minmax(0,1fr)_5.5rem_5.5rem_auto_1rem] gap-2 items-center mb-2 sm:mb-1">
            {/* on a small screen (two lines): the parameter, inverse and remove, then the range beneath */}
            <div className="col-span-2 sm:col-span-1 min-w-0 order-1">
                <ParameterPicker summary={summary} name={prefix + "1"} value={settings[prefix + "1"]} denominator={settings[prefix + "2"]} allowNone compact
                                 label={`Filter ${index} parameter`}
                                 onChange={(value, denominator) => onChange({[prefix + "1"]: value, ...(denominator ? {[prefix + "2"]: denominator} : {})})}/>
            </div>
            <TextField name={prefix + "3"} value={settings[prefix + "3"]} placeholder="minimum" className="w-full order-4 sm:order-2"
                       ariaLabel={`Filter ${index} minimum`} onCommit={(value) => onChange({[prefix + "3"]: value})}/>
            <TextField name={prefix + "4"} value={settings[prefix + "4"]} placeholder="maximum" className="w-full order-5 sm:order-3"
                       ariaLabel={`Filter ${index} maximum`} onCommit={(value) => onChange({[prefix + "4"]: value})}/>
            <div className="order-2 sm:order-4">
                <Toggle name={prefix + "inv"} label="inverse" checked={isOn(settings, prefix + "inv")}
                        onChange={(on) => onChange({[prefix + "inv"]: String(on)})}/>
            </div>
            <div className="order-3 sm:order-5">
                {onRemove && (
                    <button type="button" onClick={onRemove} title="Remove this filter" aria-label={`Remove filter ${index}`}
                            className="text-hygrey hover:text-hyred text-lg leading-none">×</button>
                )}
            </div>
        </div>
    );
}

// the filters: those in use, each with a remove button, then one empty row until the API's limit
export function FilterRows({schema, summary, settings, onChange}:
                           {schema: SettingsSchema, summary: Summary, settings: Settings, onChange: Change}) {
    const max = maxFilters(schema);
    const active = activeFilters(settings, max);
    const next = active.length < max ? active.length + 1 : null;
    return (
        <div className="mb-3">
            <Label>{active.length ? `Filters (${active.length} of ${max}):` : "Filter:"}</Label>
            {active.map((index) => (
                <FilterRow key={index} index={index} summary={summary} settings={settings} onChange={onChange}
                           onRemove={() => onChange({[`filter${index}_1`]: "none"})}/>
            ))}
            {next && <FilterRow key={`new-${next}`} index={next} summary={summary} settings={settings} onChange={onChange}/>}
        </div>
    );
}

export function AxisRow({axis, label, summary, settings, onChange, allowLog = true, allowNone = false}:
                        {axis: "x" | "y" | "z", label: string, summary: Summary, settings: Settings, onChange: Change, allowLog?: boolean, allowNone?: boolean}) {
    const name = `${axis}axis`;
    return (
        <div className="mb-3">
            <Label>{label}</Label>
            <div className="flex flex-wrap items-center gap-3">
                <ParameterPicker summary={summary} name={name + "1"} value={settings[name + "1"]} denominator={settings[name + "2"]} allowNone={allowNone}
                                 label={`${label.replace(/:$/, "")} parameter`}
                                 onChange={(value, denominator) => onChange({[name + "1"]: value, ...(denominator ? {[name + "2"]: denominator} : {})})}/>
                {allowLog && (
                    <Toggle name={name + "log"} label="log" checked={isOn(settings, name + "log")} onChange={(on) => onChange({[name + "log"]: String(on)})}/>
                )}
                <Toggle name={name + "inv"} label="inverse" checked={isOn(settings, name + "inv")} onChange={(on) => onChange({[name + "inv"]: String(on)})}/>
            </div>
        </div>
    );
}

export function SolarNormRow({summary, settings, onChange}: {summary: Summary, settings: Settings, onChange: Change}) {
    return (
        <div className="mb-3">
            <Label htmlFor="solarnorm">Solar normalization:</Label>
            <Select name="solarnorm" value={settings.solarnorm} onChange={(value) => onChange({solarnorm: value})} className="w-full">
                {summary.solarnorms.map((norm) => (
                    <option key={norm.id} value={norm.id}>{norm.author}{norm.year ? ` (${norm.year})` : ""}</option>
                ))}
            </Select>
        </div>
    );
}

export function StatisticRow({settings, onChange}: {settings: Settings, onChange: Change}) {
    return (
        <div className="mb-3">
            <Label htmlFor="statistic">If element ratio is in multiple catalogs:</Label>
            <Select name="statistic" value={settings.statistic} onChange={(value) => onChange({statistic: value})} className="w-full">
                <option value="median">Use the median</option>
                <option value="mean">Use the mean</option>
            </Select>
        </div>
    );
}

// the catalogs to exclude or allow: a list with a search box, as the old select2 control
export function CatalogsRow({summary, settings, onChange}: {summary: Summary, settings: Settings, onChange: Change}) {
    const [search, setSearch] = useState("");
    const chosen = useMemo(() => new Set(listOf(settings, "catalogs")), [settings]);
    const shown = useMemo(() => {
        const needle = search.trim().toLowerCase();
        return needle ? summary.catalogs.filter((catalog) => catalog.author.toLowerCase().includes(needle)) : summary.catalogs;
    }, [summary, search]);
    const toggle = (id: string) => {
        const next = new Set(chosen);
        if (next.has(id)) next.delete(id); else next.add(id);
        onChange({catalogs: [...next].join(";")});
    };
    return (
        <div className="mb-3">
            <div className={labelStyle + " mb-1 flex items-center gap-2"}>
                <Select name="cat_action" value={settings.cat_action} onChange={(value) => onChange({cat_action: value})} ariaLabel="What the catalog list does">
                    <option value="exclude">Exclude</option>
                    <option value="only">Allow only</option>
                </Select>
                <span>catalogs:</span>
                {chosen.size > 0 && (
                    <span className="font-normal text-hygrey">{chosen.size} chosen,{' '}
                        <button type="button" className="text-hyred hover:underline" onClick={() => onChange({catalogs: ""})}>clear</button>
                    </span>
                )}
            </div>
            <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="search the catalogs"
                   className={inputStyle + " w-full mb-1"} aria-label="search the catalogs"/>
            <div className="h-40 overflow-y-auto border border-hygrey/50 rounded bg-white px-2 py-1">
                {shown.map((catalog) => (
                    <label key={catalog.id} className="block cursor-pointer text-black whitespace-nowrap">
                        <input type="checkbox" checked={chosen.has(catalog.id)} onChange={() => toggle(catalog.id)} className="accent-hypurple mr-2"/>
                        {catalog.author}
                    </label>
                ))}
            </div>
        </div>
    );
}

export function StarsRow({settings, onChange}: {settings: Settings, onChange: Change}) {
    const count = listOf(settings, "star_list").length;
    return (
        <div className="mb-3">
            <div className={labelStyle + " mb-1 flex items-center gap-2"}>
                <Select name="star_action" value={settings.star_action} onChange={(value) => onChange({star_action: value})} ariaLabel="What the star list does">
                    <option value="exclude">Exclude</option>
                    <option value="only">Allow only</option>
                </Select>
                <span>stars by <em>any</em> <a className="text-hyred underline decoration-hyred/40 hover:text-hypurple" href="https://simbad.u-strasbg.fr/simbad/" target="_blank" rel="noopener noreferrer">SIMBAD</a> name.</span>
            </div>
            {count > 1 && (
                <div className="text-sm text-hygrey mb-1">
                    {count} stars listed.{' '}
                    <button type="button" className="text-hyred hover:underline" onClick={() => onChange({star_list: ""})}>Clear the list</button>
                </div>
            )}
            <TextField name="star_list" value={settings.star_list} className="w-full" ariaLabel="Star list, names separated by semicolons"
                       placeholder="e.g. HD 122196; * 8 Lyn; HIP 114699; 2MASS J00403279-2348172"
                       onCommit={(value) => onChange({star_list: value})}/>
        </div>
    );
}

const TARGET_ORDER = ["hwo_tier1", "hwo_tier2", "thin_disk", "thick_disk", "has_exo"];

export function TargetSetsRow({summary, settings, onChange}: {summary: Summary, settings: Settings, onChange: Change}) {
    return (
        <div className="mb-3">
            <Label>Select Target Sets:</Label>
            <div><Toggle name="show_all" label="All Hypatia Catalog" checked={isOn(settings, "show_all")} onChange={(on) => onChange({show_all: String(on)})}/></div>
            <div><Toggle name="or_logic" label='Use "Union" Logic for Multiple Target Sets' checked={isOn(settings, "or_logic")} onChange={(on) => onChange({or_logic: String(on)})}/></div>
            <div className="mt-2 text-black">Available Target Sets:</div>
            {TARGET_ORDER.filter((handle) => summary.targets[handle]).map((handle) => {
                const target = summary.targets[handle];
                return (
                    <div key={handle} title={target.ref}>
                        <Toggle name={"show_" + handle} label={target.title} title={target.description}
                                checked={isOn(settings, "show_" + handle)} onChange={(on) => onChange({["show_" + handle]: String(on)})}/>
                    </div>
                );
            })}
        </div>
    );
}

export function SubmitRow({onSubmit}: {onSubmit: () => void}) {
    return <button type="button" onClick={onSubmit} className={buttonStyle + " px-4"}>Submit</button>;
}

// the density page: the histograms along the axes, their bin sizes (a number, or a keyword) and the colour scale
export function DensityRows({schema, settings, onChange}: {schema: SettingsSchema, settings: Settings, onChange: Change}) {
    const keywords = schema.fields.xhist_bin_size?.keywords ?? [];
    const placeholder = `Float or keywords: (${keywords.join(", ")})`;
    return (
        <div className="mb-3">
            <div className="mb-2"><Toggle name="show_xyhist" label="Show X and Y histograms" checked={isOn(settings, "show_xyhist")} onChange={(on) => onChange({show_xyhist: String(on)})}/></div>
            <Label htmlFor="xhist_bin_size">X histograms bin size</Label>
            <TextField name="xhist_bin_size" value={settings.xhist_bin_size} placeholder={placeholder} className="w-full mb-2" onCommit={(value) => onChange({xhist_bin_size: value})}/>
            <Label htmlFor="yhist_bin_size">Y histograms bin size</Label>
            <TextField name="yhist_bin_size" value={settings.yhist_bin_size} placeholder={placeholder} className="w-full mb-2" onCommit={(value) => onChange({yhist_bin_size: value})}/>
            <Label htmlFor="color_pallet">Choose a Color Pallet</Label>
            <Select name="color_pallet" value={settings.color_pallet} onChange={(value) => onChange({color_pallet: value})} className="w-full">
                {(schema.fields.color_pallet?.choices ?? []).map((choice) => <option key={choice} value={choice}>{choice}</option>)}
            </Select>
        </div>
    );
}
