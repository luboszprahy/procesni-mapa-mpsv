# copilot init

Create a new Copilot Studio agent workspace from a template.

## Arguments

- `--name` (`-n`) - Agent display name.
- `--publisher-prefix` (`-pp`) - Publisher customization prefix for the solution.
- `--instructions` (`-ins`) - Agent system instructions.
- `--schema-name` (`-sn`) - Full agent schema name. Overrides the default derivation ({publisher-prefix}_{sanitized-name}). Used as-is without modification.
- `--project-dir` (`-pd`) - Target directory for the agent workspace. Defaults to current directory.
- `--template` (`-t`) - Template profile name (default, minimal). Defaults to 'default'.
- `--authoring-mode` (`-am`) - The agent authoring shape to scaffold (default: 'classic'). Use 'cli-copilot' to scaffold a CLI-authored CliCopilot agent.
- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.

