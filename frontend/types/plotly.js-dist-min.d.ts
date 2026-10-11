// the minified bundle has no types of its own; it is plotly.js
declare module "plotly.js-dist-min" {
    import * as Plotly from "plotly.js";
    export = Plotly;
}
