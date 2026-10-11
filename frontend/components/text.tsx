// The text pages (Help, About, ...) share these pieces, so they read as one site.
import React from "react";
import Link from "next/link";

export const linkStyle = "text-hyred hover:text-hypurple hover:bg-hyyellow hover:underline";

export function Page({children}: {children: React.ReactNode}) {
    return <div className="max-w-5xl mx-auto px-6 pb-16">{children}</div>;
}

export function H1({id, children}: {id?: string, children: React.ReactNode}) {
    return <h1 id={id} className="text-3xl md:text-4xl font-bold text-hypurple mt-12 mb-4">{children}</h1>;
}

export function H2({id, children}: {id?: string, children: React.ReactNode}) {
    return <h2 id={id} className="text-2xl md:text-3xl font-semibold text-hyred mt-8 mb-3">{children}</h2>;
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
