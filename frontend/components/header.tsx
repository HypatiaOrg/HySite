import React, {ReactElement} from "react";
import Link from "next/link";
import {
    scatter_url,
    targets_url,
    hist_url,
    help_url,
    about_url,
    credits_url,
    about_api_url,
} from "@/data/api_targets";
import {toURL} from "@/data/SettingsURL";

const linkTextStyle = "px-4 hover:underline hover:text-hyyellow border-2 md:border-none border-hyyellow hover:bg-hygrey hover:text-hypurple rounded-lg";



export default function NavMenu(): ReactElement {
    console.log("Rendering NavMenu, ToURL example:", toURL());
    return (
        <div className="flex-none w-full items-center bg-hypurple text-white font-sans p-2 text-3xl md:text-base lg:p-4 lg:text-xl 2xl:text-2xl 2xl:p-6">
            <div className="md:flex w-full">
                <div className={linkTextStyle}>
                    <Link href="/">Home</Link>
                </div>
                <div className={linkTextStyle}>
                    <Link href={scatter_url}>Scatter</Link>
                </div>
                <div className={linkTextStyle}>
                    <Link href={targets_url}>Target Lists</Link>
                </div>
                <div className={linkTextStyle}>
                    <Link href={hist_url}>Histogram</Link>
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