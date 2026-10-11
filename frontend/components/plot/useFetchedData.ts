'use client';
// The data for the current settings, asked for a moment after the last change. "loading" is true while the
// last answer is for other settings than the current ones, so there is no flag to get out of step.
import {useEffect, useRef, useState} from "react";
import {fetchData} from "@/lib/api";

type Answer<T> = {settings: Record<string, string>, data: T | null, error: string | null};

export function useFetchedData<T>(kind: string, settings: Record<string, string>, delay = 300):
    {data: T | null, error: string | null, loading: boolean} {
    const [answer, setAnswer] = useState<Answer<T> | null>(null);
    // the number of the latest request: an older one that answers late is ignored
    const request = useRef(0);
    useEffect(() => {
        const id = ++request.current;
        const timer = setTimeout(() => {
            fetchData<T>(kind, settings)
                .then((data) => { if (id === request.current) setAnswer({settings, data, error: null}); })
                .catch((problem: Error) => {
                    if (id === request.current) setAnswer((current) => ({settings, data: current?.data ?? null, error: problem.message}));
                });
        }, delay);
        return () => clearTimeout(timer);
    }, [kind, settings, delay]);
    return {data: answer?.data ?? null, error: answer?.error ?? null, loading: answer?.settings !== settings};
}
