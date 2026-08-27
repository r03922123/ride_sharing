from __future__ import annotations

from pathlib import Path

import typer

from ridepulse.data import pipeline
from ridepulse.data.repository import ParquetRepository
from ridepulse.data.schemas import DemandFeatureSchema, EtaFeatureSchema

app = typer.Typer(help="ride-pulse: ride-sharing demand intelligence CLI")

data_app = typer.Typer(help="Build and validate the data pipeline.")
sim_app = typer.Typer(help="Calibrate and run the simulation.")
forecast_app = typer.Typer(help="Train and backtest forecast models.")
serve_app = typer.Typer(help="Run the forecasting API.")

app.add_typer(data_app, name="data")
app.add_typer(sim_app, name="sim")
app.add_typer(forecast_app, name="forecast")
app.add_typer(serve_app, name="serve")

_MONTHS = typer.Option("2023-01..2023-02", help="Month or inclusive range YYYY-MM..YYYY-MM")
_MANIFEST = typer.Option(pipeline.DEFAULT_MANIFEST, help="Path to the download manifest")
_ROOT = typer.Option(Path("data"), help="Data root (raw/ and processed/ live here)")
_RAW_DIR = typer.Option(Path("data/raw"), help="Directory for downloaded source files")


@data_app.command()
def download(manifest: Path = _MANIFEST, raw_dir: Path = _RAW_DIR) -> None:
    """Fetch every manifest entry and print its verified SHA-256."""
    from ridepulse.data.download import computed_checksums

    paths = pipeline.download_sources(manifest, raw_dir)
    for name, digest in computed_checksums(paths).items():
        typer.echo(f"{name}: {digest}")


@data_app.command()
def clean(months: str = _MONTHS, raw_dir: Path = _RAW_DIR,
          root: Path = _ROOT) -> None:
    """Clean the given months into the cleaned_trips table."""
    out = pipeline.clean_months(pipeline.parse_months(months), raw_dir,
                                ParquetRepository(root))
    typer.echo(f"cleaned_trips -> {out}")


@data_app.command()
def features(root: Path = _ROOT) -> None:
    """Build demand + ETA feature tables from cleaned_trips."""
    demand, eta = pipeline.build_features(ParquetRepository(root))
    typer.echo(f"demand_features -> {demand}")
    typer.echo(f"eta_features -> {eta}")


@data_app.command()
def build(months: str = _MONTHS, manifest: Path = _MANIFEST,
          root: Path = _ROOT) -> None:
    """Run the full pipeline: download -> clean -> features."""
    pipeline.build_all(months, manifest, root)
    typer.echo("data build complete")


_PROFILE_OUT = typer.Option(
    Path("configs/sim/demand_profile.parquet"), help="Demand-profile artifact path"
)


_SIM_CONFIG = typer.Option(
    Path("configs/sim/baseline.yaml"), help="Scenario YAML"
)
_SIM_OUT = typer.Option(
    Path("reports/sim/baseline"), help="Output directory for event log + metrics"
)


@sim_app.command()
def calibrate(root: Path = _ROOT, out: Path = _PROFILE_OUT) -> None:
    """Calibrate the (zone x hour-of-week) demand profile from cleaned_trips."""
    from ridepulse.sim.core.demand import DemandProfile

    prof = DemandProfile.calibrate(ParquetRepository(root).path("cleaned_trips"))
    prof.save(out)
    typer.echo(f"demand profile -> {out}")


@sim_app.command()
def run(config: Path = _SIM_CONFIG, out: Path = _SIM_OUT) -> None:
    """Run a discrete-event scenario; write event_log.parquet + metrics.json."""
    from ridepulse.sim.des.runner import run_scenario

    metrics = run_scenario(config, out)
    typer.echo(f"sim run -> {out}")
    for k, v in metrics.items():
        typer.echo(f"  {k}: {v}")


@data_app.command()
def validate(root: Path = _ROOT) -> None:
    """Re-validate the processed feature tables against their schemas."""
    repo = ParquetRepository(root)
    DemandFeatureSchema.validate(repo.read("demand_features"), lazy=True)
    EtaFeatureSchema.validate(repo.read("eta_features"), lazy=True)
    typer.echo("processed tables are schema-valid")


if __name__ == "__main__":
    app()
