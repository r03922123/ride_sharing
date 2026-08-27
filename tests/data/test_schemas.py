import pandas as pd
import pytest
from pandera.errors import SchemaError, SchemaErrors

from ridepulse.data.schemas import (
    CleanedTripSchema,
    DemandFeatureSchema,
    EtaFeatureSchema,
    RawYellowTripSchema,
)

SCHEMA_FAIL = (SchemaError, SchemaErrors)


def _raw_row() -> dict[str, object]:
    return {
        "tpep_pickup_datetime": "2023-01-02 08:00:00",
        "tpep_dropoff_datetime": "2023-01-02 08:12:00",
        "passenger_count": 1.0,
        "trip_distance": 2.4,
        "PULocationID": 161,
        "DOLocationID": 230,
        "fare_amount": 12.5,  # extra column tolerated (strict=False)
    }


def _cleaned_row() -> dict[str, object]:
    return {
        "pickup_ts": "2023-01-02 08:00:00",
        "dropoff_ts": "2023-01-02 08:12:00",
        "pu_location_id": 161,
        "do_location_id": 230,
        "trip_distance": 2.4,
        "passenger_count": 1,
        "duration_min": 12.0,
    }


def _demand_row() -> dict[str, object]:
    return {
        "zone_id": 161,
        "ts": "2023-01-02 08:00:00",
        "pickups": 42,
        "hour": 8,
        "dow": 0,
        "is_holiday": False,
        "lag_1h": 40.0,
        "lag_24h": 38.0,
        "lag_168h": 41.0,
        "roll_mean_24h": 39.5,
        "roll_mean_168h": 40.1,
    }


def _eta_row() -> dict[str, object]:
    return {
        "pu_location_id": 161,
        "do_location_id": 230,
        "hour": 8,
        "dow": 0,
        "trip_distance": 2.4,
        "passenger_count": 1,
        "duration_min": 12.0,
    }


def test_raw_schema_accepts_good_and_rejects_bad_zone() -> None:
    RawYellowTripSchema.validate(pd.DataFrame([_raw_row()]))
    bad = _raw_row()
    bad["PULocationID"] = "not-an-int"
    with pytest.raises(SCHEMA_FAIL):
        RawYellowTripSchema.validate(pd.DataFrame([bad]))


def test_cleaned_schema_rejects_out_of_range_zone() -> None:
    CleanedTripSchema.validate(pd.DataFrame([_cleaned_row()]))
    bad = _cleaned_row()
    bad["pu_location_id"] = 300
    with pytest.raises(SCHEMA_FAIL):
        CleanedTripSchema.validate(pd.DataFrame([bad]))


def test_cleaned_schema_rejects_nonpositive_duration() -> None:
    bad = _cleaned_row()
    bad["duration_min"] = -1.0
    with pytest.raises(SCHEMA_FAIL):
        CleanedTripSchema.validate(pd.DataFrame([bad]))


def test_cleaned_schema_rejects_extra_columns() -> None:
    bad = _cleaned_row()
    bad["surprise"] = 1
    with pytest.raises(SCHEMA_FAIL):
        CleanedTripSchema.validate(pd.DataFrame([bad]))


def test_demand_schema_allows_null_lags_rejects_bad_hour() -> None:
    row = _demand_row()
    row["lag_168h"] = None
    DemandFeatureSchema.validate(pd.DataFrame([row]))
    bad = _demand_row()
    bad["hour"] = 24
    with pytest.raises(SCHEMA_FAIL):
        DemandFeatureSchema.validate(pd.DataFrame([bad]))


def test_eta_schema_rejects_zero_distance() -> None:
    EtaFeatureSchema.validate(pd.DataFrame([_eta_row()]))
    bad = _eta_row()
    bad["trip_distance"] = 0.0
    with pytest.raises(SCHEMA_FAIL):
        EtaFeatureSchema.validate(pd.DataFrame([bad]))
