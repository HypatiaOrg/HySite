"use client";
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
        const onKey = (event: KeyboardEvent) => {
            if (event.key === "Escape") setOpen(false);
        };
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, [open]);

    return (
        <nav className="flex-none w-full bg-hypurple text-white text-sm leading-5 border border-[#080808] mb-5 px-[15px]">
            <div className="flex items-center justify-between md:hidden">
                <Link href="/" className="text-[30px] leading-5 py-[15px]">
                    Hypatia Catalog
                </Link>
                <button
                    type="button"
                    onClick={() => setOpen(!open)}
                    aria-expanded={open}
                    aria-controls="site-menu"
                    className="px-3 py-1 rounded-lg border-2 border-hyyellow text-2xl leading-none hover:bg-hygrey hover:text-hypurple"
                >
                    <span aria-hidden="true">{open ? "✕" : "☰"}</span>
                    <span className="sr-only">{open ? "Close the menu" : "Open the menu"}</span>
                </button>
            </div>
            <div
                id="site-menu"
                className={
                    (open ? "block pt-2" : "hidden") +
                    " md:flex md:items-center w-full md:overflow-x-auto md:whitespace-nowrap lg:overflow-visible [scrollbar-width:thin] md:min-h-[50px]"
                }
            >
                {/* the site's name, the way home, at the left of the bar (the web2py site's navbar brand) */}
                <Link href="/" className="hidden md:block text-[30px] leading-5 py-[15px] pr-[15px] text-white">
                    Hypatia Catalog
                </Link>
                {children}
            </div>
        </nav>
    );
}
