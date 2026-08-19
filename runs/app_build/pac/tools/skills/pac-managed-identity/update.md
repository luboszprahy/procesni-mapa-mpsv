# managed-identity update

(Preview) Update tenant or application identifiers for the linked managed identity

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--component-type` (`-t`) - Component type (for example, ServiceEndpoint, PluginAssembly, CopilotStudio)
- `--component-id` (`-id`) - Dataverse record ID (GUID) for the component
- `--tenant-id` (`-tid`) - Azure AD tenant ID for the managed identity or application registration
- `--application-id` (`-aid`) - Application (client) ID of the managed identity or app registration

