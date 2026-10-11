import React, {ReactElement, Suspense} from "react";
import Link from "next/link";
import NavLink from "@/components/NavLink";
import Menu from "@/components/Menu";
import {scatterURL, targetsURL, histURL, densityURL, helpURL, aboutURL, creditsURL, apiPageURL} from "@/lib/urls";

// a menu link marks the current page and, between plot pages, carries the plot settings along
// (components/NavLink.tsx, which reads the URL in the browser; the plain link is what the server sends first).
// The bar itself (components/menu.tsx) folds the links behind a button on a small screen.
function MenuLink({href, children}: {href: string, children: React.ReactNode}) {
    return (
        <Suspense fallback={<Link href={href} className="block px-4 md:px-3 xl:px-4 py-1 md:py-0 mb-1 md:mb-0 border-2 md:border-none border-hyyellow rounded-lg">{children}</Link>}>
            <NavLink href={href}>{children}</NavLink>
        </Suspense>
    );
}

export default function Header(): ReactElement {
    return (
        <Menu>
            <MenuLink href="/">Home</MenuLink>
            <MenuLink href={scatterURL}>Scatter</MenuLink>
            <MenuLink href={targetsURL}>Target Lists</MenuLink>
            <MenuLink href={densityURL}>Density Map</MenuLink>
            <MenuLink href={histURL}>Histogram</MenuLink>
            <div className="md:flex md:flex-grow md:justify-end">
                <MenuLink href={helpURL}>Help</MenuLink>
                <MenuLink href={aboutURL}>About</MenuLink>
                <MenuLink href={creditsURL}>Acknowledgements</MenuLink>
                <MenuLink href={apiPageURL}>API</MenuLink>
            </div>
        </Menu>
    );
}
