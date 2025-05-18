from __future__ import annotations
import os
from dataclasses import dataclass
from typing import List

import requests

try:
    from azure.devops.connection import Connection
    from msrest.authentication import BasicAuthentication
except Exception:  # pragma: no cover - azure-devops may not be installed in CI
    Connection = None  # type: ignore
    BasicAuthentication = None  # type: ignore

try:
    from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
except Exception:  # pragma: no cover - azure-kusto-data may not be installed
    KustoClient = None  # type: ignore
    KustoConnectionStringBuilder = None  # type: ignore

import yaml

@dataclass
class Task:
    id: str
    title: str
    state: str
    source: str


class TaskFetcher:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def _get_ado_tasks(self) -> List[Task]:
        cfg = self.config.get("ado", {})
        token = os.getenv(cfg.get("token_env", ""))
        if not token or Connection is None:
            return []

        credentials = BasicAuthentication("", token)
        connection = Connection(base_url=cfg["organization"], creds=credentials)
        wit_client = connection.clients.get_work_item_tracking_client()
        query_id = cfg.get("backlog_query_id")
        if not query_id:
            return []
        query_result = wit_client.query_by_id(query_id, project=cfg["project"])  # type: ignore
        tasks: List[Task] = []
        for item in query_result.work_items:
            work_item = wit_client.get_work_item(item.id)  # type: ignore
            tasks.append(
                Task(
                    id=str(work_item.id),
                    title=work_item.fields.get("System.Title", ""),
                    state=work_item.fields.get("System.State", ""),
                    source="ADO",
                )
            )
        return tasks

    def _query_kusto(self, query: str, service_tree: str) -> List[Task]:
        kusto_cfg = self.config.get("kusto", {})
        if KustoClient is None:
            return []
        query = query.format(service_tree=service_tree)
        cluster = kusto_cfg.get("cluster")
        db = kusto_cfg.get("database")
        kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
            cluster,
            os.getenv(kusto_cfg.get("client_id_env", ""), ""),
            os.getenv(kusto_cfg.get("client_secret_env", ""), ""),
            os.getenv(kusto_cfg.get("tenant_id_env", ""), ""),
        )
        client = KustoClient(kcsb)
        response = client.execute(db, query)
        tasks: List[Task] = []
        for row in response.primary_results[0]:
            tasks.append(
                Task(
                    id=str(row["Id"]),
                    title=row.get("Title", ""),
                    state=row.get("State", ""),
                    source=row.get("Source", "Kusto"),
                )
            )
        return tasks

    def _get_icm_tasks(self, service_tree: str) -> List[Task]:
        query = self.config.get("kusto", {}).get("icm_query", "")
        return self._query_kusto(query, service_tree)

    def _get_s360_tasks(self, service_tree: str) -> List[Task]:
        query = self.config.get("kusto", {}).get("s360_query", "")
        return self._query_kusto(query, service_tree)

    def fetch_all_tasks(self, service_tree: str) -> List[Task]:
        tasks = []
        tasks.extend(self._get_ado_tasks())
        tasks.extend(self._get_icm_tasks(service_tree))
        tasks.extend(self._get_s360_tasks(service_tree))
        return tasks
