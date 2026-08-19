# model genpage add

Attach one or more existing generative pages to a model-driven app's sitemap (no re-upload). Use 'pac model genpage upload' to create or update the page itself; use this verb to make an already-uploaded page show up in another app.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--app-id` - The model-driven app's ID (GUID). Mutually exclusive with --app-name.
- `--app-name` - The model-driven app's unique name. Mutually exclusive with --app-id.
- `--page-id` - Comma-separated generative page IDs (GUIDs) to add to the app.
- `--solution` - Unique name of the Dataverse solution context for the sitemap update. Defaults to 'Default'.
- `--area` - Optional Area ID in the sitemap to place the page under. Defaults to the first Area.
- `--group` - Optional Group ID in the sitemap to place the page under. Defaults to the first Group of the chosen Area.
- `--language-code` - Language code (LCID) for the SubArea title. Defaults to 1033 (en-US).
- `--publish` - Publish the model-driven app after adding the page(s).

