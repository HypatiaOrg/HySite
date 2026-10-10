import { redirect } from 'next/navigation'

// the old plot page: /launch?mode=hist and /launch?mode=targets are the histogram and targets pages
export default async function Launch({searchParams}: {searchParams: Promise<Record<string, string | string[] | undefined>>}) {
    const mode = (await searchParams)['mode']
    if (mode === 'hist') {
        redirect('/hist')
    } else if (mode === 'targets') {
        redirect('/targets')
    }
    redirect('/scatter')
}
