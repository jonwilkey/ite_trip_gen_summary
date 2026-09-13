from __future__ import annotations

from pathlib import Path

import click

from .parsing import iter_rows
from .workbook import build_workbook


@click.command()
@click.argument("pdf_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output .xlsx path (default: <pdf name>_summary.xlsx next to the PDF).",
)
def main(pdf_path: Path, output_path: Path | None) -> None:
    """Scrape PDF_PATH into a trip generation summary spreadsheet.

    Reads the ITE Trip Generation Manual PDF at PDF_PATH, extracts every
    land use data table into one row, computes whether the average rate or
    the fitted curve equation is the recommended method for that row per
    the ITE Trip Generation Handbook criteria, and writes an .xlsx summary
    with the recommended column highlighted.
    """
    if output_path is None:
        output_path = pdf_path.with_name(f"{pdf_path.stem}_summary.xlsx")

    errors: list[tuple[int, Exception]] = []

    def on_error(page: int, exc: Exception) -> None:
        errors.append((page, exc))

    click.echo(f"Reading {pdf_path} ...")
    with click.progressbar(length=1, label="Scanning pages") as bar:
        def progress(done: int, total: int) -> None:
            if bar.length != total:
                bar.length = total
            bar.update(done - bar.pos)

        rows = list(iter_rows(str(pdf_path), progress=progress, on_error=on_error))

    click.echo(f"Parsed {len(rows)} data rows.")
    if errors:
        click.echo(
            click.style(
                f"Warning: {len(errors)} page(s) looked like data sheets but "
                "could not be parsed and were skipped:",
                fg="yellow",
            )
        )
        for page, exc in errors[:20]:
            click.echo(f"  page {page}: {exc}")
        if len(errors) > 20:
            click.echo(f"  ... and {len(errors) - 20} more")

    click.echo("Building workbook ...")
    wb = build_workbook(rows)
    wb.save(output_path)
    click.echo(f"Wrote {output_path}")
