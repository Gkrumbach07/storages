#!/usr/bin/env python3
# thoth-storages
# Copyright(C) 2018, 2019, 2020 Fridolin Pokorny
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Adapter for storing analysis results onto a persistence remote store."""

import os
import typing
from datetime import date
from datetime import timedelta

from .base import StorageBase
from .ceph import CephStore
from .result_schema import RESULT_SCHEMA
from .exceptions import SchemaError
from .exceptions import NoDocumentIdError


class ResultStorageBase(StorageBase):
    """Adapter base for storing results."""

    # Type of results to distinguish them based on prefix on Ceph.
    RESULT_TYPE = ""
    # Use core analyzers schema as default one, derived classes can adjust this.
    SCHEMA = RESULT_SCHEMA

    def __init__(
        self,
        deployment_name=None,
        *,
        host: str = None,
        key_id: str = None,
        secret_key: str = None,
        bucket: str = None,
        region: str = None,
        prefix: str = None,
    ):
        """Initialize result storage database.

        The adapter can take arguments from env variables if not provided
        explicitly.
        """
        assert (
            self.RESULT_TYPE
        ), "Make sure RESULT_TYPE in derived classes to distinguish between adapter type instances is non-empty."

        self.deployment_name = deployment_name or os.environ["THOTH_DEPLOYMENT_NAME"]
        self.prefix = "{}/{}/{}".format(
            prefix or os.environ["THOTH_CEPH_BUCKET_PREFIX"], self.deployment_name, self.RESULT_TYPE
        )
        self.ceph = CephStore(
            self.prefix, host=host, key_id=key_id, secret_key=secret_key, bucket=bucket, region=region
        )

    @classmethod
    def get_document_id(cls, document: dict) -> str:
        """Get document id under which the given document should be stored."""
        # We use hostname that matches pod id generated by OpenShift as a base.
        # Note we need to return job id here - the last part delimited by dash
        # is used for specifying pod that runs for the given job. We need job
        # id to be returned (remove pod specific part).
        document_id = document["metadata"].get("document_id")
        if not document_id:
            raise NoDocumentIdError("No document id is present in metadata")

        return document_id

    def is_connected(self) -> bool:
        """Check if the given database adapter is in connected state."""
        return self.ceph.is_connected()

    def connect(self) -> None:
        """Connect the given storage adapter."""
        self.ceph.connect()

    def _iter_dates_prefix_addition(
        self, start_date: date, end_date: typing.Optional[date] = None
    ) -> typing.Generator[str, None, None]:
        """Create prefix based on dates supplied."""
        if end_date is None:
            end_date = date.today() + timedelta(days=1)  # Today inclusively.
        elif end_date < start_date:
            raise ValueError("end_date cannot precede start_date")

        walker = start_date
        step = timedelta(days=1)
        while walker < end_date:
            yield walker.strftime(f"{self.RESULT_TYPE}-%y%m%d")
            walker += step

    def get_document_listing(
        self, *, start_date: typing.Optional[date] = None, end_date: typing.Optional[date] = None
    ) -> typing.Generator[str, None, None]:
        """Get listing of documents available in Ceph as a generator.

        Additional parameters can filter results. If start_date is supplied
        and no end_date is supplied explicitly, the current date is
        considered as end_date (inclusively).
        """
        if start_date:
            for prefix_addition in self._iter_dates_prefix_addition(start_date=start_date, end_date=end_date):
                for document_id in self.ceph.get_document_listing(prefix_addition):
                    if not document_id.endswith(".request"):
                        yield document_id
        else:
            for document_id in self.ceph.get_document_listing():
                # Filter out stored requests.
                if not document_id.endswith(".request"):
                    yield document_id

    def get_document_count(
        self, *, start_date: typing.Optional[date] = None, end_date: typing.Optional[date] = None
    ) -> int:
        """Get number of documents present."""
        return sum(1 for _ in self.get_document_listing(start_date=start_date, end_date=end_date))

    def store_document(self, document: dict) -> str:
        """Store the given document in Ceph."""
        if self.SCHEMA:
            try:
                self.SCHEMA(document)
            except Exception as exc:
                raise SchemaError("Failed to validate document schema") from exc

        document_id = self.get_document_id(document)
        self.ceph.store_document(document, document_id)
        return document_id

    def store_request(self, document_id: str, request: typing.Dict[str, typing.Any]) -> str:
        """Store the given request.

        This function stores a request document for user request traceability.
        """
        document_id = f"{document_id}.request"
        self.ceph.store_document(request, document_id)
        return document_id

    def retrieve_request(self, document_id: str) -> typing.Dict[str, typing.Any]:
        """Retrieve document capturing requests."""
        return self.ceph.retrieve_document(f"{document_id}.request")

    def request_exists(self, document_id: str) -> bool:
        """Check if a request exists for the given document id."""
        return self.ceph.document_exists(f"{document_id}.request")

    def store_file(self, file_path: str, file_id: str) -> str:
        """Store the given file in Ceph."""
        self.ceph.store_file(file_path, file_id)
        return file_id

    def retrieve_document(self, document_id: str) -> dict:
        """Retrieve a document from Ceph by its id."""
        return self.ceph.retrieve_document(document_id)

    def iterate_results(
        self, *, start_date: typing.Optional[date] = None, end_date: typing.Optional[date] = None
    ) -> typing.Generator[tuple, None, None]:
        """Iterate over results available in the Ceph.

        Additional parameters can filter results. If start_date is supplied
        and no end_date is supplied explicitly, the current date is
        considered as end_date (inclusively).
        """
        if start_date:
            for prefix_addition in self._iter_dates_prefix_addition(start_date=start_date, end_date=end_date):
                yield from self.ceph.iterate_results(prefix_addition)
        else:
            yield from self.ceph.iterate_results()

    def document_exists(self, document_id: str) -> bool:
        """Check if the there is an object with the given key in bucket."""
        return self.ceph.document_exists(document_id)
