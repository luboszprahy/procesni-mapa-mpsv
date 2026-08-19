---
name: pac-pages
description: "PAC CLI pages command group skill. It can be run as `pac pages` if PAC CLI is installed or with .NET dnx command: `dnx Microsoft.PowerApps.CLI.Tool --yes pages ...`. Commands for working with Power Pages website. List of supported commands: bootstrap-migrate, clone, download, download-code-site, list, migrate-datamodel, upload, upload-code-site"
---

Most PAC CLI commands require authentication and environment context. CLI can use OS credentials by default, but you can create more authentication profiles with 'pac auth create' command, see them with 'pac auth list', and switch between them with 'pac auth select'. Similarly, you can see environments with 'pac env list' and switch between environments with 'pac env select' or pass environment as an argument to commands that support it. You can also see environments where you have admin privileges with 'pac admin list'. You can also check your current authentication and environment context with 'pac auth who' and 'pac env who'.

## Commands

- [pages bootstrap-migrate](bootstrap-migrate.md)
- [pages clone](clone.md)
- [pages download](download.md)
- [pages download-code-site](download-code-site.md)
- [pages list](list.md)
- [pages migrate-datamodel](migrate-datamodel.md)
- [pages upload](upload.md)
- [pages upload-code-site](upload-code-site.md)

