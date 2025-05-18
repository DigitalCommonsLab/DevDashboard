from __future__ import annotations
import os
import time
from typing import Optional, Any, List

from logger import log_event

try:
    from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
    from azure.identity import ManagedIdentityCredential
except Exception:  # pragma: no cover
    KustoClient = None  # type: ignore
    KustoConnectionStringBuilder = None  # type: ignore
    ManagedIdentityCredential = None  # type: ignore


class KustoService:
    """Service for querying Kusto using MSI authentication."""

    def __init__(self, config: dict[str, Any]):
        self.cluster = config.get("cluster")
        self.database = config.get("database")
        self.credential = ManagedIdentityCredential() if ManagedIdentityCredential else None
        self.scope = f"{self.cluster}/.default" if self.cluster else ""
        self._token: Optional[str] = None
        self._token_expiry: float = 0
        self.max_retries = 3

    def _get_client(self) -> Optional[KustoClient]:
        if KustoClient is None or not self.cluster or not self.database:
            return None
        if self.credential:
            if not self._token or time.time() >= self._token_expiry - 300:
                try:
                    token = self.credential.get_token(self.scope)
                    self._token = token.token
                    self._token_expiry = token.expires_on
                except Exception as e:  # pragma: no cover
                    log_event(
                        "kusto_auth_failure",
                        resource_uri=self.cluster,
                        error=str(e),
                        retry="0",
                    )
                    return None
            kcsb = KustoConnectionStringBuilder.with_aad_managed_service_identity_authentication(
                self.cluster, client_id=None
            )
        else:
            kcsb = KustoConnectionStringBuilder.with_aad_device_authentication(self.cluster)
        return KustoClient(kcsb)

    def query(self, query: str) -> List[dict[str, Any]]:
        client = self._get_client()
        if not client:
            return []
        delay = 1
        for attempt in range(1, self.max_retries + 1):
            try:
                response = client.execute(self.database, query)
                rows = response.primary_results[0]
                return [row.to_dict() for row in rows]
            except Exception as e:  # pragma: no cover
                log_event(
                    "kusto_query_retry",
                    resource_uri=self.cluster,
                    error=str(e),
                    retry=str(attempt),
                )
                time.sleep(delay)
                delay *= 2
        return []
