---
name: agent-change-log
description: Enforces post-task logging for agent-made code changes. Use when agents modify files, complete implementation tasks, or run git commit/push workflows to ensure a timestamped log file is created in logs/.
---

# Agent Change Log

## When to apply

Apply this skill whenever an agent:
- modifies or creates project files;
- completes a feature/fix/refactor task;
- prepares commit or push steps.

## Required completion step

If any project files changed during the task, create a log file in `logs/` before final completion.

## Log filename format

Use this exact format:

`yyyy-mm-dd_hh-mm-ss_git_log.md`

Examples:
- `2026-03-11_22-03-21_git_log.md`
- `2026-03-11_22-24-10_git_log.md`

## Minimum log content

Include:
- task objective;
- list of files created/modified;
- key implemented changes (2-6 bullets);
- verification status (lint/tests/run/checks);
- next action or status (ready to commit/push or already pushed).

## Workflow checklist

1. Detect whether files changed.
2. If changed, generate timestamp.
3. Create the log file in `logs/` with required format.
4. Ensure content is concise and actionable.
5. Then return final response to user.
