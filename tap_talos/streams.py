"""Stream type classes for tap-talos."""

from __future__ import annotations

import typing as t
from importlib import resources

from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_talos.client import TalosStream

# TODO: Delete this if not using json files for schema definition
SCHEMAS_DIR = resources.files(__package__) / "schemas"


class BalancesStream(TalosStream):
    name = "balances"
    path = "/v1/balances"
    primary_keys: t.ClassVar[list[str]] = ["Market", "Currency", "Account"]
    replication_key = "LastUpdateTime"
    schema_filepath = SCHEMAS_DIR / "balances.json"

    @property
    def replication_method(self) -> str:
        return "INCREMENTAL"
