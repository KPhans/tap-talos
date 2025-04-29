"""Talos tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_talos.streams import BalancesStream


class Taptalos(Tap):
    """Talos tap class."""

    name = "tap-talos"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_key",
            th.StringType,
            required=True,
            secret=True,
            title="API Key",
            description="The API key to authenticate against the Talos API",
        ),
        th.Property(
            "api_secret",
            th.StringType,
            required=True,
            secret=True,
            title="API Secret",
            description="The API secret to sign Talos requests",
        ),
        th.Property(
            "api_host",
            th.StringType,
            required=True,
            title="API Host",
            description="The Talos API hostname (e.g., tal-295.sandbox.talostrading.com)",
        ),
    ).to_dict()

    def discover_streams(self) -> list:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [
            BalancesStream(self),
        ]


if __name__ == "__main__":
    Taptalos.cli()
