'use server'

import { redirect } from 'next/navigation'


export default async function Launch(params: any) {
    console.log('Redirecting', params)
    if ('searchParams' in params && 'mode' in params['searchParams'] && params['searchParams']['mode'] === 'hist') {
        redirect('/hist')
    } else {
        redirect('/scatter')
    }
}