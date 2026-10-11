// The pieces of the API page: an endpoint's section, its input and output fields, the Python to copy,
// and the result it gives.
import React from "react";
import {H2} from "@/components/text";

export function Endpoint({id, name, children}: {id: string, name: string, children: React.ReactNode}) {
    return (
        <section id={id} className="mb-12">
            <H2>GET {name}</H2>
            {children}
        </section>
    );
}

// a question and its answer
export function Question({id, q, children}: {id?: string, q: string, children: React.ReactNode}) {
    return (
        <div id={id} className="mb-6">
            <h3 className="text-xl md:text-2xl font-semibold text-hypurple mb-2">{q}</h3>
            <div className="text-hygrey text-lg md:text-xl">{children}</div>
        </div>
    );
}

// the inputs or outputs of an endpoint
export function Fields({title, children}: {title: string, children: React.ReactNode}) {
    return (
        <div className="mb-4">
            <h3 className="text-lg md:text-xl font-semibold text-hypurple mb-1">{title}</h3>
            <dl className="text-hygrey text-lg md:text-xl">{children}</dl>
        </div>
    );
}

export function Field({name, children}: {name: string, children: React.ReactNode}) {
    return (
        <div className="md:grid md:grid-cols-[12rem_1fr] md:gap-x-4 py-1 border-b border-hyblue/50">
            <dt><code className="text-hyred">{name}</code></dt>
            <dd>{children}</dd>
        </div>
    );
}

export function Note({children}: {children: React.ReactNode}) {
    return <p className="text-hygrey text-lg md:text-xl mb-4">{children}</p>;
}

const preStyle = "overflow-x-auto rounded-lg p-4 mb-4 text-sm md:text-base leading-relaxed";

// the request, as a link that runs it
export function Request({url}: {url: string}) {
    const full = "https://hypatiacatalog.com" + url;
    return (
        <p className="text-hygrey text-lg md:text-xl mb-2">
            GET <a className="text-hyred hover:text-hypurple hover:underline break-all" href={url}>{full}</a>
        </p>
    );
}

// Python to copy; the yellow carries on from the old page, which highlighted its snippets so
export function Python({children}: {children: string}) {
    return (
        <>
            <p className="text-hygrey text-lg md:text-xl mb-1">Python code:</p>
            <pre className={preStyle + " bg-hyyellow/30 border border-hyyellow"}><code>{children.trim()}</code></pre>
        </>
    );
}

// what the request returns
export function Result({children}: {children: string}) {
    return (
        <>
            <p className="text-hygrey text-lg md:text-xl mb-1">Result:</p>
            <pre className={preStyle + " bg-hygrey/10 text-hygrey"}><code>{children.trim()}</code></pre>
        </>
    );
}

export function Pre({children}: {children: string}) {
    return <pre className={preStyle + " bg-hygrey/10 text-hygrey"}><code>{children.trim()}</code></pre>;
}
