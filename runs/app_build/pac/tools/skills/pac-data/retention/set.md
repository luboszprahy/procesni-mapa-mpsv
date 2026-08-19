# data retention set

Create or update a retention policy for a table.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--entity` (`-e`) - The logical name of the table to configure retention for.
- `--criteria` (`-c`) - FetchXML criteria defining which records to retain.
- `--start-time` (`-st`) - The scheduled start time in ISO 8601 format (e.g., 2025-06-01T00:00:00Z). Defaults to now.
- `--recurrence` (`-r`) - Recurrence pattern for the job (e.g., FREQ=DAILY;INTERVAL=1).

