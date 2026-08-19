# model genpage remove

Detach existing generative AI page(s) from a model-driven app's sitemap. The page row in Dataverse is preserved (it may still be referenced from other apps).

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--app-id` - Model-driven app id (uniqueid) to remove the page(s) from. Mutually exclusive with --app-name.
- `--app-name` - Model-driven app unique name to remove the page(s) from. Mutually exclusive with --app-id.
- `--page-id` - One or more uxagentproject ids to remove (comma separated).
- `--solution` - Dataverse solution unique name for the sitemap update. Defaults to 'Default'.
- `--publish` - Publish the model-driven app after the sitemap edit so changes go live immediately.

