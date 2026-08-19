---
name: pac-env
description: "PAC CLI env command group skill. It can be run as `pac env` if PAC CLI is installed or with .NET dnx command: `dnx Microsoft.PowerApps.CLI.Tool --yes env ...`. Work with your Dataverse organization. List of supported commands: fetch, list, list-settings, select, update-settings, who"
---

Most PAC CLI commands require authentication and environment context. CLI can use OS credentials by default, but you can create more authentication profiles with 'pac auth create' command, see them with 'pac auth list', and switch between them with 'pac auth select'. Similarly, you can see environments with 'pac env list' and switch between environments with 'pac env select' or pass environment as an argument to commands that support it. You can also see environments where you have admin privileges with 'pac admin list'. You can also check your current authentication and environment context with 'pac auth who' and 'pac env who'.

## Commands

- [env fetch](fetch.md)
- [env list](list.md)
- [env list-settings](list-settings.md)
- [env select](select.md)
- [env update-settings](update-settings.md)
- [env who](who.md)

