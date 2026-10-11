"use client";
// The width of an element, kept up to date as the window changes
import {useCallback, useEffect, useState} from "react";

export function useElementWidth<T extends HTMLElement>(): [(node: T | null) => void, number | null] {
    const [node, setNode] = useState<T | null>(null);
    const [width, setWidth] = useState<number | null>(null);
    const ref = useCallback((element: T | null) => setNode(element), []);
    useEffect(() => {
        if (!node) return;
        const observer = new ResizeObserver((entries) => {
            for (const entry of entries) setWidth(Math.round(entry.contentRect.width));
        });
        observer.observe(node);
        return () => observer.disconnect();
    }, [node]);
    return [ref, width];
}
