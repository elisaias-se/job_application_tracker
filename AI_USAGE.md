# AI usage documentation

## Tools used
- OpenAI Codex assisted with planning, Flask code, SQL, templates, tests, and documentation.

## Key prompts
1. Review Project_Specification.docx and propose an architecture before implementation.
2. Implement the application in the dedicated repository with separate pushes and organized commits for each feature.

## What worked
- Mapping the four required tables to reusable CRUD workflows.
- Separating deterministic skill matching from HTTP routes.

## Changes and review
- Planned direct parameterized SQL to make database operations visible for the course.
- Chose restricted foreign-key deletion to preserve dependent records.
- AI-generated work is identified here; no independent human edits are claimed.

## Lessons
- AI output must be checked against the actual rubric and tested.
- A live AI API is unnecessary for deterministic skill matching.
- Validation must cover server-side inputs, not just HTML form constraints.
