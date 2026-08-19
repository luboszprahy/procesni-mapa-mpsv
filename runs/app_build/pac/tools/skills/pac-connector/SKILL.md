---
name: pac-connector
description: "PAC CLI connector command group skill. It can be run as `pac connector` if PAC CLI is installed or with .NET dnx command: `dnx Microsoft.PowerApps.CLI.Tool --yes connector ...`. Commands for working with Power Platform Connectors. List of supported commands: create, download, init, list, update"
---

Most PAC CLI commands require authentication and environment context. CLI can use OS credentials by default, but you can create more authentication profiles with 'pac auth create' command, see them with 'pac auth list', and switch between them with 'pac auth select'. Similarly, you can see environments with 'pac env list' and switch between environments with 'pac env select' or pass environment as an argument to commands that support it. You can also see environments where you have admin privileges with 'pac admin list'. You can also check your current authentication and environment context with 'pac auth who' and 'pac env who'.

## Commands

- [connector create](create.md)
- [connector download](download.md)
- [connector init](init.md)
- [connector list](list.md)
- [connector update](update.md)

