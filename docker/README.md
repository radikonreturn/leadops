# Run LeadOps with Docker

Install Docker with Docker Compose. On Windows, start Docker Desktop and enable
WSL integration for the distribution where you run these commands.

From the repository root:

```bash
docker compose up --build -d
```

Open http://localhost:3001. The first build downloads Node.js and installs the
frontend dependencies, so it needs internet access. The current page also uses
Next.js Google Fonts, which requires network access when compiling.

Useful commands:

```bash
docker compose logs -f web  # Follow server logs; Ctrl+C exits the log viewer
docker compose down         # Stop and remove the container
```

This setup runs the Next.js development server. The `src/` and `public/`
directories are mounted into the container so edits are available without
rebuilding. After changing dependencies or configuration files, rerun
`docker compose up --build -d`. If edits on a Windows-mounted drive are not
detected, restart with `docker compose restart web`.

Only the frontend is started. The Python API currently has no application entry
point; API and database services are not configured yet.

If Docker reports `Failed to initialize: protocol not available`, verify Docker
Desktop is running, enable its WSL integration, and retry from an integrated WSL
terminal or from PowerShell in the repository directory.
