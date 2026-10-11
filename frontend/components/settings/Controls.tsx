"use client";
// The small controls the settings forms are made of, in the site's colors
import React, {useEffect, useLayoutEffect, useRef, useState} from "react";

export const labelStyle = "font-semibold text-hypurple";
export const inputStyle =
    "border border-hygrey/50 rounded px-2 py-1 bg-white text-black focus:outline-none focus:border-hypurple focus:ring-1 focus:ring-hypurple";
// a button: the base, then one of the three states (never two: the later class in the stylesheet would win)
export const buttonBase = "border rounded px-2 py-1 cursor-pointer";
export const plainStyle = "border-hygrey/50 bg-white text-black hover:bg-hyblue/30";
// a picked choice (an axis or filter parameter), and a column that is in the table
export const pickedStyle = "border-hypurple bg-hypurple text-white";
export const onStyle = "border-hygreen bg-hygreen text-white";
export const buttonStyle = buttonBase + " " + plainStyle;
// the classes of a button in a state
export const buttonClass = (state: "plain" | "picked" | "on", extra = "") =>
    buttonBase + " " + {plain: plainStyle, picked: pickedStyle, on: onStyle}[state] + (extra ? " " + extra : "");

export function Label({children, htmlFor}: {children: React.ReactNode; htmlFor?: string}) {
    return (
        <label htmlFor={htmlFor} className={labelStyle + " block mb-1"}>
            {children}
        </label>
    );
}

export function Toggle({
    name,
    label,
    checked,
    onChange,
    title,
}: {
    name: string;
    label: React.ReactNode;
    checked: boolean;
    onChange: (on: boolean) => void;
    title?: string;
}) {
    return (
        <label className="inline-flex items-center gap-2 cursor-pointer text-black" title={title}>
            <input
                type="checkbox"
                name={name}
                checked={checked}
                onChange={(event) => onChange(event.target.checked)}
                className="accent-hypurple h-4 w-4"
            />
            <span>{label}</span>
        </label>
    );
}

export function Select({
    name,
    value,
    onChange,
    children,
    className = "",
    ariaLabel,
}: {
    name: string;
    value: string;
    onChange: (value: string) => void;
    children: React.ReactNode;
    className?: string;
    ariaLabel?: string;
}) {
    return (
        <select
            id={name}
            name={name}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            className={inputStyle + " " + className}
            aria-label={ariaLabel}
        >
            {children}
        </select>
    );
}

// a text field that reports its value when the user leaves it or presses Enter (as the old forms did), not
// on every keystroke
export function TextField({
    name,
    value,
    onCommit,
    placeholder,
    className = "",
    ariaLabel,
}: {
    name: string;
    value: string;
    onCommit: (value: string) => void;
    placeholder?: string;
    className?: string;
    ariaLabel?: string;
}) {
    const [text, setText] = useState(value);
    // a new value from outside (a selection on the plot, a cleared list) replaces what is typed
    const [seen, setSeen] = useState(value);
    if (value !== seen) {
        setSeen(value);
        setText(value);
    }
    const commit = () => {
        if (text !== value) onCommit(text);
    };
    return (
        <input
            type="text"
            id={name}
            name={name}
            value={text}
            placeholder={placeholder}
            className={inputStyle + " " + className}
            aria-label={ariaLabel}
            onChange={(event) => setText(event.target.value)}
            onBlur={commit}
            onKeyDown={(event) => {
                if (event.key === "Enter") {
                    event.preventDefault();
                    commit();
                }
            }}
        />
    );
}

// a button that opens a panel beneath it; the panel closes on a click elsewhere or Escape
export function Popover({
    button,
    children,
    title,
    compact = false,
    ariaLabel,
}: {
    button: React.ReactNode;
    children: React.ReactNode;
    title?: string;
    compact?: boolean;
    ariaLabel?: string;
}) {
    const [open, setOpen] = useState(false);
    const ref = useRef<HTMLDivElement>(null);
    const panelRef = useRef<HTMLDivElement>(null);
    const buttonRef = useRef<HTMLButtonElement>(null);
    // closing by a choice or Escape puts the keyboard focus back on the button
    const close = () => {
        setOpen(false);
        buttonRef.current?.focus();
    };
    // the panel under its button, shifted to stay inside the window (leftwards over the plot from the
    // form's buttons, as the old dropdown opened)
    useLayoutEffect(() => {
        const wrapper = ref.current,
            panel = panelRef.current;
        if (!open || !wrapper || !panel) return;
        const box = wrapper.getBoundingClientRect(),
            width = panel.offsetWidth,
            margin = 8;
        let left = box.left;
        if (left + width > window.innerWidth - margin) left = box.right - width;
        left = Math.max(margin, Math.min(left, window.innerWidth - width - margin));
        panel.style.left = `${left - box.left}px`;
    }, [open]);
    useEffect(() => {
        if (!open) return;
        const onClick = (event: MouseEvent) => {
            if (!ref.current?.contains(event.target as Node)) setOpen(false);
        };
        const onKey = (event: KeyboardEvent) => {
            if (event.key === "Escape") close();
        };
        document.addEventListener("mousedown", onClick);
        document.addEventListener("keydown", onKey);
        return () => {
            document.removeEventListener("mousedown", onClick);
            document.removeEventListener("keydown", onKey);
        };
    }, [open]);
    return (
        <div ref={ref} className={"relative inline-block" + (compact ? " min-w-0 max-w-full" : "")}>
            <button
                type="button"
                ref={buttonRef}
                title={title}
                onClick={() => setOpen(!open)}
                aria-expanded={open}
                aria-haspopup="dialog"
                aria-label={ariaLabel}
                className={buttonStyle + " whitespace-nowrap" + (compact ? " max-w-full truncate" : "")}
            >
                {button} <span className="text-hygrey">▾</span>
            </button>
            {open && (
                <div
                    ref={panelRef}
                    className="absolute z-30 mt-1 left-0 w-max max-w-[calc(100vw-16px)] bg-white border border-hygrey/50 rounded-lg shadow-lg p-3 max-h-[80vh] overflow-auto"
                    role="dialog"
                    aria-label={ariaLabel ?? title}
                    onClick={(event) => {
                        if ((event.target as HTMLElement).closest("[data-picks]")) close();
                    }}
                >
                    {children}
                </div>
            )}
        </div>
    );
}

export function Notice({children}: {children: React.ReactNode}) {
    return (
        <div className="bg-hyblue/30 border-l-4 border-hypurple rounded-r px-3 py-2 mb-3 text-hypurple text-sm">
            {children}
        </div>
    );
}
