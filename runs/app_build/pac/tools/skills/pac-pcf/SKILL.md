---
name: pac-pcf
description: "PAC CLI pcf command group skill. It can be run as `pac pcf` if PAC CLI is installed or with .NET dnx command: `dnx Microsoft.PowerApps.CLI.Tool --yes pcf ...`. Commands for working with Power Apps component framework projects. List of supported commands: init, push, version"
---

Most PAC CLI commands require authentication and environment context. CLI can use OS credentials by default, but you can create more authentication profiles with 'pac auth create' command, see them with 'pac auth list', and switch between them with 'pac auth select'. Similarly, you can see environments with 'pac env list' and switch between environments with 'pac env select' or pass environment as an argument to commands that support it. You can also see environments where you have admin privileges with 'pac admin list'. You can also check your current authentication and environment context with 'pac auth who' and 'pac env who'.

## Commands

- [pcf init](init.md)
- [pcf push](push.md)
- [pcf version](version.md)

