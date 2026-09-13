# ITE Trip Generation Summary

Scrapes the ITE *Trip Generation Manual, 12th Edition* PDF into a single
summary spreadsheet (`.xlsx`), one row per land use / dependent variable /
time period / setting data table in the manual.

For each row, the script also applies the selection criteria from the ITE
*Trip Generation Handbook*, 3rd Edition, Chapter 3 ("Average Rate vs.
Fitted Curve Equation") to recommend whether to use the **average rate**
or the **fitted curve equation**, and highlights the recommended column
green so it's obvious at a glance which value to use for a given land use.

> **Note:** The Trip Generation Manual is copyrighted material licensed by
> ITE. This repository does not include the PDF — you need your own
> licensed copy to run the script.

## What you get

An `.xlsx` workbook with two sheets:

- **Trip Generation Data** — one row per data table in the manual: land
  use code/name, setting, dependent/independent variable, time period,
  number of studies, average rate, range, standard deviation, R², fitted
  curve equation, and a `Recommended Method` column (`Weighted Avg`,
  `Fitted Curve`, `Line at Cluster`, or `Local Data`). The `Average Rate`
  or `Fitted Curve Equation` column is highlighted green depending on the
  recommendation.
- **Land Use Index** — a quick lookup of every land use code and name
  found in the manual.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (manages the Python install and all
  dependencies for you — no manual `pip install` needed)

### Install Python and uv

**Windows (PowerShell):**

```powershell
winget install --id Astral-SH.Uv -e
```

If you don't already have Python 3.12+, uv will download it automatically
the first time you run the script — no separate Python install needed.

**macOS:**

```bash
brew install uv
```

(or, without Homebrew: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

**Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your terminal (or follow the on-screen instructions to add
`uv` to your `PATH`).

## Usage

1. Clone this repository and `cd` into it.
2. Run the script, pointing it at your copy of the Trip Generation Manual
   PDF:

   ```bash
   uv run ite-trip-gen-summary /path/to/ite_trip_gen.pdf
   ```

   The first run will automatically create a virtual environment and
   install all dependencies — nothing else to set up.

   This writes `ite_trip_gen_summary.xlsx` next to the PDF by default.
   Scraping the full manual (~3,300 pages) takes well under a minute.

3. To choose a different output location:

   ```bash
   uv run ite-trip-gen-summary /path/to/ite_trip_gen.pdf -o my_summary.xlsx
   ```

Run `uv run ite-trip-gen-summary --help` for all options.

## How the average-vs-equation recommendation works

Per the ITE Trip Generation Handbook selection criteria:

- **Use the fitted curve equation** when it's provided and the data plot
  has 20+ data points, OR it has R² ≥ 0.75 and the standard deviation is
  *more* than 55% of the average rate.
- **Use the weighted average rate** when there are at least 3 data points,
  the equation isn't provided (or its R² is below 0.75), and the standard
  deviation is *at most* 55% of the average rate.
- **Collect local data** otherwise (e.g. fewer than 3 studies, or a highly
  variable average rate with no usable equation).

The manual's flowchart also asks whether the fitted curve/average falls
within the data cluster on the plot, which requires visually inspecting
the plot and isn't evaluated by this script — the recommendation assumes
that check passes, consistent with how this table has previously been
summarized by hand.

See `src/ite_trip_gen_summary/recommend.py` for the exact logic.

## Development

Source layout:

- `src/ite_trip_gen_summary/parsing.py` — extracts and parses each PDF
  data page into a row.
- `src/ite_trip_gen_summary/recommend.py` — average-vs-equation decision
  logic.
- `src/ite_trip_gen_summary/workbook.py` — builds the `.xlsx` output.
- `src/ite_trip_gen_summary/cli.py` — command-line interface.

To add or update dependencies: `uv add <package>`.
