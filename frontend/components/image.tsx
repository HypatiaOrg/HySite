'use client'; // This component needs to be a Client Component

import { useState } from 'react';
import Image, {StaticImageData} from 'next/image';
import abundanceHistogram from "@/public/abundances.png";
import backupAbundanceHistogram from "@/public/abundances_default.png";


export function AbundancesHist() {
    const [currentSrc, setCurrentSrc] = useState<string | StaticImageData>(abundanceHistogram);

    const handleError = () => {
        setCurrentSrc(backupAbundanceHistogram);
    };

    return (
        <Image
            src={currentSrc}
            fill={true}
            onError={handleError}
            alt="Histogram of the element abundances in the Hypatia Catalog and the number of stars for which each element has been measured."
        />
    );
};