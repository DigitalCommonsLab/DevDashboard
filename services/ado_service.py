from __future__ import annotations
import os
import time
from typing import Optional, Any

from logger import log_event

try:
    from azure.devops.connection import Connection
    from msrest.authentication import BasicAuthentication
    from azure.identity import ManagedIdentityCredential
except Exception:  # pragma: no cover
    Connection = None  # type: ignore
    BasicAuthentication = None  # type: ignore
    ManagedIdentityCredential = None  # type: ignore


class ADOService:
    """Service for interacting with Azure DevOps using MSI authentication."""

    def __init__(self, config: dict[str, Any]):
        self.org = config.get("organization")
        self.project = config.get("project")
        self.scope = "499b84ac-1321-427f-aa17-267ca6975798/.default"
        self.credential = ManagedIdentityCredential() if ManagedIdentityCredential else None
        self._token: Optional[str] = None
        self._token_expiry: float = 0
        self.max_retries = 3

    def _get_token(self) -> Optional[str]:
        if not self.credential:
            return os.getenv("ADO_PAT")
        if self._token and time.time() < self._token_expiry - 300:
            return self._token
        try:
            token = self.credential.get_token(self.scope)
            self._token = token.token
            self._token_expiry = token.expires_on
            return self._token
        except Exception as e:  # pragma: no cover
            log_event(
                "ado_auth_failure",
                resource_uri=self.org or "",
                error=str(e),
                retry="0",
            )
            return None

    def _connection(self) -> Optional[Connection]:
        if Connection is None:
            return None
        token = self._get_token()
        if not token:
            return None
        creds = BasicAuthentication("", token)
        return Connection(base_url=self.org, creds=creds)

    def _retry(self, func, *args, **kwargs):
        delay = 1
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:  # pragma: no cover
                log_event(
                    "ado_request_retry",
                    resource_uri=self.org or "",
                    error=str(e),
                    retry=str(attempt),
                )
                time.sleep(delay)
                delay *= 2
        return None

    def get_backlog_items(self, query_id: str) -> list[dict[str, Any]]:
        if Connection is None:
            return []
        conn = self._connection()
        if not conn:
            return []
        wit_client = conn.clients.get_work_item_tracking_client()
        result = self._retry(wit_client.query_by_id, query_id, project=self.project)
        if not result:
            return []
        items = []
        for item_ref in result.work_items:
            item = self._retry(wit_client.get_work_item, item_ref.id)
            if item:
                items.append(item.as_dict())
        return items
