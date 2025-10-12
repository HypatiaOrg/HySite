'use server'

import { redirect } from 'next/navigation'


export default async function Launch(params: any) {
    if ('searchParams' in params && 'mode' in params['searchParams']) {
        if (params['searchParams']['mode'] === 'hist') {
            redirect('/hist')
        } else if (params['searchParams']['mode'] === 'taragets') {
            redirect('/targets')
        }
    }
    redirect('/scatter')
}