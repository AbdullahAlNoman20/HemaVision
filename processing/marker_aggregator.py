# processing/marker_aggregator.py
import pandas as pd


def aggregate_tube(raw_df: pd.DataFrame, tube_prefix: str, marker_groups: list, tube_label: str) -> pd.DataFrame:
    regions = [f"{tube_prefix}:UL", f"{tube_prefix}:UR", f"{tube_prefix}:LL", f"{tube_prefix}:LR"]

    filtered = raw_df[raw_df["Name"].isin(regions)].copy()
    filtered["%Parent"] = pd.to_numeric(filtered["%Parent"], errors="coerce").fillna(0)
    filtered.reset_index(drop=True, inplace=True)
    filtered["Group"] = filtered.index // 4

    results = []

    for group_idx, (marker_a, marker_b) in enumerate(marker_groups):
        group_df = filtered[filtered["Group"] == group_idx]
        percent_map = dict(zip(group_df["Name"], group_df["%Parent"]))

        ul = percent_map.get(f"{tube_prefix}:UL", 0)
        ur = percent_map.get(f"{tube_prefix}:UR", 0)
        lr = percent_map.get(f"{tube_prefix}:LR", 0)

        results.append({"Marker": marker_a, "Sum Percent": ul + ur, "Tube": tube_label})
        results.append({"Marker": marker_b, "Sum Percent": ur + lr, "Tube": tube_label})

    return pd.DataFrame(results)