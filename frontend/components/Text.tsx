// The text pages (Help, About, ...) share these pieces, so they read as one site.
import React from "react";
import Link from "next/link";

export const linkStyle = "text-hyred underline decoration-hyred/40 hover:text-hypurple hover:bg-hyyellow hover:decoration-hypurple [overflow-wrap:anywhere]";

export function Page({children}: {children: React.ReactNode}) {
    return <div className="w-full max-w-5xl mx-auto px-6 pb-16">{children}</div>;
}

// a page has one h1; a later section with the h1's look is an h2 (as="h2"), its subsections h3
export function H1({id, children, as: Tag = "h1"}: {id?: string, children: React.ReactNode, as?: "h1" | "h2"}) {
    return <Tag id={id} className="text-3xl md:text-4xl font-bold text-hypurple mt-12 mb-4">{children}</Tag>;
}

export function H2({id, children, as: Tag = "h2"}: {id?: string, children: React.ReactNode, as?: "h2" | "h3"}) {
    return <Tag id={id} className="text-2xl md:text-3xl font-semibold text-hyred mt-8 mb-3">{children}</Tag>;
}

export function P({children}: {children: React.ReactNode}) {
    return <p className="text-hygrey text-lg md:text-xl mb-5">{children}</p>;
}

export function Ul({children}: {children: React.ReactNode}) {
    return <ul className="text-hygrey text-lg md:text-xl mb-5 list-disc pl-8">{children}</ul>;
}

// a link to another website, opened in a new tab
export function Ext({href, children}: {href: string, children: React.ReactNode}) {
    return <a className={linkStyle} href={href} target="_blank" rel="noopener noreferrer">{children}</a>;
}

// a link to a page of this site
export function In({href, children}: {href: string, children: React.ReactNode}) {
    return <Link className={linkStyle} href={href}>{children}</Link>;
}

// A table of definitions, such as the About page's columns: label and unit side by side on a phone with
// the description beneath; three columns with a header that stays in view on a wider screen
export type definitionType = {label: string, unit: string | null, description: React.ReactNode};
const rowStyle = "grid grid-cols-[auto_1fr] md:grid-cols-[10rem_7rem_1fr] gap-x-6 gap-y-1 py-3 border-b border-hyblue";
const labelStyle = "font-semibold text-hypurple";
const unitStyle = "text-hygrey text-sm md:text-base md:pt-0.5";
const descriptionStyle = "col-span-2 md:col-span-1 text-hygrey";

export function DefinitionTable({rows, name}: {rows: Array<definitionType>, name: string}) {
    return (
        <div className="text-lg md:text-xl mb-8" role="table" aria-label={name}>
            <div className={rowStyle + " sticky top-0 bg-white border-b-2 border-hypurple"} role="row">
                <div className={labelStyle} role="columnheader">Label</div>
                <div className={unitStyle + " font-semibold"} role="columnheader">Unit</div>
                <div className={descriptionStyle + " font-semibold hidden md:block"} role="columnheader">Description</div>
            </div>
            {rows.map((row, index) => (
                <div className={rowStyle} role="row" key={index}>
                    <div className={labelStyle} role="cell">{row.label}</div>
                    <div className={unitStyle} role="cell">{row.unit ?? "—"}</div>
                    <div className={descriptionStyle} role="cell">{row.description}</div>
                </div>
            ))}
        </div>
    );
}
