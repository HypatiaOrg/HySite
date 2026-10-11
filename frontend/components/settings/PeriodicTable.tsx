'use client';
// The periodic table as buttons: the elements the catalog has abundances for, with a second button for
// the singly ionized species where it is measured. Picks one element (an axis or filter) or toggles
// several (the table's columns).
import React from "react";
import type {Summary} from "@/data/summary";
import {buttonStyle, pickedStyle, onStyle} from "@/components/settings/controls";

const PERIODS: Array<Array<string | null>> = [
    ['H', null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, 'He'],
    ['Li', 'Be', null, null, null, null, null, null, null, null, null, null, 'B', 'C', 'N', 'O', 'F', 'Ne'],
    ['Na', 'Mg', null, null, null, null, null, null, null, null, null, null, 'Al', 'Si', 'P', 'S', 'Cl', 'Ar'],
    ['K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr'],
    ['Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe'],
    ['Cs', 'Ba', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn'],
    ['Fr', 'Ra', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds', 'Rg', 'Cn', 'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og'],
    [null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null, null],
    [null, null, 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', null, null],
    [null, null, 'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', null, null],
];

export type PeriodicTableProps = {
    summary: Summary,
    // the ids that are on (one for a picker, several for the table's columns)
    selected: Set<string>,
    onPick: (id: string) => void,
    allowH?: boolean,
    // the style of an element that is on: a pick (purple) or a column in the table (green)
    onColor?: "picked" | "on",
};

export default function PeriodicTable({summary, selected, onPick, allowH = false, onColor = "picked"}: PeriodicTableProps) {
    const available = new Set(summary.element_data.map((element) => element.element_id));
    if (allowH) available.add("H");
    const names = new Map(summary.element_data.map((element) => [element.element_id, element.element_name]));
    const highlight = onColor === "picked" ? pickedStyle : onStyle;
    const cell = (id: string, text: string, title: string) => (
        <button type="button" key={id} data-picks="1" title={title} onClick={() => onPick(id)}
                className={buttonStyle + " px-0.5 py-0 text-xs leading-5 " + (selected.has(id) ? highlight : "")}>
            {text}
        </button>
    );
    return (
        <table className="border-separate border-spacing-px">
            <tbody>
            {PERIODS.map((period, row) => (
                <tr key={row}>
                    {period.map((element, column) => {
                        if (!element) return <td key={column}/>;
                        const hasI = available.has(element), hasII = available.has(element + "_II");
                        return (
                            <td key={column} className="whitespace-nowrap text-center text-hygrey text-xs">
                                {hasI ? cell(element, element, names.get(element) ?? element) : element}
                                {hasII && cell(element + "_II", "II", (names.get(element) ?? element) + " (II)")}
                            </td>
                        );
                    })}
                </tr>
            ))}
            </tbody>
        </table>
    );
}
