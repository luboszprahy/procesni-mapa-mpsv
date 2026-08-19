# catalog install

Install a catalog item to the target environment.

## Arguments

- `--environment` (`-env`) - Url or ID of the environment that has catalog installed. When not specified, the active organization selected for the current auth profile will be used.
- `--target-env` (`-te`) - Url or ID of the target environment for catalog item installation
- `--target-url` (`-tu`) - Url of the target environment for catalog item installation
- `--catalog-item-id` (`-cid`) - Catalog item to be installed on the target environment.
- `--settings` (`-s`) - Runtime Package Settings for the installation framework to execute. The format of the string must be `key=value|key=value`.
- `--target-version` (`-tv`) - Target version to install. If left empty, the published version is selected.
- `--poll-status` (`-ps`) - Poll to check status of your request

