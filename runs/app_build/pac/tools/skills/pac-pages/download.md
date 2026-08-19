# pages download

Download Power Pages website content from the current Dataverse environment.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--path` (`-p`) - Path where the Power Pages website content is downloaded
- `--webSiteId` (`-id`) - Power Pages website ID to download
- `--includeEntities` (`-ie`) - Download only the entities specified for this argument using comma separated entity logical names.
- `--excludeEntities` (`-xe`) - Comma separated list of entity logical names to exclude downloading
- `--overwrite` (`-o`) - Power Pages website content to overwrite
- `--modelVersion` (`-mv`) - Power Pages website data model version to download. When not specified, 'Standard' will be used. [Enhanced or Standard]

