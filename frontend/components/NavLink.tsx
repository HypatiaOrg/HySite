'use client';
// A menu link: marked when it is the current page, and, between the plot pages, carrying the current
// plot settings along so the filters, axes and lists stay the same from one plot to the next
import Link from "next/link";
import {usePathname, useSearchParams} from "next/navigation";
import {plotURLs} from "@/lib/urls";

const style = "block px-4 md:px-3 xl:px-4 py-1 md:py-0 mb-1 md:mb-0 hover:underline hover:text-hyyellow border-2 md:border-none border-hyyellow hover:bg-hygrey hover:text-hypurple rounded-lg";
const currentStyle = " bg-white text-hypurple";

export default function NavLink({href, children}: {href: string, children: React.ReactNode}) {
    const pathname = usePathname();
    const params = useSearchParams();
    const current = pathname === href;
    const query = plotURLs.includes(pathname) && plotURLs.includes(href) ? params.toString() : "";
    return <Link href={query ? `${href}?${query}` : href} className={style + (current ? currentStyle : "")}
                 aria-current={current ? "page" : undefined}>{children}</Link>;
}
