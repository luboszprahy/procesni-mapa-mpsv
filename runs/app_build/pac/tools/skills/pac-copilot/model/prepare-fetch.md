# copilot model prepare-fetch

Takes the FetchXML file from the AI Large Language Model (LLM) and prepares it for execution against the current environment.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--inputFile` (`-i`) - Input FetchXML file that usually comes from AI LLM.
- `--outputFile` (`-o`) - Output FetchXML file that is ready to execute against the current environment.

