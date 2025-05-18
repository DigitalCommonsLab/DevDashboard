from __future__ import annotations
import os
from typing import List
from flask import Flask, render_template_string, request

from tasks import TaskFetcher, Task

app = Flask(__name__)
fetcher = TaskFetcher()

TABLE_TEMPLATE = """
<!doctype html>
<title>Dev Dashboard</title>
<h1>Dev Dashboard</h1>
<form method='get'>
  Service Tree: <input name='service_tree' value='{{ service_tree }}'>
  <button type='submit'>Refresh</button>
</form>
<table border='1'>
  <tr><th>ID</th><th>Title</th><th>State</th><th>Source</th></tr>
  {% for t in tasks %}
  <tr><td>{{ t.id }}</td><td>{{ t.title }}</td><td>{{ t.state }}</td><td>{{ t.source }}</td></tr>
  {% endfor %}
</table>
"""

@app.route("/")
def index():
    service_tree = request.args.get("service_tree", "default")
    tasks: List[Task] = fetcher.fetch_all_tasks(service_tree)
    return render_template_string(TABLE_TEMPLATE, tasks=tasks, service_tree=service_tree)

if __name__ == "__main__":
    app.run(debug=True)
