---
name: pac-managed-identity
description: "PAC CLI managed-identity command group skill. It can be run as `pac managed-identity` if PAC CLI is installed or with .NET dnx command: `dnx Microsoft.PowerApps.CLI.Tool --yes managed-identity ...`. Commands for managing Managed Identity records for Dataverse components. List of supported commands: configure-fic, create, delete, get, show-fic, update, upgrade-version, verify-fic"
---

Most PAC CLI commands require authentication and environment context. CLI can use OS credentials by default, but you can create more authentication profiles with 'pac auth create' command, see them with 'pac auth list', and switch between them with 'pac auth select'. Similarly, you can see environments with 'pac env list' and switch between environments with 'pac env select' or pass environment as an argument to commands that support it. You can also see environments where you have admin privileges with 'pac admin list'. You can also check your current authentication and environment context with 'pac auth who' and 'pac env who'.

## Commands

- [managed-identity configure-fic](configure-fic.md)
- [managed-identity create](create.md)
- [managed-identity delete](delete.md)
- [managed-identity get](get.md)
- [managed-identity show-fic](show-fic.md)
- [managed-identity update](update.md)
- [managed-identity upgrade-version](upgrade-version.md)
- [managed-identity verify-fic](verify-fic.md)

