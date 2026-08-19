# copilot clone

Clone a Copilot Studio agent to a local workspace directory.

## Arguments

- `--bot` (`-id`) - The Copilot ID or schema name (unique name found in Bot Details or file name in solution explorer).
- `--display-name` (`-dn`) - Display name of the agent (used for folder naming).
- `--output-dir` (`-od`) - Root folder for clone output. Defaults to current directory.
- `--component-collection` (`-cc`) - Component collection ID to clone. Repeat for multiple.
- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.

