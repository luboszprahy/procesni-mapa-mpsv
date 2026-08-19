# model genpage transpile

Transpiles a TypeScript file with runtime types for testing and debugging

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--code-file` - Path to the file containing the page code.
- `--output-file` - Path to save the transpiled JavaScript output (defaults to [code-file].compiled.js)
- `--data-sources` - Comma-separated list of data sources used (e.g., 'account,lead,contact').

