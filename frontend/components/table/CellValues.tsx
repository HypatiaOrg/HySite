"use client";
import React, {useState} from "react";

// a cell whose value came from several catalogs: a tooltip for the mouse, and a button that opens the
// catalog values for the keyboard and a screen reader
export default function CellValues({value, values}: {value: string; values: string}) {
    const [open, setOpen] = useState(false);
    const lines = values
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);
    return (
        <span className="relative">
            <button
                type="button"
                title={values}
                aria-expanded={open}
                onClick={() => setOpen(!open)}
                onKeyDown={(event) => {
                    if (event.key === "Escape") setOpen(false);
                }}
                aria-label={`${value}, from ${lines.length} catalog values`}
                className="font-semibold cursor-help hover:underline focus:outline-2 focus:outline-hypurple rounded"
            >
                {value}
            </button>
            {open && (
                <span
                    role="dialog"
                    aria-label="The catalog values"
                    onBlur={() => setOpen(false)}
                    className="absolute z-20 left-0 top-full mt-1 bg-white border border-hygrey/50 rounded shadow-lg px-2 py-1 text-xs text-black whitespace-nowrap"
                >
                    {lines.map((line, i) => (
                        <span key={i} className="block">
                            {line}
                        </span>
                    ))}
                </span>
            )}
        </span>
    );
}
