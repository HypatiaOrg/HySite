// The pieces of the API page. The page is a definition list like the old one: labels in a left
// column, content on the right, and callout panels for the notices. On a phone the label sits above
// its content.
import React from "react";
import {linkStyle} from "@/components/Text";

// a panel for a notice: "info" for what to know, "note" for a longer set of remarks
export function Callout({kind, children}: {kind: "info" | "note"; children: React.ReactNode}) {
    const colors =
        kind === "info" ? "bg-hyblue/30 border-hypurple text-hypurple" : "bg-hyyellow/20 border-hyyellow text-hygrey";
    return <div className={"border-l-4 rounded-r-lg px-5 py-4 mb-6 text-lg md:text-xl " + colors}>{children}</div>;
}

export function Definitions({children}: {children: React.ReactNode}) {
    return <dl className="text-lg md:text-xl">{children}</dl>;
}

// one label with its content; "heading" for a query (red, larger) rather than a question
export function Entry({
    id,
    label,
    heading = false,
    children,
}: {
    id?: string;
    label: string;
    heading?: boolean;
    children: React.ReactNode;
}) {
    const labelStyle = heading
        ? "text-xl md:text-2xl font-semibold text-hyred md:text-right md:pt-1"
        : "font-semibold text-hypurple md:text-right";
    return (
        <div
            id={id}
            className={
                "md:grid md:grid-cols-[13rem_1fr] md:gap-x-8 py-4 scroll-mt-4" +
                (heading ? " border-t border-hyblue mt-4" : "")
            }
        >
            <dt className={labelStyle + " mb-2 md:mb-0"}>{label}</dt>
            <dd className="min-w-0 text-hygrey">{children}</dd>
        </div>
    );
}

// the inputs or outputs of a query: a narrower label column inside the entry
export function Fields({title, children}: {title: string; children: React.ReactNode}) {
    // its own <dl>: a <dt> inside the entry's <dd> without one makes the browser close that <dd>,
    // and the page no longer matches what React rendered (hydration error #418)
    return (
        <dl className="md:grid md:grid-cols-[6rem_1fr] md:gap-x-4 mb-4">
            <dt className="font-semibold text-hypurple">{title}</dt>
            <dd className="min-w-0">{children}</dd>
        </dl>
    );
}

// a field: its name, then what it holds
export function Field({name, children}: {name: string; children: React.ReactNode}) {
    return (
        <div className="mb-1 [overflow-wrap:anywhere]">
            <code className="text-hyred">{name}</code> {children}
        </div>
    );
}

export function Note({children}: {children: React.ReactNode}) {
    return <p className="mb-4">{children}</p>;
}

const preStyle = "overflow-x-auto rounded-lg p-4 mb-4 text-sm md:text-base leading-relaxed";

// the request, as a link that runs it
export function Request({url}: {url: string}) {
    const full = "https://hypatiacatalog.com" + url;
    return (
        <p className="mb-2">
            GET{" "}
            <a className={linkStyle + " break-all"} href={url}>
                {full}
            </a>
        </p>
    );
}

// Python to copy; the yellow carries on from the old page, which highlighted its snippets so
export function Python({children}: {children: string}) {
    return (
        <>
            <p className="mb-1">Python code:</p>
            <pre
                tabIndex={0}
                aria-label="Python code"
                className={
                    preStyle +
                    " bg-hyyellow/30 border border-hyyellow text-black focus:outline-2 focus:outline-hypurple"
                }
            >
                <code>{children.trim()}</code>
            </pre>
        </>
    );
}

// what the request returns
export function Result({children}: {children: string}) {
    return (
        <>
            <p className="mb-1">Result:</p>
            <pre
                tabIndex={0}
                aria-label="Result"
                className={preStyle + " bg-hygrey/10 focus:outline-2 focus:outline-hypurple"}
            >
                <code>{children.trim()}</code>
            </pre>
        </>
    );
}

export function Pre({children}: {children: string}) {
    return (
        <pre tabIndex={0} className={preStyle + " bg-hygrey/10 focus:outline-2 focus:outline-hypurple"}>
            <code>{children.trim()}</code>
        </pre>
    );
}
