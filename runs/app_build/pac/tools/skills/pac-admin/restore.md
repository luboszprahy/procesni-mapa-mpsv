# admin restore

Restores an environment to a given backup.

## Arguments

- `--source-env` (`-se`) - Environment URL or ID of the source environment required for restore.
- `--target-env` (`-te`) - Environment URL or ID of the target environment required for restore. This would default to source URL/ID if not provided.
- `--selected-backup` (`-sb`) - DateTime of the backup in 'mm/dd/yyyy hh:mm' format OR string 'latest'.
- `--name` (`-n`) - Optional name of the restored environment.
- `--skip-audit-data` (`-sa`) - Switch indicating whether audit data should be skipped
- `--async` (`-a`) - Optional boolean argument to run pac verbs asynchronously, defaults to false.
- `--max-async-wait-time` (`-wt`) - Max asynchronous wait time in minutes. The default value is 60 minutes.

