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
    let urlFilters = []
    for (const aFilter in filterSettings) {
        let filterName: string | null;
        filterName = aFilter.name;
        if (filterName !== null && filterName !== undefined && filterName !== '') {
            urlFilters.push({...aFilter} as filterType)
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