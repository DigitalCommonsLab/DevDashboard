from __future__ import annotations
import os
import random
from dataclasses import dataclass
from typing import List

import yaml

from services.ado_service import ADOService
from services.kusto_service import KustoService


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
        self.dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
        self.ado = ADOService(self.config.get("ado", {}))
        self.kusto = KustoService(self.config.get("kusto", {}))

    def _mock_tasks(self) -> List[Task]:
        states = ["New", "Active", "Resolved"]
        sources = ["ADO", "IcM", "S360"]
        tasks = []
        for i in range(5):
            tasks.append(Task(str(i), f"Mock Task {i}", random.choice(states), random.choice(sources)))
        return tasks

    def _get_ado_tasks(self) -> List[Task]:
        cfg = self.config.get("ado", {})
        query_id = cfg.get("backlog_query_id")
        items = self.ado.get_backlog_items(query_id) if query_id else []
        tasks: List[Task] = []
        for item in items:
            fields = item.get("fields", {})
            tasks.append(
                Task(
                    id=str(item.get("id")),
                    title=fields.get("System.Title", ""),
                    state=fields.get("System.State", ""),
                    source="ADO",
                )
            )
        return tasks

    def _query_kusto(self, query: str, service_tree: str) -> List[Task]:
        rows = self.kusto.query(query.format(service_tree=service_tree))
        tasks: List[Task] = []
        for row in rows:
            tasks.append(
                Task(
                    id=str(row.get("Id")),
                    title=row.get("Title", ""),
                    state=row.get("State", ""),
                    source=row.get("Source", "Kusto"),
                )
            )
        return tasks

    def _get_icm_tasks(self, service_tree: str) -> List[Task]:
        query = self.config.get("kusto", {}).get("icm_query", "")
        return self._query_kusto(query, service_tree) if query else []

    def _get_s360_tasks(self, service_tree: str) -> List[Task]:
        query = self.config.get("kusto", {}).get("s360_query", "")
        return self._query_kusto(query, service_tree) if query else []

    def fetch_all_tasks(self, service_tree: str) -> List[Task]:
        if self.dev_mode:
            return self._mock_tasks()
        tasks = []
        tasks.extend(self._get_ado_tasks())
        tasks.extend(self._get_icm_tasks(service_tree))
        tasks.extend(self._get_s360_tasks(service_tree))
        return tasks
