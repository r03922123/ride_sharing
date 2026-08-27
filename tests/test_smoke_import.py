from typer.testing import CliRunner

import ridepulse
from ridepulse.cli import app

runner = CliRunner()


def test_import_resolves() -> None:
    assert ridepulse.__version__


def test_cli_app_resolves() -> None:
    assert app is not None


def test_cli_help_exits_zero() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for sub_app in ("data", "sim", "forecast", "serve"):
        assert sub_app in result.output
