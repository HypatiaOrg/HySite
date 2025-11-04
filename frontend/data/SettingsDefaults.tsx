// Parse settings to/from URL encoded strings

// Filters
export type filterType = {
    name: string | null,
    value1: number | null,
    value2: number | null,
    inverse: boolean,
}

export const filterDefault: filterType = {
    'name': null,
    'value1': null,
    'value2': null,
    'inverse': false,
}

// Plot Axes
export type axisType = {
    name: string | null,
    denominator: string,
    log: boolean,
    inverse: boolean,
}

export const xAxisDefault: axisType = {
    name: 'fe',
    denominator: 'h',
    log: false,
    inverse: false,
}

export const yAxisDefault: axisType = {
    name: 'si',
    denominator: 'h',
    log: false,
    inverse: false,
}

export const zAxisDefault: axisType = {
    name: null,
    denominator: 'h',
    log: false,
    inverse: false,
}

// Normalization
export const normDefault: string = 'lodders09'

// use the median as the default statistic, but allow mean to be toggled.
export const useMeanDefault: boolean = false

// Catalogs to be included or excluded in displayed data
export const excludeCatalogsDefault: boolean = false
export const catalogsDefault: Array<string> = []

// Stars to be either included or excluded in displayed data
export const excludeStarDefault: boolean = false
export const starsDefault: Array<string> = []

// Plot settings
export type plotSettingsType = {
    showGridLines: boolean,
    normalizeHist: boolean,
}

export const plotSettingsDefault: plotSettingsType = {
    showGridLines: false,
    normalizeHist: false,
}

// Target Selection Data
export type targetsType = {
    showAllHypatia: boolean,
    unionLogic: boolean,
    hwoTier1: boolean,
    hwoTier2: boolean,
    thinDisk: boolean,
    thickDicks: boolean,
    exoHosts: boolean,
}
export const targetsDefault: targetsType = {
    showAllHypatia: true,
    unionLogic: false,
    hwoTier1: false,
    hwoTier2: false,
    thinDisk: true,
    thickDicks: true,
    exoHosts: false,
}

// the settings typing
export type settingsType = {
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
}

// an assembly of default values
export const settingsDefault: settingsType = {
    filterSettings: [{...filterDefault}],
    xAxis: {...xAxisDefault},
    yAxis: {...yAxisDefault},
    zAxis: {...zAxisDefault},
    norm: normDefault,
    useMean: useMeanDefault,
    excludeCatalogs: excludeCatalogsDefault,
    catalogs: [...catalogsDefault],
    excludeStars: excludeStarDefault,
    stars: [...starsDefault],
    plotSettings: {...plotSettingsDefault},
    targets: {...targetsDefault},
}