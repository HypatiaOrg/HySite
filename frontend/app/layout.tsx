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

export function QueryClient(): ReactElement {
    return (
        <div className="flex flex-col h-full w-full absolute top-0 left-0 z-10">
            <div className="flex-none w-full items-center font-mono text-lg p-4">
                <div className="flex flex-row w-full gap-4">
                    <div>
                        <Link href="/">Home</Link>
                    </div>
                    |
                    <div>
                        <Link href="/hypatia/default/launch">Elements & Properties</Link>
                    </div>
                    |
                    <div>
                        <Link href="/hypatia/default/launch?mode=hist"> Stars With/Without Planets </Link>
                    </div>
                    <div className="flex flex-grow justify-end gap-4">
                        <div>
                            <Link href="/hypatia/default/help">Help</Link>
                        </div>
                        |
                        <div>
                            <Link href="/hypatia/default/about">About</Link>
                        </div>
                        |
                        <div>
                            <Link href="/hypatia/default/credits">Acknowledgements</Link>
                        </div>
                        |
                        <div>
                            <Link href="/api">API</Link>
                        </div>
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
            <main className="flex min-h-screen flex-col items-center justify-between p-24">
                <QueryClient/>
                {children}
            </main>
        </body>
        </html>
);
}
