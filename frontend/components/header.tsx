import React, {ReactElement, Suspense} from "react";
import Link from "next/link";
import NavLink from "@/components/nav_link";
import Menu from "@/components/menu";
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

// a menu link marks the current page and, between plot pages, carries the plot settings along
// (components/nav_link.tsx, which reads the URL in the browser; the plain link is what the server sends first).
// The bar itself (components/menu.tsx) folds the links behind a button on a small screen.
function MenuLink({href, children}: {href: string, children: React.ReactNode}) {
    return (
        <Suspense fallback={<Link href={href} className="block px-4 md:px-3 xl:px-4 py-1 md:py-0 mb-1 md:mb-0 border-2 md:border-none border-hyyellow rounded-lg">{children}</Link>}>
            <NavLink href={href}>{children}</NavLink>
        </Suspense>
    );
}

export default function NavMenu(): ReactElement {
    return (
        <Menu>
            <MenuLink href="/">Home</MenuLink>
            <MenuLink href={scatter_url}>Scatter</MenuLink>
            <MenuLink href={targets_url}>Target Lists</MenuLink>
            <MenuLink href={density_url}>Density Map</MenuLink>
            <MenuLink href={hist_url}>Histogram</MenuLink>
            <div className="md:flex md:flex-grow md:justify-end">
                <MenuLink href={help_url}>Help</MenuLink>
                <MenuLink href={about_url}>About</MenuLink>
                <MenuLink href={credits_url}>Acknowledgements</MenuLink>
                <MenuLink href={about_api_url}>API</MenuLink>
            </div>
        </Menu>
    );
}
