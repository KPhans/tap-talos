"""REST client handling, including TalosStream base class."""

from __future__ import annotations

import datetime
import decimal
import typing as t
import hmac
import hashlib
import base64
from importlib import resources

import requests
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.pagination import BaseAPIPaginator  # noqa: TC002
from singer_sdk.streams import RESTStream

if t.TYPE_CHECKING:
    from singer_sdk.helpers.types import Context

# TODO: Delete this if not using json files for schema definition
SCHEMAS_DIR = resources.files(__package__) / "schemas"


class TalosStream(RESTStream):
    """Talos stream class."""

    records_jsonpath = "$.data[*]"
    next_page_token_jsonpath = "$.next_page"  # noqa: S105

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return f"https://{self.config.get('api_host')}"

    @property
    def use_pagination(self) -> bool:
        """Return False because the endpoint is not paginated."""
        return False

    @property
    def http_headers(self) -> dict:
        """Return the HTTP headers needed.

        Returns:
            A dictionary of HTTP headers.
        """
        utc_now = datetime.datetime.utcnow()
        utc_datetime = utc_now.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
        host = self.config.get("api_host")
        api_key = self.config.get("api_key")
        api_secret = self.config.get("api_secret")
        path = self.path

        method = "GET"

        payload = "\n".join([
            method,
            utc_datetime,
            host,
            path,
        ])

        signature = base64.urlsafe_b64encode(
            hmac.new(api_secret.encode('ascii'), payload.encode('ascii'), hashlib.sha256).digest()
        ).decode()

        headers = {
            "TALOS-KEY": api_key,
            "TALOS-SIGN": signature,
            "TALOS-TS": utc_datetime,
        }

        return headers

    def get_new_paginator(self) -> BaseAPIPaginator:
        """Create a new pagination helper instance.

        Talos balances endpoint does not paginate.

        Returns:
            None
        """
        return None

    def request_records(self, context: dict | None) -> t.Iterator[dict]:
        """Override request_records to NOT use paginator."""
        self.logger.info("DEBUG: Sending request without pagination")

        url = f"{self.url_base}{self.path}"
        headers = self.http_headers

        response = requests.get(url, headers=headers)

        if not response.ok:
            raise RuntimeError(f"Error fetching data: {response.status_code} - {response.text}")

        yield from self.parse_response(response)

    def get_url_params(
        self,
        context: Context | None,  # noqa: ARG002
        next_page_token: t.Any | None,  # noqa: ANN401
    ) -> dict[str, t.Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        return {}

    def prepare_request_payload(
        self,
        context: Context | None,  # noqa: ARG002
        next_page_token: t.Any | None,  # noqa: ARG002, ANN401
    ) -> dict | None:
        """Prepare the data payload for the REST API request."""
        return None

    def parse_response(self, response: requests.Response) -> t.Iterator[dict]:
        """Parse the response and yield Singer RECORD messages."""

        raw_records = extract_jsonpath(
            self.records_jsonpath,
            input=response.json(parse_float=decimal.Decimal),
        )

        count = 0
        for record in raw_records:
            record = self.post_process(record)
            self.logger.debug(f"Parsed record: {record}")
            yield record
            count += 1

        self.logger.info(f"DEBUG: Emitted {count} records")
        return iter(())
