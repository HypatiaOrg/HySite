"use client";
// The data table under the plots: the API builds it (columns, display strings, hover text); this shows it,
// sorts by a click on a header, loads every row on request, and downloads it.
import React, {useMemo, useState} from "react";
import type {Summary} from "@/lib/summary";
import type {Settings} from "@/lib/settings";
import {listOf} from "@/lib/settings";
import type {TableData} from "@/lib/plotTypes";
import {useFetchedData} from "@/components/plot/useFetchedData";
import PeriodicTable from "@/components/settings/PeriodicTable";
import {buttonStyle, buttonClass} from "@/components/settings/Controls";
import CellValues from "@/components/table/CellValues";

// the column options beyond the elements, as the API's table tokens
const OPTIONS: Array<[string, string]> = [
    ["stellar", "Stellar Properties"],
    ["planet", "Planet Properties Mode"],
    ["names", "More Names"],
    ["names_all", "All Names"],
    ["spread", "Error"],
    ["ref", "Reference"],
];
const NAME_LABELS: Record<string, string> = {
    star_id: "Name",
    hd: "HD",
    "2mass": "2MASS",
    wds: "WDS",
    aliases: "All Names",
    nea_name: "NEA Name",
    planet_letter: "Planet Letter",
};
const SMALL_COLUMNS = /(_err|_ref)$|^aliases$/;

function columnLabel(summary: Summary, column: string): {text: string; hover: string; units: string} {
    const info = summary.units_and_fields[column];
    if (info) return {text: info.label, hover: info.hover, units: info.units ?? ""};
    if (NAME_LABELS[column]) return {text: NAME_LABELS[column], hover: NAME_LABELS[column], units: ""};
    const element = summary.element_data.find((item) => item.element_id === column);
    if (element) return {text: element.abbreviation, hover: element.element_name, units: ""};
    return {text: column, hover: column, units: ""};
}

// the chevron the web2py page's bands show before "Data Table" and "Download this table" (a glyphicon there)
function Chevron() {
    return (
        <span aria-hidden="true" className="inline-block w-3 mr-1 align-middle">
            <svg viewBox="0 0 12 8" width="12" height="8">
                <path d="M1 1l5 5 5-5" fill="none" stroke="#333" strokeWidth="2.4" />
            </svg>
        </span>
    );
}

// the "new window" glyph the web2py page shows after a star's name, for its SIMBAD page
function NewWindowIcon() {
    return (
        <svg viewBox="0 0 12 12" width="11" height="11" aria-hidden="true" className="inline-block">
            <path d="M2 1h4v1.5H3.5v6h6V6H11v4H2z" fill="#4e11b7" />
            <path d="M7 1h4v4l-1.4-1.4L6 7.2 4.8 6l3.6-3.6z" fill="#4e11b7" />
        </svg>
    );
}

function simbadLink(name: string) {
    return (
        "http://simbad.u-strasbg.fr/simbad/sim-basic?Ident=" +
        name.replace(/\+/g, "%2B").replace("2MASS ", "2MASS J") +
        "&submit=SIMBAD+search"
    );
}

type Props = {
    summary: Summary;
    settings: Settings;
    onChange: (changes: Record<string, string>) => void;
    showTargets: boolean;
    // the columns a new visitor sees (the settings model's default), which Reset restores
    defaultColumns: string;
};

