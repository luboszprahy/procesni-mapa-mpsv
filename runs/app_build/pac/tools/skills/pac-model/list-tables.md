# model list-tables

List Dataverse tables in the connected environment.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--search` (`-s`) - Comma-separated list of names to search for (matches logical name, schema name, or display name).
- `--type` (`-t`) - Filter by table type: 'custom', 'standard', or 'all' (default: all).

