# admin reset

Reset the environment from your tenant.

## Arguments

- `--environment` (`-env`) - URL or ID of the Environment that needs to be reset.
- `--currency` (`-c`) - Sets the currency used for your environment. [defaults to USD]
- `--domain` (`-d`) - The domain name is part of the environment URL. If domain name is already in use, a numeric value is appended to the domain name. For example: If 'contoso' is already in use, then the environment URL is updated to https://{contoso}0.crm.dynamics.com.
- `--name` (`-n`) - Sets the name of the environment.
- `--language` (`-l`) - Sets the language used for your environment. [defaults to English]
- `--purpose` (`-p`) - Sets the description used to associate the environment with a specific intent.
- `--templates` (`-tm`) - Sets the Dynamics 365 app that needs to be deployed, passed as comma separated values. For example: -tm "D365_Sample, D365_Sales"
- `--input-file` (`-if`) - The verb arguments to be passed in a .json input file. For example: {"name" : "contoso"}. The arguments passed through command-line will take precedence over arguments from the .json input file.
- `--async` (`-a`) - Optional boolean argument to run pac verbs asynchronously, defaults to false.
- `--max-async-wait-time` (`-wt`) - Max asynchronous wait time in minutes. The default value is 60 minutes.

