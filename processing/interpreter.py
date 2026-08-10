# processing/interpreter.py
import pandas as pd

THRESHOLD = 20

T_CELL_MARKERS = {"cyCD3 V450-A", "CD5 PerCP-Cy5.5-A", "CD7 APC-A"}
B_CELL_MARKERS = {"CD19 PE-Cy7-A", "CD79a PE-A"}
AML_MARKERS = {"Anti-MPO FITC-A", "CD13 PE-A", "CD33 APC-R700-A", "CD117 PE-Cy7-A"}
ALL_MAJOR_MARKERS = T_CELL_MARKERS | B_CELL_MARKERS | AML_MARKERS
EXCLUDE_MARKERS = {"CD10 APC-A", "CD34 PerCP-Cy5.5-A", "Anti-HLA-DR V450-A"}


def interpret_results(combined_df: pd.DataFrame) -> str:
    combined_df = combined_df.copy()
    combined_df["Sum Percent"] = pd.to_numeric(combined_df["Sum Percent"], errors="coerce").fillna(0)

    above_threshold = set(
        combined_df.loc[combined_df["Sum Percent"] >= THRESHOLD, "Marker"].unique()
    )

    aberrant = [m for m in above_threshold if m not in ALL_MAJOR_MARKERS and m not in EXCLUDE_MARKERS]

    marker_values = combined_df.groupby("Marker")["Sum Percent"].max().to_dict()

    T_PRIMARY_MARKER = "cyCD3 V450-A"
    B_PRIMARY_MARKER = "CD19 PE-Cy7-A"
    AML_PRIMARY_MARKER = "Anti-MPO FITC-A"

    t_primary_val = marker_values.get(T_PRIMARY_MARKER, 0)
    b_primary_val = marker_values.get(B_PRIMARY_MARKER, 0)
    aml_primary_val = marker_values.get(AML_PRIMARY_MARKER, 0)

    has_t_primary = t_primary_val >= THRESHOLD
    has_b_primary = b_primary_val >= THRESHOLD
    has_aml_primary = aml_primary_val >= THRESHOLD
    primary_lineage_count = sum([has_t_primary, has_b_primary, has_aml_primary])

    if primary_lineage_count >= 2:
        result = "Acute Mixed Lineage Leukaemia"
    else:
        candidates = []
        if has_t_primary:
            candidates.append(("Acute Lymphoblastic Leukaemia (T-Cell lineage)", t_primary_val))
        if has_b_primary:
            candidates.append(("Acute Lymphoblastic Leukaemia (B-Cell lineage)", b_primary_val))
        if has_aml_primary:
            candidates.append(("Acute Myeloid Leukaemia (AML)", aml_primary_val))

        result = max(candidates, key=lambda c: c[1])[0] if candidates else "No specific leukaemia pattern detected."

    if primary_lineage_count == 1 and aberrant:
        result += f" with aberrant expression of {' & '.join(m.split()[0] for m in aberrant)}"

    return result