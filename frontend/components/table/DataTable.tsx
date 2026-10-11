'use client';
// The data table under the plots: the API builds it (columns, display strings, hover text); this shows it,
// sorts by a click on a header, loads every row on request, and downloads it.
import React, {useEffect, useMemo, useRef, useState} from "react";
import type {Summary} from "@/lib/summary";
import type {Settings} from "@/lib/settings";
import {listOf} from "@/lib/settings";
import {fetchData} from "@/lib/api";
import {type TableData} from "@/lib/plotTypes";
import PeriodicTable from "@/components/settings/PeriodicTable";
import {buttonStyle, buttonClass} from "@/components/settings/Controls";
import CellValues from "@/components/table/CellValues";

const DEFAULT_COLUMNS = "Fe,C,O,Mg,Si,S,Ca,Ti";
// the column options beyond the elements, as the API's table tokens
const OPTIONS: Array<[string, string]> = [
    ["stellar", "Stellar Properties"], ["planet", "Planet Properties Mode"], ["names", "More Names"],
    ["names_all", "All Names"], ["spread", "Error"], ["ref", "Reference"],
];
const NAME_LABELS: Record<string, string> = {
    star_id: "Name", hd: "HD", "2mass": "2MASS", wds: "WDS", aliases: "All Names", nea_name: "NEA Name", planet_letter: "Planet Letter",
};
const SMALL_COLUMNS = /(_err|_ref)$|^aliases$/;

function columnLabel(summary: Summary, column: string): {text: string, hover: string, units: string} {
    const info = summary.units_and_fields[column];
    if (info) return {text: info.label, hover: info.hover, units: info.units ?? ""};
    if (NAME_LABELS[column]) return {text: NAME_LABELS[column], hover: NAME_LABELS[column], units: ""};
    const element = summary.element_data.find((item) => item.element_id === column);
    if (element) return {text: element.abbreviation, hover: element.element_name, units: ""};
    return {text: column, hover: column, units: ""};
}

function simbadLink(name: string) {
    return "http://simbad.u-strasbg.fr/simbad/sim-basic?Ident=" + name.replace(/\+/g, "%2B").replace("2MASS ", "2MASS J") + "&submit=SIMBAD+search";
}

type Props = {summary: Summary, settings: Settings, onChange: (changes: Record<string, string>) => void, showTargets: boolean};

