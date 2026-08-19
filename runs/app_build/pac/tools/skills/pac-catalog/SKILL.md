---
name: pac-catalog
description: "PAC CLI catalog command group skill. It can be run as `pac catalog` if PAC CLI is installed or with .NET dnx command: `dnx Microsoft.PowerApps.CLI.Tool --yes catalog ...`. Commands for working with Catalog in Power Platform. List of supported commands: create-submission, install, list, status, submit, update"
---

Most PAC CLI commands require authentication and environment context. CLI can use OS credentials by default, but you can create more authentication profiles with 'pac auth create' command, see them with 'pac auth list', and switch between them with 'pac auth select'. Similarly, you can see environments with 'pac env list' and switch between environments with 'pac env select' or pass environment as an argument to commands that support it. You can also see environments where you have admin privileges with 'pac admin list'. You can also check your current authentication and environment context with 'pac auth who' and 'pac env who'.

## Commands

- [catalog create-submission](create-submission.md)
- [catalog install](install.md)
- [catalog list](list.md)
- [catalog status](status.md)
- [catalog submit](submit.md)
- [catalog update](update.md)

