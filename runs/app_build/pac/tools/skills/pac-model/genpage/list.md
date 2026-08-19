# model genpage list

List generated pages — env-wide by default, or for one app when --app-id is supplied. Pass --include-unpublished to also list draft pages.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--app-id` - The ID of the model-driven app.
- `--include-unpublished` - Include unpublished generative pages in the list (default: only published).

