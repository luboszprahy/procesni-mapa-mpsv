# connector update

Updates a Connector Entity in Dataverse.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--connector-id` (`-id`) - The ID of the Connector
- `--api-definition-file` (`-df`) - The filename and path to read the Connector's OpenApiDefinition.
- `--api-properties-file` (`-pf`) - The filename and path to read the Connector's API Properties file.
- `--icon-file` (`-if`) - The filename and path to and Icon .png file.
- `--script-file` (`-sf`) - The filename and path to a Script .csx file.
- `--solution-unique-name` (`-sol`) - The unique name of the solution to add the connector to
- `--settings-file` - The filename and path Connector Settings file.

