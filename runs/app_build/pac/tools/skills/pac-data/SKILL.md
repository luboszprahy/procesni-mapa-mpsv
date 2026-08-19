---
name: pac-data
description: "PAC CLI data command group skill. It can be run as `pac data` if PAC CLI is installed or with .NET dnx command: `dnx Microsoft.PowerApps.CLI.Tool --yes data ...`. Import and export data from Dataverse. List of supported commands: bulk-delete cancel, bulk-delete list, bulk-delete pause, bulk-delete resume, bulk-delete schedule, bulk-delete show, export, import, retention enable-entity, retention list, retention set, retention show, retention status"
---

Most PAC CLI commands require authentication and environment context. CLI can use OS credentials by default, but you can create more authentication profiles with 'pac auth create' command, see them with 'pac auth list', and switch between them with 'pac auth select'. Similarly, you can see environments with 'pac env list' and switch between environments with 'pac env select' or pass environment as an argument to commands that support it. You can also see environments where you have admin privileges with 'pac admin list'. You can also check your current authentication and environment context with 'pac auth who' and 'pac env who'.

## Commands

- [data bulk-delete cancel](bulk-delete/cancel.md)
- [data bulk-delete list](bulk-delete/list.md)
- [data bulk-delete pause](bulk-delete/pause.md)
- [data bulk-delete resume](bulk-delete/resume.md)
- [data bulk-delete schedule](bulk-delete/schedule.md)
- [data bulk-delete show](bulk-delete/show.md)
- [data export](export.md)
- [data import](import.md)
- [data retention enable-entity](retention/enable-entity.md)
- [data retention list](retention/list.md)
- [data retention set](retention/set.md)
- [data retention show](retention/show.md)
- [data retention status](retention/status.md)

