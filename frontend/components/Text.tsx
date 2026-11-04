// The text pages (Help, About, ...) share these pieces, so they read as one site.
import React from "react";
import Link from "next/link";

// the web2py pages' text: Bootstrap's blue links, a 640 pixel column, 36 and 30 pixel headings, 14 pixel paragraphs
export const linkStyle = "bs-link [overflow-wrap:anywhere]";

export function Page({children}: {children: React.ReactNode}) {
    return <div className="w-[670px] max-w-full mx-auto px-[15px] pb-16">{children}</div>;
}

// a page has one h1; a later section with the h1's look is an h2 (as="h2"), its subsections h3
export function H1({id, children, as: Tag = "h1"}: {id?: string; children: React.ReactNode; as?: "h1" | "h2"}) {
    return (
        <Tag
            id={id}
            className="text-[36px] max-sm:text-[28px] leading-[1.1] font-medium text-[#333] mt-5 mb-2.5 [overflow-wrap:anywhere]"
        >
            {children}
        </Tag>
    );
}

export function H2({id, children, as: Tag = "h2"}: {id?: string; children: React.ReactNode; as?: "h2" | "h3"}) {
    return (
        <Tag
            id={id}
            className="text-[30px] max-sm:text-[24px] leading-[1.1] font-medium text-[#333] mt-5 mb-2.5 [overflow-wrap:anywhere]"
        >
            {children}
        </Tag>
    );
}

export function P({children}: {children: React.ReactNode}) {
    return <p className="text-[#333] text-sm leading-5 mb-2.5">{children}</p>;
}

export function Ul({children}: {children: React.ReactNode}) {
    return <ul className="text-[#333] text-sm leading-5 mb-2.5 list-disc pl-10">{children}</ul>;
}

// a link to another website, opened in a new tab
export function Ext({href, children}: {href: string; children: React.ReactNode}) {
    return (
        <a className={linkStyle} href={href} target="_blank" rel="noopener noreferrer">
            {children}
        </a>
    );
}

// a link to a page of this site
export function In({href, children}: {href: string; children: React.ReactNode}) {
    return (
        <Link className={linkStyle} href={href}>
            {children}
        </Link>
    );
}

// A table of definitions, such as the About page's columns: label and unit side by side on a phone with
// the description beneath; three columns with a header that stays in view on a wider screen
export type definitionType = {label: string; unit: string | null; description: React.ReactNode};
// the web2py About page's table: Bootstrap's striped table, 8 pixels of padding, a light rule between rows
const rowStyle =
    "grid grid-cols-[auto_1fr] md:grid-cols-[4.5rem_5rem_1fr] gap-x-4 gap-y-1 p-2 border-t border-[#ddd] odd:bg-[#f9f9f9]";
const labelStyle = "text-[#333]";
const unitStyle = "text-[#333]";
const descriptionStyle = "col-span-2 md:col-span-1 text-[#333]";

export function DefinitionTable({rows, name}: {rows: Array<definitionType>; name: string}) {
    return (
        <div className="text-sm leading-5 mb-5" role="table" aria-label={name}>
            <div className={rowStyle + " sticky top-0 bg-white font-bold"} role="row">
                <div className={labelStyle} role="columnheader">
                    Label
                </div>
                <div className={unitStyle} role="columnheader">
                    Unit
                </div>
                <div className={descriptionStyle + " hidden md:block"} role="columnheader">
                    Description
                </div>
            </div>
            {rows.map((row, index) => (
                <div className={rowStyle} role="row" key={index}>
                    <div className={labelStyle} role="cell">
                        {row.label}
                    </div>
                    <div className={unitStyle} role="cell">
                        {row.unit ?? "---"}
                    </div>
                    <div className={descriptionStyle} role="cell">
                        {row.description}
                    </div>
                </div>
            ))}
        </div>
    );
}
