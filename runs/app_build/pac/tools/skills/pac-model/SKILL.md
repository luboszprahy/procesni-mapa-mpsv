---
name: pac-model
description: "PAC CLI model command group skill. It can be run as `pac model` if PAC CLI is installed or with .NET dnx command: `dnx Microsoft.PowerApps.CLI.Tool --yes model ...`. Commands for working with model-driven apps. List of supported commands: create, genpage add, genpage download, genpage generate-types, genpage list, genpage remove, genpage transpile, genpage upload, list, list-languages, list-tables"
---

Most PAC CLI commands require authentication and environment context. CLI can use OS credentials by default, but you can create more authentication profiles with 'pac auth create' command, see them with 'pac auth list', and switch between them with 'pac auth select'. Similarly, you can see environments with 'pac env list' and switch between environments with 'pac env select' or pass environment as an argument to commands that support it. You can also see environments where you have admin privileges with 'pac admin list'. You can also check your current authentication and environment context with 'pac auth who' and 'pac env who'.

## Commands

- [model create](create.md)
- [model genpage add](genpage/add.md)
- [model genpage download](genpage/download.md)
- [model genpage generate-types](genpage/generate-types.md)
- [model genpage list](genpage/list.md)
- [model genpage remove](genpage/remove.md)
- [model genpage transpile](genpage/transpile.md)
- [model genpage upload](genpage/upload.md)
- [model list](list.md)
- [model list-languages](list-languages.md)
- [model list-tables](list-tables.md)

