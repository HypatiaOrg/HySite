import DataProvider from "@/data/UserSettings";
import {getHomeData} from "@/data/fetch_data";
import React from "react";


export default async function UserSettingLayout({children,}: Readonly<{children: React.ReactNode;}>) {
    const counts = await getHomeData();
    return (
        <DataProvider
            total_stars={counts['stars']}
            total_planet_hosts={counts['stars_with_planets']}
            total_multistar_systems={counts['stars_multistar']}
            total_elements={counts['elements']}
            total_catalogs={counts['catalogs']}
            total_abundances={counts['abundances']}>
            {children}
        </DataProvider>
    )
}