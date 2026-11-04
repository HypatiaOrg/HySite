import React, {ReactElement, Suspense} from "react";
import Link from "next/link";
import NavLink from "@/components/NavLink";
import Menu from "@/components/Menu";
import {scatterURL, targetsURL, histURL, densityURL, helpURL, aboutURL, creditsURL, apiPageURL} from "@/lib/urls";

// a menu link marks the current page and, between plot pages, carries the plot settings along
// (components/NavLink.tsx, which reads the URL in the browser; the plain link is what the server sends first).
// The bar itself (components/menu.tsx) folds the links behind a button on a small screen.
function MenuLink({href, children}: {href: string; children: React.ReactNode}) {
    return (
        <Suspense
            fallback={
                <Link href={href} className="block px-[15px] py-[15px] leading-5 text-white">
                    {children}
                </Link>
            }
        >
            <NavLink href={href}>{children}</NavLink>
        </Suspense>
    );
}

export default function Header(): ReactElement {
    return (
        <Menu>
            {/* no "Home" entry: the site's name at the left is the way home, as on the web2py site */}
            <MenuLink href={scatterURL}>Scatter</MenuLink>
            <MenuLink href={targetsURL}>Target Lists</MenuLink>
            <MenuLink href={densityURL}>Density Map</MenuLink>
            <MenuLink href={histURL}>Histogram</MenuLink>
            <div className="md:flex md:flex-grow md:justify-end md:items-center">
                <MenuLink href={helpURL}>Help</MenuLink>
                <MenuLink href={aboutURL}>About</MenuLink>
                <MenuLink href={creditsURL}>Acknowledgements</MenuLink>
                <MenuLink href={apiPageURL}>API</MenuLink>
            </div>
        </Menu>
    );
}
