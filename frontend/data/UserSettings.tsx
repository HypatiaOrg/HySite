"use client"
import React, {createContext, useContext} from "react";


export const dataProviderDefaultValue = {
    total_stars: 0,
    total_planet_hosts: 0,
    total_multistar_systems: 0,
    total_elements: 0,
    total_catalogs: 0,
    total_abundances: 0,
}

const DataContext = createContext(dataProviderDefaultValue);
export const useData = () => useContext(DataContext);

export default function DataProvider({
    total_stars = 0,
    total_planet_hosts = 0,
    total_multistar_systems = 0,
    total_elements = 0,
    total_catalogs = 0,
    total_abundances = 0,
    children
}:{
    total_stars: number,
    total_planet_hosts: number,
    total_multistar_systems: number,
    total_elements: number,
    total_catalogs: number,
    total_abundances: number,
    children: React.ReactNode
}): React.ReactElement {
    // Statistics for the entire database


    return (
        <DataContext.Provider value={{
            total_stars, total_planet_hosts, total_multistar_systems, total_elements, total_catalogs, total_abundances
        }}>
            {children}
        </DataContext.Provider>
    );
}
