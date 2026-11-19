# AI Usage Documentation

## Human contribution and project direction

I directed the project and used OpenAI Codex as an implementation assistant. My contributions included defining the work, reviewing the proposed approach, making interface decisions, and providing feedback while trying the application locally.

### Requirements and planning

- Provided the course specification and created the dedicated GitHub repository.
- Required an explanation of the implementation plan and file architecture before coding began.
- Used the specification as the basis for the required database tables, CRUD workflows, dashboard, and job matching feature.
- Directed development to proceed in separate feature milestones rather than one large repository update.

### Review and version control

- Required proposed commit messages to be presented for approval before committing and pushing subsequent features.
- Approved the companies, jobs, applications, contacts, dashboard, and matching milestones individually.
- Supplied revised wording for the documentation/testing commit and directed how the later design update should be published.

These approvals reflect decisions about development milestones and publication; they do not imply an independent line-by-line code review.

### Interface design and feedback

- Requested a different application name, then selected **JobTrack** instead of the AI-proposed name.
- Specified that the white base should remain and green accents should change to blue.
- Requested removal of unnecessary slogans, including the text at the bottom of the sidebar.
- Reported that the running application still displayed the old branding, prompting investigation and a server restart to load the updated templates.

### Local use and demonstration preparation

- Asked how to run and test the application locally and how to start and connect to MySQL.
- Reported the database-unavailable message, which prompted checking the database, account, and configuration setup.
- Requested a walkthrough covering all features, database queries, and MySQL logs for the project recording.

## AI tools and scope of assistance

OpenAI Codex generated substantial portions of the Python/Flask code, SQL, HTML/Jinja templates, CSS, JavaScript, automated tests, and documentation under my direction. It also assisted with architecture, debugging, local setup instructions, and implementation verification. Human direction and feedback shaped the resulting application; the generated code and automated verification are attributed to the AI assistant.

Git, pytest, MySQL, Python, and headless Google Chrome were used during verification. The finished application does not call an AI service at runtime.

## Key prompts and instructions

The following summarize actual requests from the development conversation:

1. Review Project_Specification.docx and explain the implementation plan and file architecture before implementation.
2. Implement the app in the dedicated repository with separate pushes and organized feature commit messages.
3. Show each proposed commit message and wait for approval before committing or pushing.
4. Call the application JobTrack, remove unnecessary slogans, retain the white base, and change green accents to blue.
5. Explain how to run the application, start MySQL, and diagnose the database-unavailable message.
6. Create a text-file walkthrough for demonstrating all features, including MySQL logs, in the project video.

## What worked well

- Reviewing the architecture before implementation made the proposed scope concrete.
- Feature-by-feature development made individual milestones easier to discuss and approve.
- Specific interface feedback produced a clearer name, simpler wording, and the requested color scheme.
- AI assistance helped build consistent CRUD workflows, visible parameterized SQL, and a separate matching service.
- Automated tests and real MySQL checks provided evidence beyond whether a page appeared to work.

## Changes and refinements

### Changes I requested

- Renaming the application to JobTrack.
- Replacing green accents with blue while keeping the white base.
- Removing promotional slogans from the interface.
- Organizing commits and requiring approval before feature publication.
- Revising a proposed commit message and requesting a separate design update.

### Implementation refinements made with AI assistance

- Organized Flask code using an app factory, Blueprint, shared entity definitions, and separate services.
- Used foreign-key restrictions to preserve dependent records during deletion.
- Added server-side validation for salary ranges, dates, allowed values, URLs, email, and existing parent records.
- Added CSRF protection, escaped templates, parameterized SQL, and form-value preservation after validation errors.
- Stored skills and interview details as JSON while exposing ordinary form controls.
- Normalized skill names, removed duplicates, ranked by unrounded scores, and handled jobs without requirements.
- Added sample data, setup instructions, and tests using disposable MySQL databases.

These implementation refinements were carried out by Codex; they are not represented as code I independently wrote.

## Verification and limitations

The AI-assisted verification included 120 passing pytest tests against MySQL 8.4, including four integration tests. Browser checks exercised desktop/mobile layouts, matching, CSRF-protected forms, interview controls, persistence, and deletion. After the JobTrack design changes, 116 default tests passed, with four opt-in MySQL integration tests skipped, and the revised branding, colors, and mobile layout were checked in Chrome.

My contribution to verification included reporting observed setup and interface problems and directing corrections. The automated test runs and browser automation above were performed by the coding assistant. They do not establish that every browser, operating system, or deployment configuration has been tested.

README.md documents how to run the default and MySQL integration tests. AI assistance and passing tests do not replace understanding the code and explaining its behavior in the project recording.

## Lessons from the development process

- Human requirements, review decisions, and specific feedback influence the result throughout development.
- Check generated work against the actual rubric, including exact schema fields and all four CRUD workflows.
- Browser input constraints should be backed by server-side validation.
- Mock-based tests and real database tests verify different aspects of the application.
- Distinguish a database setup problem from an application-code defect, and cached templates from unchanged source files.
- State the skill-matching calculation clearly: matched required skills divided by total required skills.
- Attribute both human decisions and AI-generated implementation accurately.
