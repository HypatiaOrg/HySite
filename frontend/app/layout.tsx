import Script from "next/script";
import type {Metadata} from "next";
import React from "react";
import "./globals.css";
import Header from "@/components/Header";

export const metadata: Metadata = {
    title: "Hypatia Catalog",
    description:
        "The Hypatia Catalog features an interactive table and multiple plotting interfaces that allow easy access and exploration of data within the Hypatia Catalog, a multidimensional, amalgamate dataset comprised of stellar abundance measurements for FGKM-type stars within 500 pc of the Sun from carefully selected literature sources that measured both [Fe/H] and at least one other element.",
    authors: [{name: "Natalie Hinkel"}, {name: "Caleb Wheeler"}],
    keywords: [
        "stellar abundance",
        "exoplanet",
        "astronomy",
        "spectroscopy",
        "elements",
        "chemistry",
        "Hypatia",
        "database",
        "physics",
        "stellar composition",
        "stellar make up",
        "stellar properties",
        "planet composition",
        "planet abundances",
        "planet make up",
        "interior structure",
        "interior mineralogy",
        "dex notation",
        "hinkle",
        "astronomy natalie",
    ],
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en">
            <head>
                <Script src="https://www.googletagmanager.com/gtag/js?id=G-TNXP7EHWXV" />
                <Script id="google-analytics">
                    {`
                      window.dataLayer = window.dataLayer || [];
                      function gtag() {dataLayer.push(arguments)}
                      gtag('js', new Date());
                      gtag('config', 'G-TNXP7EHWXV');
                    `}
                </Script>
            </head>
            <body>
                <div className="flex flex-col h-full w-full absolute top-0 left-0 z-10">
                    {/* for keyboard users: past the menu (and a plot's tool bar) to the page */}
                    <a
                        href="#main"
                        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:top-2 focus:left-2 focus:bg-hyyellow focus:text-hypurple focus:px-3 focus:py-2 focus:rounded-lg"
                    >
                        Skip to content
                    </a>
                    <header>
                        <Header />
                    </header>
                    <main id="main" tabIndex={-1} className="outline-none flex-grow">
                        {children}
                    </main>
                    {/* the web2py layout's footer: a dark band with the year */}
                    <footer className="flex-none w-full h-[60px] bg-[#333] text-[#aaa] text-sm">
                        <div className="px-[15px] m-5">Copyright &copy; {new Date().getFullYear()}</div>
                    </footer>
                </div>
            </body>
        </html>
    );
}
