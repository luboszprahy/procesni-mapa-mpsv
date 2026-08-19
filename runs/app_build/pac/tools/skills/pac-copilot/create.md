# copilot create

Creates a new copilot using an existing template file as the reference.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--schemaName` - The schema name (unique name) of the new copilot.
- `--templateFileName` - Source yaml file containing the copilot template that was extracted using the extract-template command.
- `--displayName` - The display name of the new copilot
- `--solution` (`-s`) - Name of the solution.

