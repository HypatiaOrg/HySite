'use server'

import { redirect } from 'next/navigation'
import { revalidatePath } from 'next/cache'


export default async function Launch(params: any) {
    console.log('Redirecting', params)
    if ('searchParams' in params && 'mode' in params['searchParams'] && params['searchParams']['mode'] === 'hist') {
        revalidatePath('/hist')
        redirect('/hist')
    } else {
        revalidatePath('/scatter')
        redirect('/scatter')
    }
}