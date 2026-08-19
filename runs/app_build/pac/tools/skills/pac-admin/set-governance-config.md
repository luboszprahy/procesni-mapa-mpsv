# admin set-governance-config

Enable, disable, and edit managed environments.

## Arguments

- `--environment` (`-env`) - URL or ID of the environment for which managed environments need to be enabled, disabled or edited.
- `--protection-level` (`-pl`) - Set protection level : 'Standard' to enable managed environments, 'Basic' to disable managed environments.
- `--disable-group-sharing` (`-dgs`) - Disable group sharing.
- `--exclude-analysis` (`-ea`) - Exclude usage insights for the environment from the weekly digest email.
- `--include-insights` (`-ii`) - Include insights in the Power Platform Admin Center homepage cards.
- `--limit-sharing-mode` (`-lsm`) - Limit sharing mode.
- `--max-limit-user-sharing` (`-ml`) - If group sharing is disabled, specify the number of people that makers can share canvas apps with.
- `--solution-checker-mode` (`-scm`) - Solution checker validation mode.
- `--maker-onboarding-url` (`-mou`) - Maker onboarding URL
- `--maker-onboarding-markdown` (`-mom`) - Maker onboarding markdown
- `--suppress-validation-emails` (`-sve`) - Suppress validation emails
- `--checker-rule-overrides` (`-cro`) - Solution checker rule overrides
- `--cloud-flows-mode` (`-cfm`) - Solution cloud flows limit sharing mode
- `--cloud-flows-limit` (`-cfl`) - Number of people that makers can share solution cloud flows with

