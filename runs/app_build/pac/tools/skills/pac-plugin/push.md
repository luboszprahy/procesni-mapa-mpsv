# plugin push

Import plug-in into Dataverse.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--pluginId` (`-id`) - ID of plug-in assembly or plug-in package
- `--pluginFile` (`-pf`) - File name of plug-in assembly or plug-in package
- `--type` (`-t`) - Type of item if not specified explicitly through --pluginFile. The default value is: 'Nuget'.
- `--configuration` (`-c`) - Build configuration. The default value is: 'Debug'.

