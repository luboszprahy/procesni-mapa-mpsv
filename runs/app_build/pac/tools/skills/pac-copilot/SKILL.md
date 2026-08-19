---
name: pac-copilot
description: "PAC CLI copilot command group skill. It can be run as `pac copilot` if PAC CLI is installed or with .NET dnx command: `dnx Microsoft.PowerApps.CLI.Tool --yes copilot ...`. Tools and utilities for copilot management. List of supported commands: clone, create, delete, extract-template, extract-translation, init, list, mcp, merge-translation, model list, model predict, model prepare-fetch, pack, publish, pull, push, quarantine, status"
---

Most PAC CLI commands require authentication and environment context. CLI can use OS credentials by default, but you can create more authentication profiles with 'pac auth create' command, see them with 'pac auth list', and switch between them with 'pac auth select'. Similarly, you can see environments with 'pac env list' and switch between environments with 'pac env select' or pass environment as an argument to commands that support it. You can also see environments where you have admin privileges with 'pac admin list'. You can also check your current authentication and environment context with 'pac auth who' and 'pac env who'.

## Commands

- [copilot clone](clone.md)
- [copilot create](create.md)
- [copilot delete](delete.md)
- [copilot extract-template](extract-template.md)
- [copilot extract-translation](extract-translation.md)
- [copilot init](init.md)
- [copilot list](list.md)
- [copilot mcp](mcp.md)
- [copilot merge-translation](merge-translation.md)
- [copilot model list](model/list.md)
- [copilot model predict](model/predict.md)
- [copilot model prepare-fetch](model/prepare-fetch.md)
- [copilot pack](pack.md)
- [copilot publish](publish.md)
- [copilot pull](pull.md)
- [copilot push](push.md)
- [copilot quarantine](quarantine.md)
- [copilot status](status.md)

