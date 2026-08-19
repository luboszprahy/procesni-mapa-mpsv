# model genpage generate-types

Generates TypeScript schema definitions for data sources

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--data-sources` - Comma-separated list of data sources used (e.g., 'account,lead,contact').
- `--output-file` (`-o`) - Path to save the generated TypeScript schema file (defaults to RuntimeTypes.ts)

