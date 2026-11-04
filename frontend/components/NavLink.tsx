"use client";
// A menu link: marked when it is the current page, and, between the plot pages, carrying the current
// plot settings along so the filters, axes and lists stay the same from one plot to the next
import Link from "next/link";
import {usePathname, useSearchParams} from "next/navigation";
import {plotURLs} from "@/lib/urls";

// a link as the web2py menu drew it: white on the purple bar, 15px of padding; the current page white with purple
// text in a rounded pill, light grey under the mouse (issue #35)
const style = "block px-[15px] py-[15px] leading-5 text-white hover:text-white";
const currentStyle = " !bg-white !text-hypurple rounded-lg !p-[7px] !m-2 hover:!bg-[#c8c8c8]";

export default function NavLink({href, children}: {href: string; children: React.ReactNode}) {
    const pathname = usePathname();
    const params = useSearchParams();
    const current = pathname === href;
    const query = plotURLs.includes(pathname) && plotURLs.includes(href) ? params.toString() : "";
    return (
        <Link
            href={query ? `${href}?${query}` : href}
            className={style + (current ? currentStyle : "")}
            aria-current={current ? "page" : undefined}
        >
            {children}
        </Link>
    );
}
