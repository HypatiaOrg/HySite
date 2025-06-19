import Link from 'next/link';
import Script from 'next/script'
import type { Metadata} from "next";
import React, {ReactElement} from "react";
import { Inter } from "next/font/google";
import "./globals.css";



const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Hypatia Catalog",
    description: "The Hypatia Catalog Database features an interactive table and multiple plotting interfaces that allow easy access and exploration of data within the Hypatia Catalog, a multidimensional, amalgamate dataset comprised of stellar abundance measurements for FGKM-type stars within 500 pc of the Sun from carefully selected literature sources that measured both [Fe/H] and at least one other element.",
    authors: [{name: 'Natalie Hinkel'}, {name: 'Caleb Wheeler'}],
    keywords: ["stellar abundance", "exoplanet", "astronomy", "spectroscopy", "elements", "chemistry", "Hypatia", "database", "physics", "stellar composition", "stellar make up", "stellar properties", "planet composition", "planet abundances", "planet make up", "interior structure", "interior mineralogy", "dex notation", "hinkle", "astronomy natalie"]

};


const linkTextStyle = "px-4 hover:underline hover:text-hyyellow border-2 md:border-none border-hyyellow hover:bg-hygrey hover:text-hypurple rounded-lg";


export function NavMenu(): ReactElement {
    return (
        <div className="flex-none w-full items-center bg-hypurple text-white font-mono p-2 text-xl lg:p-4 lg:text-base 2xl:text-xl 2xl:p-6">
            <div className="md:flex w-full">
                <div className={linkTextStyle}>
                    <Link href="/">Home</Link>
                </div>
                <div className={linkTextStyle}>
                    <Link href="/hypatia/default/launch">Elements & Properties</Link>
                </div>
                <div className={linkTextStyle}>
                    <Link href="/hypatia/default/launch?mode=hist"> Stars With/Without Planets </Link>
                </div>
                <div className="md:flex md:flex-grow md:justify-end">
                    <div className={linkTextStyle}>
                        <Link href="/hypatia/default/help">Help</Link>
                    </div>
                    <div className={linkTextStyle}>
                        <Link href="/hypatia/default/about">About</Link>
                    </div>
                    <div className={linkTextStyle}>
                        <Link href="/hypatia/default/credits">Acknowledgements</Link>
                    </div>
                    <div className={linkTextStyle}>
                        <Link href="/api">API</Link>
                    </div>
                </div>
            </div>
        </div>
    );
}


export default function RootLayout({
                                       children,
                                   }: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <head>
                <Script src="https://www.googletagmanager.com/gtag/js?id=G-TNXP7EHWXV"/>
                <Script id="google-analytics">
                    {`
                      window.dataLayer = window.dataLayer || [];
                      function gtag() {dataLayer.push(arguments)}
                      gtag('js', new Date());
                      gtag('config', 'G-TNXP7EHWXV');
                    `}
                </Script>
            </head>
            <body className={inter.className}>
                <main className="flex flex-col h-full w-full absolute top-0 left-0 z-10">
                    <NavMenu/>
                    {children}
                </main>
            </body>
        </html>
);
}
