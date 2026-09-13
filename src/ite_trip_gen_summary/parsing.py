"""Extract trip-generation data rows from the ITE Trip Generation Manual PDF.

Each "data sheet" page in the manual (one land use x dependent variable x
time period x setting combination) is parsed into a single ``Row``. Pages
that only contain a land use description (no data table) are skipped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pymupdf

# Lines that can appear before the real page content because of how the
# manual's running header/footer gets interleaved with the body text when
# extracted in reading order. These are stripped from the start of a page's
# text before the main record pattern is applied.
_LEADING_NOISE_LINE_RE = re.compile(
    r"^("
    r"\d+\s*"  # a bare page number
    r"|Trip Generation Manual,.*Volume\s+\d+"  # even-page running footer
    r"|.+\(Land Uses [\d\u2013-]+\)"  # odd-page category footer
    r"|\s*"  # blank line
    r")$"
)

# One data page, in the order fields appear on the page. Every anchor
# ("On a:", "Setting/Location:", etc.) is literal text printed by the
# manual, so this is robust to the variable-length free text between
# anchors (multi-line time periods, wrapped equations, etc.).
_RECORD_RE = re.compile(
    r"^(?P<header>.+?)\n"
    r"(?P<dep_var>[^\n]+?)\s+vs:\n"
    r"(?P<indep_var>.+?)\n"
    r"On a:\n"
    r"(?P<time>.+?)\n"
    r"Setting/Location:\n"
    r"(?P<setting>.+?)\n"
    r"Number of Studies:\n"
    r"(?P<n_studies>\d+)\n"
    r"(?P<avg_iv_label>.+?):\n"
    r"(?P<avg_iv_value>.+?)\n"
    r"Directional Distribution:\n"
    r"(?P<dir_dist>.+?)\n"
    r".+?\n"
    r"Average Rate\nRange of Rates\nStandard Deviation\n"
    r"(?P<avg_rate>.+?)\n"
    r"(?P<range>.+?)\n"
    r"(?P<stdev>.+?)\n"
    r"Data Plot and Equation\n"
    r"(?P<plot_area>.*?)"
    r"Fitted Curve Equation:\s*(?P<equation>.+?)\n"
    r"R\u00b2\s*=\s*(?P<rsq>.+?)\n",
    re.DOTALL,
)

_CODE_RE = re.compile(r"\((\d+)\)")
_VOLUME_RE = re.compile(r"Volume\s+(\d+)")


@dataclass
class Row:
    pdf_page: int
    volume: str
    code: int
    land_use_name: str
    setting: str
    dependent_variable: str
    independent_variable: str
    time_period: str
    n_studies: int
    avg_iv: float | str
    dir_dist: str
    avg_rate: float | str
    range_of_rates: str
    stdev: float | str
    rsq: float | str
    equation: str
    caution: str


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _to_number(text: str) -> float | str:
    text = text.strip()
    try:
        value = float(text.replace(",", ""))
    except ValueError:
        return text
    return int(value) if value.is_integer() else value


def _strip_leading_noise(text: str) -> str:
    lines = text.split("\n")
    idx = 0
    while idx < len(lines) and _LEADING_NOISE_LINE_RE.match(lines[idx]):
        idx += 1
    return "\n".join(lines[idx:])


def _split_name_and_code(header: str) -> tuple[str, int]:
    matches = list(_CODE_RE.finditer(header))
    if not matches:
        raise ValueError(f"no land use code found in header: {header!r}")
    last = matches[-1]
    name = header[: last.start()] + header[last.end() :]
    return _clean(name), int(last.group(1))


def _normalize_dir_dist(text: str) -> str:
    text = _clean(text)
    return text.replace("entering", "in").replace("exiting", "out")


def _normalize_range(text: str) -> str:
    return re.sub(r"\s*-\s*", "-", _clean(text))


def _extract_caution(plot_area: str) -> str:
    match = re.search(r"Caution\s*[\u2013-]\s*([^\n]+)", plot_area)
    return match.group(1).strip() if match else ""


def parse_page(raw_text: str, pdf_page: int, volume: str) -> Row | None:
    """Parse one PDF page's extracted text into a Row, or None if the page
    is not a data sheet (e.g. a land use description page)."""
    if "Number of Studies:" not in raw_text:
        return None

    text = _strip_leading_noise(raw_text)
    match = _RECORD_RE.match(text)
    if match is None:
        raise ValueError(f"failed to parse data page {pdf_page}")
    fields = match.groupdict()

    name, code = _split_name_and_code(fields["header"])

    return Row(
        pdf_page=pdf_page,
        volume=volume,
        code=code,
        land_use_name=name,
        setting=_clean(fields["setting"]),
        dependent_variable=_clean(fields["dep_var"]),
        independent_variable=_clean(fields["indep_var"]),
        time_period=_clean(fields["time"]),
        n_studies=int(fields["n_studies"]),
        avg_iv=_to_number(fields["avg_iv_value"]),
        dir_dist=_normalize_dir_dist(fields["dir_dist"]),
        avg_rate=_to_number(fields["avg_rate"]),
        range_of_rates=_normalize_range(fields["range"]),
        stdev=_to_number(fields["stdev"]),
        rsq=_to_number(fields["rsq"]),
        equation=_clean(fields["equation"]),
        caution=_extract_caution(fields["plot_area"]),
    )


def iter_rows(pdf_path: str, progress=None, on_error=None):
    """Yield a Row for every data-sheet page in the PDF, in page order.

    progress: optional callable invoked with (pages_done, pages_total) after
    each page is processed.
    on_error: optional callable invoked with (pdf_page, exception) when a
    page looks like a data sheet but doesn't match the expected layout;
    that page is skipped rather than aborting the whole run.
    """
    doc = pymupdf.open(pdf_path)
    total = doc.page_count
    current_volume = ""
    try:
        for i in range(total):
            page_text = doc[i].get_text()
            volume_match = _VOLUME_RE.search(page_text)
            if volume_match:
                current_volume = f"Volume {volume_match.group(1)}"
            try:
                row = parse_page(page_text, pdf_page=i + 1, volume=current_volume)
            except ValueError as exc:
                if on_error is not None:
                    on_error(i + 1, exc)
                row = None
            if row is not None:
                yield row
            if progress is not None:
                progress(i + 1, total)
    finally:
        doc.close()
