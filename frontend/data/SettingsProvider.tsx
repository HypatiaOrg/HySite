"use client"
import {
    settingsDefault, filterType, filterDefault,
    axisType, xAxisDefault, yAxisDefault, zAxisDefault,
    normDefault, useMeanDefault,
    excludeCatalogsDefault, catalogsDefault,
    excludeStarDefault, starsDefault,
     plotSettingsType, plotSettingsDefault, targetsType, targetsDefault,
}
    from '@/data/SettingsDefaults'
import React, {createContext, useContext} from "react";


const DataContext = createContext(settingsDefault);
export const useData = () => useContext(DataContext);


export default function DataProvider({
    filterSettings = [{...filterDefault}],
    xAxis = {...xAxisDefault},
    yAxis = {...yAxisDefault},
    zAxis = {...zAxisDefault},
    norm = normDefault,
    useMean = useMeanDefault,
    excludeCatalogs = excludeCatalogsDefault,
    catalogs = [...catalogsDefault],
    excludeStars = excludeStarDefault,
    stars = [...starsDefault],
    plotSettings = {...plotSettingsDefault},
    targets = {...targetsDefault},
    children
}:{
    filterSettings: Array<filterType>,
    xAxis: axisType,
    yAxis: axisType,
    zAxis: axisType,
    norm: string
    useMean: boolean,
    excludeCatalogs: boolean,
    catalogs: Array<string>,
    excludeStars: boolean,
    stars: Array<string>,
    plotSettings: plotSettingsType,
    targets: targetsType,
    children: React.ReactNode
}): React.ReactElement {

    return (
        <DataContext.Provider value={{
            filterSettings, xAxis, yAxis, zAxis, norm, useMean, excludeCatalogs, catalogs, excludeStars, stars,
            plotSettings, targets,
        }}>
            {children}
        </DataContext.Provider>
    );
}
