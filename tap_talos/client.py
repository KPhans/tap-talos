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
from singer_sdk.authenticators import Authenticator
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.pagination import BaseAPIPaginator
from singer_sdk.streams import RESTStream

if t.TYPE_CHECKING:
    from singer_sdk.helpers.types import Context

SCHEMAS_DIR = resources.files(__package__) / "schemas"


class TalosAuthenticator(Authenticator):
    """Custom HMAC authenticator for Talos."""

    def __init__(self, stream: RESTStream) -> None:
        super().__init__(stream)
        self.api_key = self.config.get("api_key")
        self.api_secret = self.config.get("api_secret")
        self.host = self.config.get("api_host")

    def update_request_headers(self, request: requests.PreparedRequest) -> None:
        """Add authentication headers to request."""
        utc_now = datetime.datetime.utcnow()
        utc_datetime = utc_now.strftime("%Y-%m-%dT%H:%M:%S.000000Z")

        method = request.method
        path = request.path_url.split('?')[0]

        params = [
            method,
            utc_datetime,
            self.host,
            path,
        ]

        # Important: handle query params or body if necessary later
        payload = "\n".join(params)
        hashvalue = hmac.new(
            self.api_secret.encode('ascii'), payload.encode('ascii'), hashlib.sha256
        )
        signature = base64.urlsafe_b64encode(hashvalue.digest()).decode()

        request.headers.update({
            "TALOS-KEY": self.api_key,
            "TALOS-SIGN": signature,
            "TALOS-TS": utc_datetime,
        })


class TalosStream(RESTStream):
    """Base stream class for Talos."""

    records_jsonpath = "$.data[*]"  # because the Talos API wraps in {"data": [...]}

    @property
    def url_base(self) -> str:
        return f"https://{self.config.get('api_host')}"

    @property
    def authenticator(self) -> TalosAuthenticator:
        return TalosAuthenticator(self)

    def get_new_paginator(self) -> BaseAPIPaginator:
        """Talos endpoints don't paginate, so no paginator needed."""
        return None

    def get_url_params(
        self,
        context: Context | None,
        next_page_token: t.Any | None,
    ) -> dict[str, t.Any]:
        """No URL params needed for balances."""
        return {}

    def prepare_request_payload(
        self,
        context: Context | None,
        next_page_token: t.Any | None,
    ) -> dict | None:
        """No payload for GET."""
        return None

    def parse_response(self, response: requests.Response) -> t.Iterable[dict]:
        """Parse the response and yield records."""
        yield from extract_jsonpath(
            self.records_jsonpath,
            input=response.json(parse_float=decimal.Decimal),
        )

    def post_process(
        self,
        row: dict,
        context: Context | None = None,
    ) -> dict | None:
        """Optionally modify records."""
        return row
