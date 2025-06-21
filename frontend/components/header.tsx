import React, {ReactElement} from "react";
import Link from "next/link";
import {scatter_url, hist_url, help_url, about_url, credits_url, about_api_url} from "@/data/api_targets";

const linkTextStyle = "px-4 hover:underline hover:text-hyyellow border-2 md:border-none border-hyyellow hover:bg-hygrey hover:text-hypurple rounded-lg";



export default function NavMenu(): ReactElement {
    return (
        <div className="flex-none w-full items-center bg-hypurple text-white font-mono p-2 text-xl lg:p-4 lg:text-base 2xl:text-xl 2xl:p-6">
            <div className="md:flex w-full">
                <div className={linkTextStyle}>
                    <Link href="/">Home</Link>
                </div>
                <div className={linkTextStyle}>
                    <Link href={scatter_url}>Elements & Properties</Link>
                </div>
                <div className={linkTextStyle}>
                    <Link href={hist_url}> Stars With/Without Planets </Link>
                </div>
                <div className="md:flex md:flex-grow md:justify-end">
                    <div className={linkTextStyle}>
                        <Link href={help_url}>Help</Link>
                    </div>
                    <div className={linkTextStyle}>
                        <Link href={about_url}>About</Link>
                    </div>
                    <div className={linkTextStyle}>
                        <Link href={credits_url}>Acknowledgements</Link>
                    </div>
                    <div className={linkTextStyle}>
                        <Link href={about_api_url}>API</Link>
                    </div>
                </div>
            </div>
        </div>
    );
}