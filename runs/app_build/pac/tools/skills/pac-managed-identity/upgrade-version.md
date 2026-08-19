# managed-identity upgrade-version

(Preview) Upgrade managed identity to the latest supported version for the component type

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--component-type` (`-t`) - Component type (for example, ServiceEndpoint, PluginAssembly, CopilotStudio)
- `--component-id` (`-id`) - Dataverse record ID (GUID) for the component
- `--revert-version` - Revert the managed identity to the previous version instead of upgrading
- `--skip-fic-configuration` - Skip automatic federated identity credential configuration. When set, shows FIC values for manual Azure Portal configuration and requires user confirmation before version upgrade.
- `--confirm` (`-y`) - Confirms the upgrade-version operation when updating or reverting the managed identity version
- `--target-version` - Target version to upgrade to (e.g., 2). Performs all intermediate upgrades automatically. If not specified, upgrades by one version.

