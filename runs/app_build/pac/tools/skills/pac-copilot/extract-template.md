# copilot extract-template

Extracts a template file from an existing copilot in an environment.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--bot` (`-id`) - The Copilot ID or schema name (unique name found in Bot Details or file name in solution explorer).
- `--templateFileName` - Location of the yaml file to write the copilot template to.
- `--overwrite` (`-o`) - Allow overwrite of the output data file if it already exists.
- `--templateName` - Template name or 'kickStartTemplate' if name is not specified.
- `--templateVersion` - Template version in X.X.X format or 1.0.0 if version is not specified.

