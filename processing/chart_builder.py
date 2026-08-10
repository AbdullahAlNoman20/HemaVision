# processing/chart_builder.py
import json
import pandas as pd

THRESHOLD = 20

T_CELL_MARKERS = {"cyCD3 V450-A", "CD5 PerCP-Cy5.5-A", "CD7 APC-A"}
B_CELL_MARKERS = {"CD19 PE-Cy7-A", "CD79a PE-A"}
AML_MARKERS = {"Anti-MPO FITC-A", "CD13 PE-A", "CD33 APC-R700-A", "CD117 PE-Cy7-A"}
ALL_MAJOR_MARKERS = T_CELL_MARKERS | B_CELL_MARKERS | AML_MARKERS

T_PRIMARY_MARKER = "cyCD3 V450-A"
B_PRIMARY_MARKER = "CD19 PE-Cy7-A"
AML_PRIMARY_MARKER = "Anti-MPO FITC-A"


def _get_label(marker: str, active_lineages: set) -> str:
    labels = []
    if marker in T_CELL_MARKERS and "t" in active_lineages:
        labels.append("T")
    if marker in B_CELL_MARKERS and "b" in active_lineages:
        labels.append("B")
    if marker in AML_MARKERS and "aml" in active_lineages:
        labels.append("AML")
    return "/".join(labels)


def build_vega_lite_spec(combined_df: pd.DataFrame) -> dict:
    df = combined_df.copy()
    df["Sum Percent"] = pd.to_numeric(df["Sum Percent"], errors="coerce").fillna(0)

    marker_values = df.groupby("Marker")["Sum Percent"].max().to_dict()

    markers_above = [m for m, v in marker_values.items() if v >= THRESHOLD]

    t_primary_val = marker_values.get(T_PRIMARY_MARKER, 0)
    b_primary_val = marker_values.get(B_PRIMARY_MARKER, 0)
    aml_primary_val = marker_values.get(AML_PRIMARY_MARKER, 0)

    has_t_primary = t_primary_val >= THRESHOLD
    has_b_primary = b_primary_val >= THRESHOLD
    has_aml_primary = aml_primary_val >= THRESHOLD
    primary_lineage_count = sum([has_t_primary, has_b_primary, has_aml_primary])

    if primary_lineage_count >= 2:
        active_lineages = set()
        if has_t_primary:
            active_lineages.add("t")
        if has_b_primary:
            active_lineages.add("b")
        if has_aml_primary:
            active_lineages.add("aml")
    else:
        candidates = []
        if has_t_primary:
            candidates.append(("t", t_primary_val))
        if has_b_primary:
            candidates.append(("b", b_primary_val))
        if has_aml_primary:
            candidates.append(("aml", aml_primary_val))
        active_lineages = {max(candidates, key=lambda c: c[1])[0]} if candidates else set()

    lineage_marker_map = {"t": T_CELL_MARKERS, "b": B_CELL_MARKERS, "aml": AML_MARKERS}
    highlight_markers = set()
    for lin in active_lineages:
        highlight_markers |= lineage_marker_map[lin] & set(markers_above)

    highlight_df = df[df["Marker"].isin(highlight_markers)].copy()
    highlight_df["Bar_Label"] = highlight_df["Marker"].apply(
        lambda m: _get_label(m, active_lineages)
    )

    base_values = json.loads(df.to_json(orient="records"))
    highlight_values = json.loads(highlight_df.to_json(orient="records"))

    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "title": "Combined Results of Tube 01 and Tube 02",
        "width": "container",
        "background": "white",
        "layer": [
            {
                "data": {"values": base_values},
                "mark": "bar",
                "encoding": {
                    "x": {"field": "Marker", "type": "nominal", "sort": "-y", "title": "Marker",
                          "axis": {"labelAngle": -35}},
                    "y": {"field": "Sum Percent", "type": "quantitative", "title": "Sum Percent"},
                    "color": {"field": "Tube", "type": "nominal", "legend": {"title": "Tube"}},
                    "tooltip": [
                        {"field": "Tube", "type": "nominal"},
                        {"field": "Marker", "type": "nominal"},
                        {"field": "Sum Percent", "type": "quantitative"}
                    ]
                }
            },
            {
                "data": {"values": highlight_values},
                "mark": {"type": "bar", "strokeWidth": 2},
                "encoding": {
                    "x": {"field": "Marker", "type": "nominal", "sort": "-y"},
                    "y": {"field": "Sum Percent", "type": "quantitative"},
                    "color": {
                        "datum": "Result",
                        "scale": {"domain": ["Result"], "range": ["red"]},
                        "legend": {"title": "Result"}
                    },
                    "stroke": {"value": "red"},
                    "tooltip": [
                        {"field": "Tube", "type": "nominal"},
                        {"field": "Marker", "type": "nominal"},
                        {"field": "Sum Percent", "type": "quantitative"}
                    ]
                }
            },
            {
                "data": {"values": highlight_values},
                "mark": {"type": "text", "align": "left", "baseline": "bottom", "dx": 5, "dy": -2, "fontWeight": "bold"},
                "encoding": {
                    "x": {"field": "Marker", "type": "nominal", "sort": "-y"},
                    "y": {"field": "Sum Percent", "type": "quantitative", "stack": "zero"},
                    "text": {"field": "Bar_Label", "type": "nominal"},
                    "color": {"value": "red"}
                }
            }
        ],
        "resolve": {"scale": {"color": "independent"}}
    }

    return spec