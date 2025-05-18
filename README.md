# DevDashboard

This project shows a simple developer dashboard that aggregates tasks from Azure DevOps and Kusto queries. It now includes a modern UI using Tailwind CSS and supports dark mode.

## Requirements

- Python 3.11+
- `Flask` for the web server
- `azure-kusto-data`, `azure-devops`, and `azure-identity` for Azure connectivity

Install dependencies:

```bash
pip install flask azure-kusto-data azure-devops azure-identity
```

## Usage

1. Copy `.env.example` to `.env` and adjust values as needed.
2. Edit `config.yaml` with the organization, project, and Kusto cluster information.
3. Run the application:

```bash
python3 app.py
```

Open `http://localhost:5000/` to view the dashboard.

Set `DEV_MODE=true` in your environment to work with mock data without Azure credentials.

## Notes

Authentication uses Managed Identity when available. Logs for authentication failures are written in structured JSON format to stdout.
