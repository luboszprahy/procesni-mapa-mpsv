---
name: pac-code
description: "PAC CLI code command group skill. It can be run as `pac code` if PAC CLI is installed or with .NET dnx command: `dnx Microsoft.PowerApps.CLI.Tool --yes code ...`. (Preview) Commands to manage your Code apps. List of supported commands: add-data-source, delete-data-source, init, list, list-connection-references, list-datasets, list-sql-stored-procedures, list-tables, push, run"
---

Most PAC CLI commands require authentication and environment context. CLI can use OS credentials by default, but you can create more authentication profiles with 'pac auth create' command, see them with 'pac auth list', and switch between them with 'pac auth select'. Similarly, you can see environments with 'pac env list' and switch between environments with 'pac env select' or pass environment as an argument to commands that support it. You can also see environments where you have admin privileges with 'pac admin list'. You can also check your current authentication and environment context with 'pac auth who' and 'pac env who'.

## Commands

- [code add-data-source](add-data-source.md)
- [code delete-data-source](delete-data-source.md)
- [code init](init.md)
- [code list](list.md)
- [code list-connection-references](list-connection-references.md)
- [code list-datasets](list-datasets.md)
- [code list-sql-stored-procedures](list-sql-stored-procedures.md)
- [code list-tables](list-tables.md)
- [code push](push.md)
- [code run](run.md)

