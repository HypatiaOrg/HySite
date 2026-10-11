import {describe, expect, test} from "vitest";
import {axisRange, histFigure, scatterFigure} from "@/components/plot/figures";

describe("an axis range", () => {
    test("adds a 10 % margin each side", () => {
        expect(axisRange([0, 10])).toEqual({range: [-1, 11], type: "linear"});
    });
    test("inverted, the range is reversed", () => {
        expect(axisRange([0, 10], false, true).range).toEqual([11, -1]);
    });
    test("log: from the smallest positive value, in powers of ten; linear when nothing is positive", () => {
        const log = axisRange([1, 100], true);
        expect(log.type).toBe("log");
        expect(log.range[0]).toBeCloseTo(0);
        expect(log.range[1]).toBeCloseTo(Math.log10(109.9));
        expect(axisRange([-2, -1], true).type).toBe("linear");
    });
    test("one value still gives a range", () => {
        expect(axisRange([5]).range).toEqual([3.8, 6.2]);
    });
});

describe("the histogram figure", () => {
    const data = {
        labels: {xaxis: "[Fe/H]", yaxis: "Number of Stellar Systems"},
        series: [
            {id: "all", label: "All", color: "maroon", counts: [1, 3]},
            {id: "exo", label: "Hosts", color: "orange", counts: [0, 2]},
        ],
        edges: [0, 1, 3],
        x_range: [0, 3],
    };
    test("bars sit at the bin centres with the bins' widths, and the y range leaves room", () => {
        const figure = histFigure(data, false, false, false)!;
        const bar = figure.data[0] as {x: Array<number>; width: Array<number>};
        expect(bar.x).toEqual([0.5, 2]);
        expect(bar.width).toEqual([1, 2]);
        const [low, high] = figure.layout.yaxis?.range as [number, number];
        expect(low).toBe(0);
        expect(high).toBeCloseTo(3.6);
    });
    test("normalized, the bars are translucent and the y axis says so", () => {
        const figure = histFigure(data, true, false, false)!;
        expect((figure.data[0] as {opacity: number}).opacity).toBe(0.5);
        expect(figure.layout.yaxis?.title).toMatchObject({text: "Relative Frequency"});
    });
    test("no data, no figure", () => {
        expect(histFigure({...data, x_range: null}, false, false, false)).toBeNull();
    });
});

describe("the scatter figure", () => {
    test("counts stars in the title, and planets when the API counted them", () => {
        const base = {
            outputs: {name: ["a", "b"], xaxis: [1, 2], yaxis: [3, 4]},
            labels: {},
            axes: {
                xaxis: {label: "[Fe/H]", log: false, inverse: false},
                yaxis: {label: "[Si/H]", log: false, inverse: false},
            },
            star_count: 2,
            planet_count: null,
            is_loggable: {},
        };
        expect(scatterFigure(base, false)?.layout.title).toMatchObject({text: "2 stars selected"});
        expect(scatterFigure({...base, planet_count: 3}, false)?.layout.title).toMatchObject({
            text: "3 planets selected from 2 stars",
        });
        expect(scatterFigure({...base, outputs: {}}, false)).toBeNull();
    });
});
