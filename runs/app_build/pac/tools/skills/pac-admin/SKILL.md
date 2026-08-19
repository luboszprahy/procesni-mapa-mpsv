---
name: pac-admin
description: "PAC CLI admin command group skill. It can be run as `pac admin` if PAC CLI is installed or with .NET dnx command: `dnx Microsoft.PowerApps.CLI.Tool --yes admin ...`. Work with your Power Platform Admin Account. List of supported commands: add-group, application list, application register, application unregister, assign-group, assign-user, backup, copy, create, create-service-principal, delete, dlp-policy list, dlp-policy show, list, list-app-templates, list-backups, list-groups, list-roles, list-service-principal, list-tenant-settings, query, reset, restore, self-elevate, set-backup-retention-period, set-governance-config, set-runtime-state, status, update-tenant-settings"
---

Most PAC CLI commands require authentication and environment context. CLI can use OS credentials by default, but you can create more authentication profiles with 'pac auth create' command, see them with 'pac auth list', and switch between them with 'pac auth select'. Similarly, you can see environments with 'pac env list' and switch between environments with 'pac env select' or pass environment as an argument to commands that support it. You can also see environments where you have admin privileges with 'pac admin list'. You can also check your current authentication and environment context with 'pac auth who' and 'pac env who'.

## Commands

- [admin add-group](add-group.md)
- [admin application list](application/list.md)
- [admin application register](application/register.md)
- [admin application unregister](application/unregister.md)
- [admin assign-group](assign-group.md)
- [admin assign-user](assign-user.md)
- [admin backup](backup.md)
- [admin copy](copy.md)
- [admin create](create.md)
- [admin create-service-principal](create-service-principal.md)
- [admin delete](delete.md)
- [admin dlp-policy list](dlp-policy/list.md)
- [admin dlp-policy show](dlp-policy/show.md)
- [admin list](list.md)
- [admin list-app-templates](list-app-templates.md)
- [admin list-backups](list-backups.md)
- [admin list-groups](list-groups.md)
- [admin list-roles](list-roles.md)
- [admin list-service-principal](list-service-principal.md)
- [admin list-tenant-settings](list-tenant-settings.md)
- [admin query](query.md)
- [admin reset](reset.md)
- [admin restore](restore.md)
- [admin self-elevate](self-elevate.md)
- [admin set-backup-retention-period](set-backup-retention-period.md)
- [admin set-governance-config](set-governance-config.md)
- [admin set-runtime-state](set-runtime-state.md)
- [admin status](status.md)
- [admin update-tenant-settings](update-tenant-settings.md)

