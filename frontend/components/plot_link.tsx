'use client';
// A link to a plot page that carries the current plot settings along when the visitor is on another
// plot page, so the filters, axes and lists stay the same from one plot to the next
import Link from "next/link";
import {usePathname, useSearchParams} from "next/navigation";
import {plot_urls} from "@/data/api_targets";

export default function PlotLink({href, children}: {href: string, children: React.ReactNode}) {
    const pathname = usePathname();
    const params = useSearchParams();
    const query = plot_urls.includes(pathname) ? params.toString() : "";
    return <Link href={query ? `${href}?${query}` : href}>{children}</Link>;
}
