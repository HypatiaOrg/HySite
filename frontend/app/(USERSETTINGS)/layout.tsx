import DataProvider from "@/data/SettingsProvider";
import {settingsDefault} from "@/data/SettingsDefaults"
import React from "react";


export default function UserSettingLayout({children,}: Readonly<{children: React.ReactNode;}>) {
    return (
        <DataProvider
            {...settingsDefault}
        >
            {children}
        </DataProvider>
    )
}