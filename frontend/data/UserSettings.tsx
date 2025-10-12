"use client"
import React, {createContext, useContext} from "react";


export const dataProviderDefaultValue = {
    filterSettings: [{}],
}

const DataContext = createContext(dataProviderDefaultValue);
export const useData = () => useContext(DataContext);


type filterType= {
    name: string,
    value1: number,
    value2: number,
    inverse: boolean,
}

export default function DataProvider({
    filterSettings=[],
    children
}:{
    filterSettings: filterType[],
    children: React.ReactNode
}): React.ReactElement {

    return (
        <DataContext.Provider value={{
            filterSettings,
        }}>
            {children}
        </DataContext.Provider>
    );
}
