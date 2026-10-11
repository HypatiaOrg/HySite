'use client';
// An axis or filter parameter: an element ratio (with its denominator), a stellar property or a planet
// property, picked from a panel like the old dropdown
import React from "react";
import type {Summary} from "@/lib/summary";
import {labelOf, hoverOf} from "@/lib/summary";
import {isElement} from "@/lib/settings";
import PeriodicTable from "@/components/settings/PeriodicTable";
import {Popover, buttonClass} from "@/components/settings/Controls";

type Props = {
    summary: Summary,
    name: string,          // the setting's name: xaxis1, filter2_1 ...
    value: string,
    denominator: string,   // the ratio's denominator (xaxis2 ...), shown only for an element
    onChange: (value: string, denominator?: string) => void,
    allowNone?: boolean,
    // in a filter row: the name shortened to fit rather than wrapping the row
    compact?: boolean,
    // what the picker is for, for a screen reader: "X-axis parameter", "filter 2 parameter"
    label: string,
};

function PropertyButtons({summary, handles, value, onPick}: {summary: Summary, handles: Array<string>, value: string, onPick: (id: string) => void}) {
    return (
        <div className="flex flex-wrap gap-1 mb-2">
            {handles.map((handle) => (
                <button type="button" key={handle} data-picks="1" title={hoverOf(summary, handle)} onClick={() => onPick(handle)}
                        className={buttonClass(value === handle ? "picked" : "plain", "px-1.5 py-0 text-xs leading-5")}>
                    {labelOf(summary, handle)}
                </button>
            ))}
        </div>
    );
}

export default function ParameterPicker({summary, name, value, denominator, onChange, allowNone = false, compact = false, label}: Props) {
    return (
        <span className={"inline-flex items-center gap-1" + (compact ? " min-w-0" : "")}>
            <Popover button={<span>{labelOf(summary, value)}</span>} title={hoverOf(summary, value)} compact={compact}
                     ariaLabel={`${label}: ${labelOf(summary, value)}`}>
                <div className="w-[68rem]">
                    {allowNone && (
                        <button type="button" data-picks="1" onClick={() => onChange("none")}
                                className={buttonClass(value === "none" ? "picked" : "plain", "px-1.5 py-0 text-xs leading-5 mb-2")}>none</button>
                    )}
                    <div className="font-semibold text-hypurple">Element ratio:</div>
                    <PeriodicTable summary={summary} selected={new Set([value])} onPick={(id) => onChange(id)}/>
                    <div className="font-semibold text-hypurple mt-2">Stellar property:</div>
                    <PropertyButtons summary={summary} handles={summary.stellar_param_types} value={value} onPick={(id) => onChange(id)}/>
                    <div className="font-semibold text-hypurple">Planet property:</div>
                    <PropertyButtons summary={summary} handles={summary.planet_param_types} value={value} onPick={(id) => onChange(id)}/>
                </div>
            </Popover>
            {isElement(value) && (
                <Popover button={<span>{labelOf(summary, denominator)}</span>} title="the denominator of the ratio"
                         ariaLabel={`${label}, denominator of the ratio: ${labelOf(summary, denominator)}`}>
                    <div className="w-[68rem]">
                        <div className="font-semibold text-hypurple">Denominator:</div>
                        <PeriodicTable summary={summary} selected={new Set([denominator])} allowH onPick={(id) => onChange(value, id)}/>
                    </div>
                </Popover>
            )}
            <input type="hidden" name={name} value={value}/>
        </span>
    );
}
