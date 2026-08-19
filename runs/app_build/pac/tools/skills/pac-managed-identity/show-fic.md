# managed-identity show-fic

(Preview) Show the computed federated identity credential for a Dataverse component

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--component-type` (`-t`) - Component type (for example, ServiceEndpoint, PluginAssembly, CopilotStudio)
- `--component-id` (`-id`) - Dataverse record ID (GUID) for the component
- `--version` (`-v`) - The managed identity version to use for FIC generation. Version 1 uses CN-based FIC paths; version 2 uses SHA256-hashed paths that support certificates with special characters. Defaults to the version stored on the managed identity record.

