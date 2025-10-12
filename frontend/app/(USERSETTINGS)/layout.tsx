import DataProvider from "@/data/UserSettings";
import React from "react";


export default function UserSettingLayout({children,}: Readonly<{children: React.ReactNode;}>) {
    return (
        <DataProvider
            filterSettings={[{name: "default", value1: 0, value2: 100, inverse: false}]}
        >
            {children}
        </DataProvider>
    )
}