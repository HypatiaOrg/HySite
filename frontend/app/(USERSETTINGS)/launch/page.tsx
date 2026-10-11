import { redirect } from 'next/navigation'

// the old plot page: /launch?mode=hist and /launch?mode=targets are the histogram and targets pages; the
// other settings in the URL carry over
export default async function Launch({searchParams}: {searchParams: Promise<Record<string, string | string[] | undefined>>}) {
    const params = await searchParams
    const mode = params['mode']
    const query = new URLSearchParams()
    for (const [name, value] of Object.entries(params)) {
        if (typeof value === 'string' && name !== 'mode') query.set(name, value)
    }
    const suffix = query.size ? '?' + query.toString() : ''
    if (mode === 'hist') {
        redirect('/hist' + suffix)
    } else if (mode === 'targets') {
        redirect('/targets' + suffix)
    }
    redirect('/scatter' + suffix)
}
