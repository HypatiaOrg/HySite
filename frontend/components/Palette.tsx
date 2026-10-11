'use client';
// The site's named colors, read from the CSS theme (app/globals.css) so this always shows the real
// values. Each swatch has a color picker that changes the variable on this page alone, to try a color
// against every piece of the site at once; the value to keep goes into globals.css.
import {useState, useSyncExternalStore} from "react";

export const siteColors = [
    {name: "hypurple", role: "menu bar, main headings"},
    {name: "hyred", role: "subheadings, links"},
    {name: "hyyellow", role: "link hover, home page gradient"},
    {name: "hyblue", role: "captions, table row lines"},
    {name: "hygrey", role: "body text"},
    {name: "hygreen", role: "not used yet"},
];

// the theme's values, read from the browser once; the server (which has no stylesheet) renders none
const noColors: Record<string, string> = {};
let themeColors: Record<string, string> | null = null;
function readTheme(): Record<string, string> {
    if (themeColors === null) {
        const style = getComputedStyle(document.documentElement);
        themeColors = Object.fromEntries(
            siteColors.map(({name}) => [name, style.getPropertyValue(`--color-${name}`).trim()]));
    }
    return themeColors;
}
const noSubscription = () => () => {};

export function Palette() {
    const original = useSyncExternalStore(noSubscription, readTheme, () => noColors);
    // the colors tried on this page, by name; the theme's value where there is none
    const [tried, setTried] = useState<Record<string, string>>({});
    const colors = {...original, ...tried};

    const setColor = (name: string, value: string) => {
        document.documentElement.style.setProperty(`--color-${name}`, value);
        setTried({...tried, [name]: value});
    };
    const reset = () => {
        for (const name of Object.keys(tried)) {
            document.documentElement.style.removeProperty(`--color-${name}`);
        }
        setTried({});
    };
    const changed = Object.keys(tried).length > 0;

    return (
        <div className="mb-8">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                {siteColors.map(({name, role}) => (
                    <label key={name} className="block cursor-pointer">
                        <div className="h-24 rounded-lg border border-hyblue" style={{background: `var(--color-${name})`}}/>
                        <div className="pt-2 font-semibold text-hypurple">{name}</div>
                        <div className="text-hygrey text-sm">{role}</div>
                        <div className="text-hygrey font-mono text-sm pt-1">
                            {colors[name] ?? ""}
                            {colors[name] !== original[name] && <span> (was {original[name]})</span>}
                        </div>
                        <input
                            type="color"
                            className="mt-1 h-8 w-16 cursor-pointer"
                            value={colors[name] ?? "#000000"}
                            onChange={(event) => setColor(name, event.target.value)}
                            aria-label={`Try another color for ${name}`}
                        />
                    </label>
                ))}
            </div>
            <div className="pt-4 text-hygrey">
                Pick a color to try it on everything on this page. Nothing is saved: a value to keep goes into{' '}
                <code>frontend/app/globals.css</code>.{' '}
                {changed && (
                    <button onClick={reset} className="text-hyred hover:text-hypurple hover:bg-hyyellow hover:underline">
                        Back to the theme&apos;s colors
                    </button>
                )}
            </div>
        </div>
    );
}
