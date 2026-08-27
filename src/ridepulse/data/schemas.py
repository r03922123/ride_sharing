"""pandera schemas that gate every stage of the data pipeline.

A schema failure stops the pipeline loudly (spec §10) rather than passing bad
rows downstream. Zone ids are constrained to the 263 real NYC taxi zones; the
lookup table also contains 264/265 ("Unknown") which cleaning drops.
"""

from __future__ import annotations

import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

ZONE_MIN, ZONE_MAX = 1, 263
MAX_DURATION_MIN = 180.0
MAX_TRIP_MILES = 100.0

_zone = Check.in_range(ZONE_MIN, ZONE_MAX)

RawYellowTripSchema = DataFrameSchema(
    {
        "tpep_pickup_datetime": Column("datetime64[ns]", coerce=True),
        "tpep_dropoff_datetime": Column("datetime64[ns]", coerce=True),
        "passenger_count": Column(float, nullable=True, coerce=True),
        "trip_distance": Column(float, coerce=True),
        "PULocationID": Column(int, coerce=True),
        "DOLocationID": Column(int, coerce=True),
    },
    strict=False,  # raw files carry many fare columns we do not use
    name="RawYellowTripSchema",
)

CleanedTripSchema = DataFrameSchema(
    {
        "pickup_ts": Column("datetime64[ns]", coerce=True),
        "dropoff_ts": Column("datetime64[ns]", coerce=True),
        "pu_location_id": Column(int, _zone, coerce=True),
        "do_location_id": Column(int, _zone, coerce=True),
        "trip_distance": Column(
            float, Check.in_range(0.0, MAX_TRIP_MILES, include_min=False), coerce=True
        ),
        "passenger_count": Column(
            "Int64", Check.ge(0), nullable=True, coerce=True
        ),
        "duration_min": Column(
            float,
            Check.in_range(0.0, MAX_DURATION_MIN, include_min=False),
            coerce=True,
        ),
    },
    strict=True,
    name="CleanedTripSchema",
)

DemandFeatureSchema = DataFrameSchema(
    {
        "zone_id": Column(int, _zone, coerce=True),
        "ts": Column("datetime64[ns]", coerce=True),
        "pickups": Column(int, Check.ge(0), coerce=True),
        "hour": Column(int, Check.in_range(0, 23), coerce=True),
        "dow": Column(int, Check.in_range(0, 6), coerce=True),
        "is_holiday": Column(bool, coerce=True),
        "lag_1h": Column(float, nullable=True, coerce=True),
        "lag_24h": Column(float, nullable=True, coerce=True),
        "lag_168h": Column(float, nullable=True, coerce=True),
        "roll_mean_24h": Column(float, nullable=True, coerce=True),
        "roll_mean_168h": Column(float, nullable=True, coerce=True),
    },
    strict=True,
    name="DemandFeatureSchema",
)

EtaFeatureSchema = DataFrameSchema(
    {
        "pickup_ts": Column("datetime64[ns]", coerce=True),
        "pu_location_id": Column(int, _zone, coerce=True),
        "do_location_id": Column(int, _zone, coerce=True),
        "hour": Column(int, Check.in_range(0, 23), coerce=True),
        "dow": Column(int, Check.in_range(0, 6), coerce=True),
        "trip_distance": Column(
            float, Check.in_range(0.0, MAX_TRIP_MILES, include_min=False), coerce=True
        ),
        "passenger_count": Column("Int64", Check.ge(0), nullable=True, coerce=True),
        "duration_min": Column(
            float,
            Check.in_range(0.0, MAX_DURATION_MIN, include_min=False),
            coerce=True,
        ),
        "split": Column(str, Check.isin(["train", "holdout"])),
    },
    strict=True,
    name="EtaFeatureSchema",
)

__all__ = [
    "CleanedTripSchema",
    "DemandFeatureSchema",
    "EtaFeatureSchema",
    "RawYellowTripSchema",
    "pa",
]
