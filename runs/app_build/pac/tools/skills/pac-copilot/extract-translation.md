# copilot extract-translation

Extracts file containing localized content for one or more bots.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--sourcedir` (`-src`) - Source solution directory. When specified, will ignore the connected environment when looking for bots and instead look for content in the solution folder.
- `--bot` (`-id`) - The Copilot ID or schema name (unique name found in Bot Details or file name in solution explorer).
- `--outdir` - The output directory to write to.
- `--format` - The file format in which to write localized files, either 'resx' or 'json'. The default is 'resx'.
- `--all` (`-a`) - Write localization files for all supported languages. By default, only the primary language is written.
- `--overwrite` (`-o`) - Allow overwrite of the output data file if it already exists.

