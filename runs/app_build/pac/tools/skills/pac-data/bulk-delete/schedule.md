# data bulk-delete schedule

Schedule a bulk delete job for records in a table.

## Arguments

- `--environment` (`-env`) - Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
- `--entity` (`-e`) - The logical name of the table (e.g., account, activitypointer).
- `--fetchxml` (`-fx`) - FetchXML query to filter records. If omitted, all records in the table are targeted.
- `--job-name` (`-jn`) - A descriptive name for the bulk delete job.
- `--start-time` (`-st`) - The scheduled start time in ISO 8601 format (e.g., 2025-06-01T00:00:00Z). Defaults to now.
- `--recurrence` (`-r`) - Recurrence pattern for the job (e.g., FREQ=DAILY;INTERVAL=1).