export default function DataTable({summary, settings, onChange, showTargets, defaultColumns}: Props) {
    const [sort, setSort] = useState<{column: string | null; reverse: boolean}>({column: null, reverse: false});
    const [showRows, setShowRows] = useState(false);
    const columns = useMemo(() => new Set(listOf(settings, "tablecols")), [settings]);

    // the settings the API's table endpoint takes: the plot's, plus the table's own
    const tableSettings = useMemo(
        () => ({
            ...settings,
            show_targets: String(showTargets),
            showrows: String(showRows),
            ...(sort.column ? {sort: sort.column, reverse: String(sort.reverse)} : {}),
        }),
        [settings, showTargets, showRows, sort],
    );

    const {data: table, error, loading} = useFetchedData<TableData>("table", tableSettings);

    const toggleColumn = (id: string) => {
        const next = new Set(columns);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        onChange({tablecols: [...next].join(",")});
    };
    const sortBy = (column: string) => {
        setShowRows(false);
        setSort((current) => ({column, reverse: current.column === column ? !current.reverse : false}));
    };
    const download = async (format: "csv" | "tsv" | "psv") => {
        const response = await fetch("/data/table", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({...tableSettings, format, download: "true"}),
        });
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        const date = new Date();
        anchor.href = url;
        anchor.download = `hypatia-${String(date.getDate()).padStart(2, "0")}${String(date.getMonth() + 1).padStart(2, "0")}${date.getFullYear()}.${format}`;
        anchor.click();
        URL.revokeObjectURL(url);
    };

    return (
        <section className="mt-6 -mx-[30px]">
            {/* the bands of the web2py page: the heading with its chevron, then the controls on light grey */}
            <div className="bg-[#f8f8f8] border-t-2 border-hypurple text-center p-2 text-[16.8px] leading-6">
                <b>
                    <Chevron />
                    Data Table
                </b>{" "}
                <span>{table?.status ?? ""}</span>
            </div>
            <div className="bg-[#f8f8f8] border-b-2 border-hypurple pb-5">
                <div className="mx-auto w-[880px] max-w-full overflow-x-auto">
                    <PeriodicTable summary={summary} selected={columns} onPick={toggleColumn} onColor="on" />
                    <br />
                    <div>
                        {OPTIONS.map(([token, label]) => (
                            <button
                                type="button"
                                key={token}
                                onClick={() => toggleColumn(token)}
                                className={buttonClass(columns.has(token) ? "on" : "plain", "mr-1")}
                            >
                                {label}
                            </button>
                        ))}
                        <br />
                        <br />
                        <button
                            type="button"
                            className={buttonStyle}
                            onClick={() => onChange({tablecols: defaultColumns})}
                        >
                            Reset
                        </button>
                    </div>
                </div>
            </div>
            <div className="bg-white text-[#333] p-2 mb-2">
                <Chevron />
                Download this table:
                {(["csv", "tsv", "psv"] as const).map((format) => (
                    <button
                        type="button"
                        key={format}
                        className="btn btn-link uppercase"
                        onClick={() => download(format)}
                    >
                        {format}
                    </button>
                ))}
            </div>
            {error && <div className="text-[#a94442] p-4">The table could not be loaded: {error}</div>}
            {/* the table in its box: a little room between the window edges and the first and last columns, more on
                the right, clear of the scroll bar; a table wider than the page scrolls sideways inside the box */}
            <div className={"overflow-x-auto pl-2.5 pr-5 transition-opacity " + (loading ? "opacity-50" : "")}>
                {table && (
                    <table className="w-full border-collapse bg-white text-sm leading-5 text-[#333]">
                        <thead className="sticky top-0 bg-white z-10">
                            <tr>
                                {table.columns.map((column) => {
                                    const sub = column.endsWith("_min_err")
                                        ? "-err"
                                        : column.endsWith("_max_err")
                                          ? "+err"
                                          : column.endsWith("_err")
                                            ? "err"
                                            : column.endsWith("_ref")
                                              ? "reference"
                                              : null;
                                    const label = columnLabel(summary, column);
                                    return (
                                        <th
                                            key={column}
                                            scope="col"
                                            className={
                                                "text-center border-b-2 border-hypurple p-[5px] align-bottom font-bold" +
                                                // the first column (the star's name) is only as wide as its names
                                                (column === "star_id" ? " w-[1%] whitespace-nowrap" : "")
                                            }
                                            aria-sort={
                                                sort.column === column
                                                    ? sort.reverse
                                                        ? "descending"
                                                        : "ascending"
                                                    : undefined
                                            }
                                        >
                                            {sub ? (
                                                <small className="text-[#555]">{sub}</small>
                                            ) : (
                                                <>
                                                    <button
                                                        type="button"
                                                        title={label.hover}
                                                        onClick={() => sortBy(column)}
                                                        aria-label={`Sort by ${label.text}`}
                                                        className="font-bold text-hypurple hover:underline whitespace-nowrap"
                                                    >
                                                        {label.text}
                                                        {sort.column === column ? (sort.reverse ? " ▾" : " ▴") : ""}
                                                    </button>
                                                    {label.units && (
                                                        <>
                                                            <br />
                                                            <small className="text-[#555]">{label.units}</small>
                                                        </>
                                                    )}
                                                </>
                                            )}
                                        </th>
                                    );
                                })}
                            </tr>
                        </thead>
                        <tbody>
                            {table.rows.map((row, r) => (
                                <tr key={r} className="odd:bg-[#f9f9f9]">
                                    {row.map((cell, c) => {
                                        const column = table.columns[c];
                                        const lines = Array.isArray(cell) ? cell : [cell];
                                        const hover = table.hover[r]?.[c] ?? undefined;
                                        return (
                                            <td key={c} className="p-[5px] text-center whitespace-nowrap">
                                                {lines.map((line, i) => (
                                                    <span
                                                        key={i}
                                                        className={
                                                            "block " +
                                                            (SMALL_COLUMNS.test(column) ? "text-xs text-[#555]" : "")
                                                        }
                                                    >
                                                        {hover ? <CellValues value={line} values={hover} /> : line}
                                                        {column === "star_id" && i === 0 && line && (
                                                            <a
                                                                href={simbadLink(line)}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="bs-link ml-1 inline-block align-middle"
                                                                aria-label={`${line} on SIMBAD`}
                                                                title="SIMBAD"
                                                            >
                                                                <NewWindowIcon />
                                                            </a>
                                                        )}
                                                    </span>
                                                ))}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
            {table?.moreRows && (
                <div className="px-2.5 py-3 text-[#333]">
                    Showing the first {table.rows.length} of {table.totalRows} rows.{" "}
                    {table.canLoadAll ? (
                        <button type="button" className="bs-link" onClick={() => setShowRows(true)}>
                            Load All
                        </button>
                    ) : (
                        <>
                            This table is too large to show on the page;{" "}
                            <button type="button" className="bs-link" onClick={() => download("csv")}>
                                download it as CSV
                            </button>{" "}
                            to get all {table.totalRows} rows.
                        </>
                    )}
                </div>
            )}
        </section>
    );
}
