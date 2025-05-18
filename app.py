from __future__ import annotations
from typing import List
from flask import Flask, render_template, request

from tasks import TaskFetcher, Task

app = Flask(__name__)
fetcher = TaskFetcher()

query_history: list[dict[str, str]] = []


def _calculate_metrics(tasks: List[Task]) -> dict[str, int]:
    return {
        "open_issues": sum(1 for t in tasks if t.source == "ADO" and t.state != "Closed"),
        "alerts": sum(1 for t in tasks if t.source != "ADO"),
        "kusto_queries": len(query_history),
        "ado_projects": 1,
    }


@app.route("/")
def index():
    service_tree = request.args.get("service_tree", "default")
    tasks: List[Task] = fetcher.fetch_all_tasks(service_tree)
    metrics = _calculate_metrics(tasks)
    chart_labels = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    chart_issue_counts = [1, 2, 3, 2, 4]
    chart_alert_counts = [0, 1, 0, 2, 1]
    return render_template(
        "index.html",
        tasks=tasks,
        service_tree=service_tree,
        metrics=metrics,
        chart={"labels": chart_labels, "issue_counts": chart_issue_counts, "alert_counts": chart_alert_counts},
        query_history=query_history,
    )


if __name__ == "__main__":
    app.run(debug=True)
