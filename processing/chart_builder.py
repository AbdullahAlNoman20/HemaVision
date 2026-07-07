# processing/chart_builder.py
import json
import pandas as pd

THRESHOLD = 20

T_CELL_MARKERS = {"cyCD3 V450-A", "CD5 PerCP-Cy5.5-A", "CD10 APC-A"}
B_CELL_MARKERS = {"CD19 PE-Cy7-A", "CD79a PE-A", "CD10 APC-A"}
AML_MARKERS = {"Anti-MPO FITC-A", "CD13 PE-A", "CD33 APC-R700-A"}
ALL_MAJOR_MARKERS = T_CELL_MARKERS | B_CELL_MARKERS | AML_MARKERS


def _get_label(marker: str, lineage_count: int, has_t: bool, has_b: bool, has_aml: bool) -> str:
    if lineage_count >= 2:
        if marker in T_CELL_MARKERS:
            return "T"
        if marker in B_CELL_MARKERS:
            return "B"
        if marker in AML_MARKERS:
            return "AML"
        return "Mixed"
    if has_t:
        return "T"
    if has_b:
        return "B"
    if has_aml:
        return "AML"
    return ""


def build_vega_lite_spec(combined_df: pd.DataFrame) -> dict:
    df = combined_df.copy()
    df["Sum Percent"] = pd.to_numeric(df["Sum Percent"], errors="coerce").fillna(0)

    markers_above = [
        m for m in df["Marker"].unique()
        if df.loc[df["Marker"] == m, "Sum Percent"].iloc[0] >= THRESHOLD
    ]

    has_t = bool(T_CELL_MARKERS & set(markers_above))
    has_b = bool(B_CELL_MARKERS & set(markers_above))
    has_aml = bool(AML_MARKERS & set(markers_above))
    lineage_count = sum([has_t, has_b, has_aml])

    if lineage_count >= 2:
        highlight_markers = set(markers_above) & ALL_MAJOR_MARKERS
    elif has_t:
        highlight_markers = T_CELL_MARKERS & set(markers_above)
    elif has_b:
        highlight_markers = B_CELL_MARKERS & set(markers_above)
    elif has_aml:
        highlight_markers = AML_MARKERS & set(markers_above)
    else:
        highlight_markers = set()

    highlight_df = df[df["Marker"].isin(highlight_markers)].copy()
    highlight_df["Bar_Label"] = highlight_df["Marker"].apply(
        lambda m: _get_label(m, lineage_count, has_t, has_b, has_aml)
    )

    base_values = json.loads(df.to_json(orient="records"))
    highlight_values = json.loads(highlight_df.to_json(orient="records"))

    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "title": "Combined Results — Tube 001 & Tube 002",
        "background": "transparent",
        "config": {
            "axis": {"labelColor": "#8b93a3", "titleColor": "#e7ebf2", "gridColor": "#232a37"},
            "legend": {"labelColor": "#e7ebf2", "titleColor": "#e7ebf2"},
            "title": {"color": "#e7ebf2", "fontSize": 14, "font": "Inter"},
            "view": {"stroke": "transparent"}
        },
        "layer": [
            {
                "data": {"values": base_values},
                "mark": {"type": "bar", "cornerRadiusTopLeft": 3, "cornerRadiusTopRight": 3},
                "encoding": {
                    "x": {"field": "Marker", "type": "nominal", "sort": "-y", "title": None,
                          "axis": {"labelAngle": -35}},
                    "y": {"field": "Sum Percent", "type": "quantitative", "title": "Sum Percent (%)"},
                    "color": {
                        "field": "Tube", "type": "nominal",
                        "scale": {"range": ["#5eead4", "#38bdf8"]},
                        "legend": {"title": "Tube"}
                    },
                    "tooltip": [
                        {"field": "Tube", "type": "nominal"},
                        {"field": "Marker", "type": "nominal"},
                        {"field": "Sum Percent", "type": "quantitative", "format": ".2f"}
                    ]
                }
            },
            {
                "data": {"values": highlight_values},
                "mark": {"type": "bar", "stroke": "#f87171", "strokeWidth": 2, "fillOpacity": 0},
                "encoding": {
                    "x": {"field": "Marker", "type": "nominal", "sort": "-y"},
                    "y": {"field": "Sum Percent", "type": "quantitative"},
                    "tooltip": [
                        {"field": "Tube", "type": "nominal"},
                        {"field": "Marker", "type": "nominal"},
                        {"field": "Sum Percent", "type": "quantitative", "format": ".2f"}
                    ]
                }
            },
            {
                "data": {"values": highlight_values},
                "mark": {"type": "text", "align": "left", "baseline": "bottom", "dx": 5, "dy": -4,
                         "fontWeight": "bold", "color": "#f87171"},
                "encoding": {
                    "x": {"field": "Marker", "type": "nominal", "sort": "-y"},
                    "y": {"field": "Sum Percent", "type": "quantitative"},
                    "text": {"field": "Bar_Label", "type": "nominal"}
                }
            }
        ]
    }

    return spec