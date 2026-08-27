import typer

app = typer.Typer(help="ride-pulse: ride-sharing demand intelligence CLI")

data_app = typer.Typer(help="Build and validate the data pipeline.")
sim_app = typer.Typer(help="Calibrate and run the simulation.")
forecast_app = typer.Typer(help="Train and backtest forecast models.")
serve_app = typer.Typer(help="Run the forecasting API.")

app.add_typer(data_app, name="data")
app.add_typer(sim_app, name="sim")
app.add_typer(forecast_app, name="forecast")
app.add_typer(serve_app, name="serve")


if __name__ == "__main__":
    app()
