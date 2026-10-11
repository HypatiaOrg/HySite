'use client';
// The menu bar. On a small screen it is the site's name and a button that pops the links open as a
// vertical list, closed again by a choice, the button, or Escape; from md up the links are always a row.
import React, {useEffect, useState} from "react";
import Link from "next/link";
import {usePathname} from "next/navigation";

export default function Menu({children}: {children: React.ReactNode}) {
    const [open, setOpen] = useState(false);
    // a choice closes the menu: the page changes, the list folds away
    const pathname = usePathname();
    const [seenPath, setSeenPath] = useState(pathname);
    if (pathname !== seenPath) {
        setSeenPath(pathname);
        setOpen(false);
    }
    useEffect(() => {
        if (!open) return;
        const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") setOpen(false); };
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, [open]);

    return (
        <nav className="flex-none w-full bg-hypurple text-white font-sans p-2 text-xl md:text-base lg:p-4 lg:text-xl 2xl:text-2xl 2xl:p-6">
            <div className="flex items-center justify-between md:hidden">
                <Link href="/" className="font-bold px-2">Hypatia Catalog</Link>
                <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} aria-controls="site-menu"
                        className="px-3 py-1 rounded-lg border-2 border-hyyellow text-2xl leading-none hover:bg-hygrey hover:text-hypurple">
                    <span aria-hidden="true">{open ? "✕" : "☰"}</span>
                    <span className="sr-only">{open ? "Close the menu" : "Open the menu"}</span>
                </button>
            </div>
            <div id="site-menu" className={(open ? "block pt-2" : "hidden") + " md:flex w-full md:overflow-x-auto md:whitespace-nowrap lg:overflow-visible [scrollbar-width:thin]"}>
                {children}
            </div>
        </nav>
    );
}
