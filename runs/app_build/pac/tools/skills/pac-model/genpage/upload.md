# model genpage upload

Upload a generated page to Dataverse and publish it. Creates a new page when --page-id is omitted; updates the existing page when --page-id is supplied. To attach a page that already exists in the environment to another app's sitemap without re-uploading, use 'pac model genpage add' instead.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--app-id` - The ID of the model-driven app.
- `--page-id` - The ID of the page to update. If not provided, a new page will be created.
- `--code-file` - Path to the file containing the page code.
- `--compiled-code-file` - Path to the file containing the compiled JavaScript code. If not provided, TypeScript will be automatically transpiled to JavaScript.
- `--name` (`-n`) - The name of the page.
- `--prompt` - The user prompt that generated this page.
- `--prompt-file` - Path to a file containing the user prompt that generated this page.
- `--agent-message` - The agent's response message.
- `--agent-message-file` - Path to a file containing the agent's response message.
- `--data-sources` - Comma-separated list of data sources used (e.g., 'account,lead,contact').
- `--model` - The AI model used to generate the page (e.g., 'claude-3-5-sonnet-20241022').
- `--add-to-sitemap` - Add the page to the app's sitemap navigation.

