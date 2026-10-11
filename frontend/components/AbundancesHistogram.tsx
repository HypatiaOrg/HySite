'use client'; // This component needs to be a Client Component

import { useState } from 'react';
import Image, {StaticImageData} from 'next/image';
import backupAbundanceHistogram from "@/public/abundances_default.png";
import {abundancesPlotURL} from "@/lib/config";


export function AbundancesHist() {
    // the plot the API drew when it started, served by nginx; the bundled copy if that is missing
    const [currentSrc, setCurrentSrc] = useState<string | StaticImageData>(abundancesPlotURL);

    const handleError = () => {
        setCurrentSrc(backupAbundanceHistogram);
    };

    return (
        <Image
            src={currentSrc}
            fill={true}
            // the plot is not on this server, so the image optimizer could not fetch it
            unoptimized={true}
            onError={handleError}
            alt="Histogram of the element abundances in the Hypatia Catalog and the number of stars for which each element has been measured."
        />
    );
};
