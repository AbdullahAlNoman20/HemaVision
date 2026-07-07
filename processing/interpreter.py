# processing/interpreter.py
import pandas as pd

THRESHOLD = 20

T_CELL_MARKERS = {"cyCD3 V450-A", "CD5 PerCP-Cy5.5-A", "CD7 APC-A", "CD10 APC-A"}
B_CELL_MARKERS = {"CD19 PE-Cy7-A", "CD79a PE-A", "CD10 APC-A"}
AML_MARKERS = {"Anti-MPO FITC-A", "CD13 PE-A", "CD33 APC-R700-A", "CD117 PE-Cy7-A"}
ALL_MAJOR_MARKERS = T_CELL_MARKERS | B_CELL_MARKERS | AML_MARKERS
EXCLUDE_MARKERS = {"CD10 APC-A", "CD34 PerCP-Cy5.5-A", "Anti-HLA-DR V450-A", "Anti-MPO FITC-A"}


def interpret_results(combined_df: pd.DataFrame) -> str:
    combined_df = combined_df.copy()
    combined_df["Sum Percent"] = pd.to_numeric(combined_df["Sum Percent"], errors="coerce").fillna(0)

    above_threshold = set(
        combined_df.loc[combined_df["Sum Percent"] >= THRESHOLD, "Marker"].unique()
    )

    major_above = above_threshold & ALL_MAJOR_MARKERS
    aberrant = [m for m in above_threshold if m not in ALL_MAJOR_MARKERS and m not in EXCLUDE_MARKERS]

    has_t = bool(T_CELL_MARKERS & major_above)
    has_b = bool(B_CELL_MARKERS & major_above)
    has_aml = bool(AML_MARKERS & major_above)
    lineage_count = sum([has_t, has_b, has_aml])

    if lineage_count >= 2:
        result = "Acute Mixed Lineage Leukaemia"
    elif has_t:
        result = "Acute Lymphoblastic Leukaemia (T-Cell lineage)"
    elif has_b:
        result = "Acute Lymphoblastic Leukaemia (B-Cell lineage)"
    elif has_aml:
        result = "Acute Myeloid Leukaemia (AML)"
    else:
        result = "No specific leukaemia pattern detected based on the criteria."

    if lineage_count == 1 and aberrant:
        result += f" with aberrant expression of {' & '.join(m.split()[0] for m in aberrant)}"

    return result