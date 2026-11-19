# AI Usage Documentation

## Tools used

OpenAI Codex assisted with requirement review, architecture, Python/Flask implementation, MySQL SQL, HTML/Jinja templates, CSS, JavaScript, tests, and documentation. Git, pytest, MySQL, and the Python runtime were used to verify generated work. The application does not call an AI service at runtime.

## Key user prompts

1. “Review the instructions .docx ... Before any implementation please go over what you will do to create the job application tracker, file architecture, etc.”
2. “Please implement the app to the repository. Separate your pushes, there needs to be organized commit messages for each feature.” (Spelling normalized.)
3. “For any push or commit please let me see what message you will put and wait for my approval. Messages should be brief but organized with feature descriptions.” (Capitalization normalized.)
4. The user approved individual feature commit messages for companies, jobs, applications, contacts, the dashboard, and matching.

These were the actual task instructions. No additional tools, model identities, or imagined human prompts are attributed here.

## What worked well

- Translating the document's four-table schema and grading categories into concrete features and an implementation sequence.
- Using allowlisted field definitions and shared CRUD templates to provide consistent forms and avoid copying route logic for every entity.
- Keeping SQL visible and parameterized, making joins and relationships easy to inspect for a database course.
- Separating skill matching into a pure Python service with focused examples and edge-case tests.
- Building feature-scoped tests while implementing each feature, then adding real MySQL lifecycle tests.
- Organizing repository history around small feature commits rather than one large code dump.

## Changes made during AI-assisted development

The following are refinements made by the AI coding agent during implementation, not claims of independent human-written changes:

- Replaced a monolithic prototype with an app factory, Blueprint, reusable entity metadata, and separate matching/dashboard services.
- Used restricted foreign-key deletion instead of cascading removal of tracked history.
- Added explicit server-side checks for salary bounds/order, allowed statuses and job types, dates, email/URLs, and existing parent records.
- Added CSRF tokens and preserved form inputs when validation fails.
- Corrected an integer-validation error path so malformed numbers return validation messages instead of a Python exception.
- Converted required skills to JSON arrays and interviews to structured JSON objects while presenting ordinary form inputs.
- Shared normalization between job editing and matching; prevented duplicate skills from inflating scores and sorted by unrounded scores.
- Added unscored handling for missing requirements, empty states, and stable result ordering.
- Kept tests that mock SQL separate from opt-in integration tests using isolated, disposable MySQL databases.
- Added sample data and explicit clone-to-run instructions so the instructor can reproduce the application.

The initial foundation commit/push was already in progress when the user requested individual message approval. Subsequent feature commits were presented for approval before committing/pushing.

## Verification and limitations

Tests cover the specification's matching examples, all CRUD resource routes, input validation, parameter binding, JSON conversion, CSRF, escaping, dashboard states, and dependency-related deletion errors. Real MySQL tests additionally cover schema creation, sample data, persistence, FK restrictions, salary constraints, and successful token-protected submission. See README.md for running both test modes and the GitHub Actions workflow.

Verification completed: 120 pytest tests passed against MySQL 8.4, including the four integration tests. An implementation-time headless Google Chrome check also passed for desktop/mobile layout, matching, CSRF forms, interview controls, persistence, and deletion. Screenshots use only fictional seed records. The browser check is separate from the committed pytest suite.

Automated tests are evidence of the paths they exercise, not a claim that every browser, operating system, or deployment configuration has been tested. The user should review the code, run the app, and explain its behavior in the required recording.

## Lessons learned

- Check AI output against the original rubric, particularly exact column names, ENUMs, JSON fields, and all four CRUD workflows.
- Browser validation alone is insufficient; submitted values still need validation on the server.
- Mock-based tests run quickly, but only a real MySQL test validates the actual schema, SQL joins, constraints, and connector behavior together.
- Document the matching denominator explicitly: required job skills, not the number of skills entered by the user.
- AI-assisted development does not require a paid AI API in the finished application.
- Treat commit and publication preferences as part of the requirements, and obtain approval before each requested commit/push.
