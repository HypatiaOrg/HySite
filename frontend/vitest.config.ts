import {defineConfig} from "vitest/config";
import {fileURLToPath} from "node:url";

// the unit tests of the pure functions (npm test): the settings model and the figures
export default defineConfig({
    resolve: {alias: {"@": fileURLToPath(new URL(".", import.meta.url))}},
    test: {include: ["**/*.test.ts"], exclude: ["node_modules", ".next"]},
});
