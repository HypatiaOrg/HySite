'use client';
// What the old pages' notices said, shown while the setting they are about is in use
import React from "react";
import Link from "next/link";
import type {Settings} from "@/data/settings";
import {Notice} from "@/components/settings/controls";
import {help_url} from "@/data/api_targets";

export default function Notices({settings}: {settings: Settings}) {
    // an axis or any filter using the parameter
    const inUse = (handle: string) => Object.entries(settings).some(([name, value]) => /^([xyz]axis1|filter\d+_1)$/.test(name) && value === handle);
    return (
        <>
            {settings.solarnorm === "original" && (
                <Notice>Abundances originally published in absolute A(X) notation cannot be shown when the &quot;Original&quot; normalization is selected since no solar normalization was specified.</Notice>
            )}
            {inUse("disk") && <Notice>Values are assigned zero for thin disk and one for thick disk.</Notice>}
            {inUse("sptype") && (
                <Notice>Spectral type values are assigned a number: F = 10, G = 20, K = 30, M = 40, plus the subclass digit (1-10), plus the roman numeral value * 0.01. Example. F2V = 12.05.</Notice>
            )}
            {settings.statistic === "mean" && (
                <Notice>Note: The mean must be calculated in linear-space for accuracy, then converted to the standard dex notation in log-space. Therefore, mean values will appear slightly more positive compared to the log-space mean, see <Link className="underline" href={help_url}>Help</Link>.</Notice>
            )}
        </>
    );
}
