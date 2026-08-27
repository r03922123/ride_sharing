"""Data pipeline: manifest-driven download, schema validation, cleaning, and
feature construction for the NYC TLC trip records.

What it does:  turns raw public TLC files into pandera-validated demand and ETA
               feature tables, reproducibly, from a checksummed manifest.
How to use it: ``ridepulse data build --months 2023-01..2023-02`` (or the
               ``download`` / ``validate`` / ``clean`` / ``features`` subcommands).
Depends on:    DuckDB (out-of-core SQL), pandas, pyarrow, pandera, PyYAML.
"""
