# Git Workflow

Use small, meaningful commits that describe an engineering change.

## Commit types

- feat: new robot capability
- fix: bug or hardware/software correction
- test: experiments and validation
- refactor: code restructuring without changing intended behaviour
- docs: documentation only
- chore: repository/tooling/maintenance work

## Examples

feat: add Xbox controller steering
fix: prevent motor movement after UDP timeout
test: evaluate smooth arm trajectory limits
refactor: centralize servo calibration constants
docs: document PiCar hardware setup
chore: add JARVIS engineering logging workflow

## Engineering evidence rule

A commit should represent meaningful progress.

Do not create commits merely because a file was opened or a trivial command
was executed.

At the end of a useful work session:

1. Run the relevant tests.
2. Record the session using tools/jarvis_log.sh.
3. Review git status and diff.
4. Commit code and its corresponding engineering log together when appropriate.
5. Push the validated commit to GitHub.
