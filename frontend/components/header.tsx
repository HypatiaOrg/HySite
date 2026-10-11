import React, {ReactElement, Suspense} from "react";
import Link from "next/link";
import NavLink from "@/components/nav_link";
import {
    scatter_url,
    targets_url,
    hist_url,
    density_url,
    help_url,
    about_url,
    credits_url,
    about_api_url,
} from "@/data/api_targets";

// the menu: each link marks the current page and, between plot pages, carries the plot settings along
// (components/nav_link.tsx, which reads the URL in the browser; the plain link is what the server sends first)
function MenuLink({href, children}: {href: string, children: React.ReactNode}) {
    return (
        <Suspense fallback={<Link href={href} className="block px-3 xl:px-4 py-1 md:py-0">{children}</Link>}>
            <NavLink href={href}>{children}</NavLink>
        </Suspense>
    );
}

export default function NavMenu(): ReactElement {
    return (
        <nav className="flex-none w-full items-center bg-hypurple text-white font-sans p-2 text-lg md:text-base lg:p-4 lg:text-xl 2xl:text-2xl 2xl:p-6">
            {/* on a small screen the links are one row that scrolls sideways, so the page starts higher */}
            <div className="flex w-full overflow-x-auto whitespace-nowrap gap-1 lg:gap-0 lg:overflow-visible [scrollbar-width:thin]">
                <MenuLink href="/">Home</MenuLink>
                <MenuLink href={scatter_url}>Scatter</MenuLink>
                <MenuLink href={targets_url}>Target Lists</MenuLink>
                <MenuLink href={density_url}>Density Map</MenuLink>
                <MenuLink href={hist_url}>Histogram</MenuLink>
                <div className="flex lg:flex-grow lg:justify-end gap-1 lg:gap-0">
                    <MenuLink href={help_url}>Help</MenuLink>
                    <MenuLink href={about_url}>About</MenuLink>
                    <MenuLink href={credits_url}>Acknowledgements</MenuLink>
                    <MenuLink href={about_api_url}>API</MenuLink>
                </div>
            </div>
        </nav>
    );
}
