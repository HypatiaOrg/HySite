'use client'; // This component needs to be a Client Component

import { useState } from 'react';
import Image, {StaticImageData} from 'next/image';
import abundanceHistogram from "@/public/abundances.png";

export function AbundancesHist() {
    const [currentSrc, setCurrentSrc] = useState<string | StaticImageData>("/hypatia/api/plots/abundances_histogram.png");

    const handleError = () => {
        setCurrentSrc(abundanceHistogram);
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