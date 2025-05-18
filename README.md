# DevDashboard

This repository provides a simple dashboard web application that aggregates tasks from multiple sources like Azure DevOps backlogs and Kusto queries for IcMs or S360 items. The goal is to visualize upcoming work and track progress as items move from triage to development and completion.

## Requirements

- Python 3.11+
- `Flask` for the web server
- `azure-kusto-data` for running Kusto queries
- `azure-devops` for interacting with Azure DevOps REST APIs

These packages are not included in this repository and must be installed separately:

```bash
pip install flask azure-kusto-data azure-devops
```

## Usage

1. Edit `config.yaml` to provide connection information for your Azure DevOps organization, backlog, and Kusto cluster.
2. Run the application:

```bash
python3 app.py
```

Then open `http://localhost:5000/` in your browser to view the dashboard.

## Notes

- The current implementation focuses on reading existing tasks. Automating task creation is planned for the future.
- Authentication details (such as tokens) should be stored securely. This sample expects environment variables for secrets.
