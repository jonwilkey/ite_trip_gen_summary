"""Average-rate-vs-fitted-curve-equation selection logic.

Implements the decision criteria from the ITE Trip Generation Handbook,
3rd Edition, Chapter 3 ("Process for Selecting Average Rate or Equation",
Figure 4.2), as summarized in the TE-29 exam review presentation:

Use Fitted Curve Equation when:
  - a fitted curve equation is provided and the data plot has >= 20 points
  OR
  - a fitted curve equation is provided, R^2 >= 0.75, and the standard
    deviation is MORE than 55% of the average rate (i.e. the average rate
    is not a reliable weighted average).

Use Weighted Average Rate when:
  - the data plot has >= 3 points, AND
  - (R^2 < 0.75 or no equation is provided), AND
  - the standard deviation is 55% or less of the average rate.

Collect Local Data (use with caution) otherwise, e.g. fewer than 3 data
points, or a variable/unreliable average rate with no usable equation.

The "falls within data cluster" and "independent variable within range of
data" checks in the source flowchart require visually inspecting the data
plot and are not evaluated here -- they're assumed satisfied, matching the
simplification used by prior manual summaries of this table.
"""

from __future__ import annotations

LOCAL_DATA = "Local Data"
WEIGHTED_AVG = "Weighted Avg"
FITTED_CURVE = "Fitted Curve"
LINE_AT_CLUSTER = "Line at Cluster"

MIN_STUDIES_FOR_AVERAGE = 3
MIN_STUDIES_FOR_CURVE = 20
MIN_RSQ = 0.75
MAX_COEFFICIENT_OF_VARIATION = 0.55


def _is_low_variance(stdev: float | str, avg_rate: float | str) -> bool:
    """True if stdev is at most 55% of the average rate.

    Mirrors the reference spreadsheet's IFERROR(stdev/avg_rate, 1) <= 0.55:
    if either value isn't a usable number, treat the ratio as 1 (i.e. NOT
    low variance).
    """
    if not isinstance(stdev, (int, float)) or not isinstance(avg_rate, (int, float)):
        return False
    if avg_rate == 0:
        return False
    return (stdev / avg_rate) <= MAX_COEFFICIENT_OF_VARIATION


def recommend_method(
    n_studies: int,
    avg_rate: float | str,
    stdev: float | str,
    rsq: float | str,
    equation: str,
) -> str:
    """Return one of LOCAL_DATA, WEIGHTED_AVG, FITTED_CURVE, LINE_AT_CLUSTER."""
    if n_studies < MIN_STUDIES_FOR_AVERAGE:
        return LOCAL_DATA

    low_variance = _is_low_variance(stdev, avg_rate)
    equation_given = equation.strip().lower() != "not given"

    if not equation_given:
        return WEIGHTED_AVG if low_variance else LOCAL_DATA

    if n_studies >= MIN_STUDIES_FOR_CURVE:
        return FITTED_CURVE

    if isinstance(rsq, (int, float)) and rsq >= MIN_RSQ:
        return LINE_AT_CLUSTER if low_variance else FITTED_CURVE

    return WEIGHTED_AVG if low_variance else LOCAL_DATA
