"""
The data shaping behind the frontend's plots: which layer each star of a targets plot belongs to, the
histogram as named series, and the axis decisions (log, inverted) a page's settings imply. The
frontend only draws what comes back.

Until October 2026 the targets grouping lived in web2py's plot code (models/plot_bokeh.py,
create_bokeh_targets); it moved here unchanged, so the plots are the same point for point.
"""
from api.web2py.data_process import targets_metadata, is_true_str, histogram_format
from api.web2py.table import TARGET_HANDLE_SETTINGS

HISTOGRAM_SERIES = [('all', 'All Hypatia', 'maroon'), ('exo_hosts', 'Exo-Hosts', 'orange')]


def requested_target_handles(settings) -> list[str]:
    """The target lists a page has switched on, in the order the frontend always used."""
    return [handle for setting, handle in TARGET_HANDLE_SETTINGS if is_true_str(settings.get(setting, 'false'))]


def axes_from_settings(settings, labels: dict[str, str], is_loggable: dict[str, bool]) -> dict[str, dict]:
    """Per axis: the label, and whether it is logarithmic (asked for, and the parameter allows it) and inverted."""
    axes = {}
    for axis_str, label in labels.items():
        axis = axis_str[0]
        axes[axis_str] = {
            'label': label,
            'log': bool(is_true_str(settings.get(f'{axis}axislog', 'false')) and is_loggable.get(axis_str, False)),
            'inverse': is_true_str(settings.get(f'{axis}axisinv', 'false')),
        }
    return axes


def layer_options(group: str, metadata: dict) -> dict:
    default = targets_metadata.get('default', {})
    return {
        'group': group,
        'label': metadata.get('title', default.get('title', 'Hypatia Catalog')),
        'color': metadata.get('color', default.get('color', 'black')),
        'fill_alpha': metadata.get('fill_alpha', default.get('fill_alpha', 0.5)),
        'line_alpha': metadata.get('line_alpha', default.get('line_alpha', 0.5)),
        'marker': metadata.get('marker', default.get('marker', 'circle')),
        'x': [], 'y': [], 'names': [], 'handles': [],
    }


def group_targets(names: list[str], xaxis: list, yaxis: list, target_handles: list[list[str]],
                  requested_handles: list[str], show_all: bool, or_logic: bool) -> tuple[list[dict], int]:
    """
    The layers of a targets plot, in drawing order, and the number of stars counted as targets.
    With OR logic a star is a target if it is in any selected list; otherwise a star in exactly one
    selected list goes to that list's layer, a star in all of them to "combined matches", a star in
    some to "partial matches". Stars in no selected list form the "all Hypatia" background, if shown.
    """
    requested_set = set(requested_handles)

    def sort_key(handles):
        found = requested_set & set(handles)
        score = len(found)
        for handle in found:
            score += 0.01 * requested_handles.index(handle)
        return score

    scores = [sort_key(handles) for handles in target_handles]
    layers = {}
    number_of_targets = 0

    def add(group, metadata, x_point, y_point, handles, name):
        if group not in layers:
            layers[group] = layer_options(group, metadata)
        layer = layers[group]
        layer['x'].append(x_point)
        layer['y'].append(y_point)
        layer['handles'].append(handles)
        layer['names'].append(name)

    for _score, x_point, y_point, handles, name in sorted(zip(scores, xaxis, yaxis, target_handles, names)):
        handles_set = set(handles)
        if or_logic:
            if handles_set.isdisjoint(requested_handles):
                if show_all:
                    add('all_hypatia', targets_metadata['all_hypatia'], x_point, y_point, handles, name)
            else:
                add('or_matches', targets_metadata['or_matches'], x_point, y_point, handles, name)
                number_of_targets += 1
        else:
            found = {handle for handle in requested_handles if handle in handles_set}
            if not found:
                if show_all:
                    add('all_hypatia', targets_metadata['all_hypatia'], x_point, y_point, handles, name)
            elif len(found) == 1:
                handle = next(iter(found))
                add(handle, targets_metadata.get(handle, {}), x_point, y_point, handles, name)
                number_of_targets += 1
            elif requested_set.issubset(found):
                add('combined_matches', targets_metadata['combined_matches'], x_point, y_point, handles, name)
                number_of_targets += 1
            else:
                add('partial_matches', targets_metadata['partial_matches'], x_point, y_point, handles, name)
                number_of_targets += 1
    return list(layers.values()), number_of_targets


def histogram_series(graph_data: list[dict], labels: dict[str, str], from_v2: dict[str, str],
                     normalize: bool) -> dict:
    """The histogram as named series over shared bin edges, plus the x range of the data."""
    hist_all, hist_planet, edges, x_data = histogram_format(graph_data=graph_data, labels=labels, from_v2=from_v2,
                                                            normalize_hist=normalize)
    counts = {'all': hist_all.tolist(), 'exo_hosts': hist_planet.tolist()}
    return dict(
        hist_all=counts['all'], hist_planet=counts['exo_hosts'], edges=edges.tolist(), x_data=x_data,
        series=[{'id': series_id, 'label': label, 'color': color, 'counts': counts[series_id]}
                for series_id, label, color in HISTOGRAM_SERIES],
        x_range=[min(x_data), max(x_data)] if x_data else None,
    )
