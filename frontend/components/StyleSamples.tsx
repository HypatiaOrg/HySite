"use client";
// The plot pages' controls on the style page, with sample data in place of the catalog summary
import React, {useState} from "react";
import type {Summary} from "@/lib/summary";
import {Toggle, Select, TextField, Label, Notice, buttonStyle, buttonClass} from "@/components/settings/Controls";
import ParameterPicker from "@/components/settings/ParameterPicker";

const sampleSummary: Summary = {
    units_and_fields: {
        teff: {label: "Effective Temperature", hover: "Effective Temperature", units: "K", decimals: 0},
        dist: {label: "Distance", hover: "Distance", units: "pc", decimals: 2},
    },
    stellar_param_types: ["teff", "dist"],
    planet_param_types: [],
    ranked_string_params: {},
    catalogs: [],
    solarnorms: [],
    element_data: ["Li", "C", "O", "Mg", "Si", "Ca", "Ti", "Fe", "Fe_II", "Ni", "Ba_II", "Eu"].map((id) => ({
        element_id: id,
        element_name: id,
        abbreviation: id,
    })),
    representative_error: {},
    targets: {},
};

export default function StyleSamples() {
    const [axis, setAxis] = useState({value: "Fe", denominator: "H"});
    const [on, setOn] = useState(true);
    return (
        <div className="mb-8 text-black">
            <div className="flex flex-wrap items-end gap-6 mb-4">
                <div>
                    <Label>X-axis:</Label>
                    <ParameterPicker
                        summary={sampleSummary}
                        name="sample"
                        value={axis.value}
                        denominator={axis.denominator}
                        label="X-axis parameter"
                        onChange={(value, denominator) =>
                            setAxis({value, denominator: denominator ?? axis.denominator})
                        }
                    />
                </div>
                <div>
                    <Label htmlFor="sample-select">A choice:</Label>
                    <Select name="sample-select" value="median" onChange={() => {}}>
                        <option value="median">Use the median</option>
                    </Select>
                </div>
                <div>
                    <Label htmlFor="sample-text">A text field:</Label>
                    <TextField
                        name="sample-text"
                        value=""
                        placeholder="e.g. HD 122196; * 8 Lyn"
                        onCommit={() => {}}
                        className="w-56"
                    />
                </div>
                <Toggle name="sample-toggle" label="Show gridlines" checked={on} onChange={setOn} />
            </div>
            <div className="flex flex-wrap items-center gap-3 mb-4">
                <button type="button" className={buttonStyle}>
                    A button
                </button>
                <button type="button" className={buttonClass("picked")}>
                    Picked for an axis
                </button>
                <button type="button" className={buttonClass("on")}>
                    A column in the table
                </button>
            </div>
            <Notice>A notice beside the form, such as the one about the mean being calculated in linear space.</Notice>
            <div className="inline-block bg-white/95 border border-hygrey rounded px-1.5 py-0.5 text-xs leading-tight text-[#222]">
                <div className="py-0.5 border-t border-[#ddd]">
                    <b>HD 216435</b>
                    <br />
                    [Fe/H] = 0.25, [Si/H] = 0.27
                </div>
                <div className="py-0.5 border-t border-[#ddd]">
                    <b>HD 224789</b>
                    <br />
                    [Fe/H] = 0.00, [Si/H] = 0.04
                </div>
            </div>
            <span className="text-hygrey text-sm ml-3">the hover labels on a points plot</span>
        </div>
    );
}
