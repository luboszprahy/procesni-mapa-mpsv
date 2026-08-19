---
name: pac-auth
description: "PAC CLI auth command group skill. It can be run as `pac auth` if PAC CLI is installed or with .NET dnx command: `dnx Microsoft.PowerApps.CLI.Tool --yes auth ...`. Manage how you authenticate to various services. List of supported commands: clear, create, delete, list, name, select, update, who"
---

Most PAC CLI commands require authentication and environment context. CLI can use OS credentials by default, but you can create more authentication profiles with 'pac auth create' command, see them with 'pac auth list', and switch between them with 'pac auth select'. Similarly, you can see environments with 'pac env list' and switch between environments with 'pac env select' or pass environment as an argument to commands that support it. You can also see environments where you have admin privileges with 'pac admin list'. You can also check your current authentication and environment context with 'pac auth who' and 'pac env who'.

## Commands

- [auth clear](clear.md)
- [auth create](create.md)
- [auth delete](delete.md)
- [auth list](list.md)
- [auth name](name.md)
- [auth select](select.md)
- [auth update](update.md)
- [auth who](who.md)

