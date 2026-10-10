import {
    settingsType,
    settingsDefault,
    filterDefault, filterType
} from "@/data/SettingsDefaults";


export function toURL(settings: settingsType = settingsDefault): string {
    const {
        filterSettings, xAxis, yAxis, zAxis, norm, useMean, excludeCatalogs, catalogs, excludeStars, stars,
        plotSettings, targets,
    }: settingsType = settings
    let urlData = {}
    const urlFilters: Array<filterType> = []
    // only the filters that have a name set
    for (const aFilter of filterSettings) {
        const filterName = aFilter.name;
        if (filterName !== null && filterName !== undefined && filterName !== '') {
            urlFilters.push({...aFilter})
        }
    }
    urlData = {
        filterSettings: urlFilters,
        xAxis: xAxis,
        yAxis: yAxis,
        zAxis: zAxis,
    }
    return JSON.stringify(urlData);

}