export default function DataTable({summary, settings, onChange, showTargets}: Props) {
    const [sort, setSort] = useState<{column: string | null, reverse: boolean}>({column: null, reverse: false});
    const [showRows, setShowRows] = useState(false);
    // what the API answered, and for which settings: the table is loading while they are not the current ones
    const [answer, setAnswer] = useState<{settings: Record<string, string>, table: TableData | null, error: string | null} | null>(null);
    const request = useRef(0);
    const columns = useMemo(() => new Set(listOf(settings, "tablecols")), [settings]);

    // the settings the API's table endpoint takes: the plot's, plus the table's own
    const tableSettings = useMemo(() => ({
        ...settings, show_targets: String(showTargets), showrows: String(showRows),
        ...(sort.column ? {sort: sort.column, reverse: String(sort.reverse)} : {}),
    }), [settings, showTargets, showRows, sort]);

    useEffect(() => {
        const id = ++request.current;
        const timer = setTimeout(() => {
            fetchData<TableData>("table", tableSettings)
                .then((data) => { if (id === request.current) setAnswer({settings: tableSettings, table: data, error: null}); })
                .catch((problem: Error) => { if (id === request.current) setAnswer((current) => ({settings: tableSettings, table: current?.table ?? null, error: problem.message})); });
        }, 300);
        return () => clearTimeout(timer);
    }, [tableSettings]);
    const table = answer?.table ?? null, error = answer?.error ?? null;
    const loading = answer?.settings !== tableSettings;

    const toggleColumn = (id: string) => {
        const next = new Set(columns);
        if (next.has(id)) next.delete(id); else next.add(id);
        onChange({tablecols: [...next].join(",")});
    };
    const sortBy = (column: string) => {
        setShowRows(false);
        setSort((current) => ({column, reverse: current.column === column ? !current.reverse : false}));
    };
    const download = async (format: "csv" | "tsv" | "psv") => {
        const response = await fetch("/data/table", {
            method: "POST", headers: {"Content-Type": "application/json"},
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
        <section className="mt-6">
            <div className="bg-hygrey/10 border-t-2 border-hypurple text-center py-2 text-lg">
                <b className="text-hypurple">Data Table</b> <span className="text-hygrey">{table?.status ?? ""}</span>
            </div>
            <div className="bg-hygrey/10 border-b-2 border-hypurple pb-4">
                <div className="mx-auto w-fit max-w-full overflow-x-auto px-2">
                    <PeriodicTable summary={summary} selected={columns} onPick={toggleColumn} onColor="on"/>
                    <div className="flex flex-wrap gap-1 mt-2">
                        {OPTIONS.map(([token, label]) => (
                            <button type="button" key={token} onClick={() => toggleColumn(token)}
                                    className={buttonClass(columns.has(token) ? "on" : "plain")}>{label}</button>
                        ))}
                    </div>
                    <div className="flex flex-wrap items-center gap-3 mt-3">
                        <button type="button" className={buttonStyle} onClick={() => onChange({tablecols: DEFAULT_COLUMNS})}>Reset</button>
                        <span className="text-hygrey">Download this table:</span>
                        {(["csv", "tsv", "psv"] as const).map((format) => (
                            <button type="button" key={format} className="text-hyred hover:text-hypurple hover:underline uppercase" onClick={() => download(format)}>{format}</button>
                        ))}
                    </div>
                </div>
            </div>

            {error && <div className="text-hyred p-4">The table could not be loaded: {error}</div>}
            <div className={"overflow-x-auto transition-opacity " + (loading ? "opacity-50" : "")}>
                {table && (
                    <table className="w-full border-collapse bg-white text-sm">
                        <thead className="sticky top-0 bg-white z-10">
                        <tr>
                            {table.columns.map((column) => {
                                const sub = column.endsWith("_min_err") ? "-err" : column.endsWith("_max_err") ? "+err"
                                    : column.endsWith("_err") ? "err" : column.endsWith("_ref") ? "reference" : null;
                                const label = columnLabel(summary, column);
                                return (
                                    <th key={column} scope="col" className="text-center border-b-2 border-hypurple px-2 py-1 align-bottom font-normal"
                                        aria-sort={sort.column === column ? (sort.reverse ? "descending" : "ascending") : undefined}>
                                        {sub ? <small className="text-hygrey">{sub}</small> : (
                                            <>
                                                <button type="button" title={label.hover} onClick={() => sortBy(column)}
                                                        aria-label={`Sort by ${label.text}`}
                                                        className={"font-semibold hover:underline " + (sort.column === column ? "text-hyred" : "text-hypurple")}>
                                                    {label.text}{sort.column === column ? (sort.reverse ? " ▾" : " ▴") : ""}
                                                </button>
                                                <br/><small className="text-hygrey uppercase">{label.units || " "}</small>
                                            </>
                                        )}
                                    </th>
                                );
                            })}
                        </tr>
                        </thead>
                        <tbody>
                        {table.rows.map((row, r) => (
                            <tr key={r} className="odd:bg-hyblue/10">
                                {row.map((cell, c) => {
                                    const column = table.columns[c];
                                    const lines = Array.isArray(cell) ? cell : [cell];
                                    const hover = table.hover[r]?.[c] ?? undefined;
                                    return (
                                        <td key={c} className="px-2 py-0.5 whitespace-nowrap">
                                            {lines.map((line, i) => (
                                                <span key={i} className={"block " + (SMALL_COLUMNS.test(column) ? "text-xs text-hygrey" : "")}>
                                                    {hover ? <CellValues value={line} values={hover}/> : line}
                                                    {column === "star_id" && i === 0 && line && (
                                                        <a href={simbadLink(line)} target="_blank" rel="noopener noreferrer" className="text-hyred ml-1"
                                                           aria-label={`${line} on SIMBAD`} title="SIMBAD">↗</a>
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
                <div className="p-3 text-hygrey">
                    Showing the first {table.rows.length} of {table.totalRows} rows.{' '}
                    {table.canLoadAll
                        ? <button type="button" className="text-hyred hover:underline" onClick={() => setShowRows(true)}>Load All</button>
                        : <>This table is too large to show on the page; <button type="button" className="text-hyred hover:underline" onClick={() => download("csv")}>download it as CSV</button> to get all {table.totalRows} rows.</>}
                </div>
            )}
        </section>
    );
}
