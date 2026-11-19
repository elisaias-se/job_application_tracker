-- Optional fictional demonstration records. Run after schema.sql, once per demo database.
USE job_tracker;
START TRANSACTION;
INSERT INTO companies (company_name, industry, website, city, state, notes)
VALUES ('Evergreen Labs', 'Software', 'https://example.com', 'Boston', 'MA', 'Fictional demo company.');
SET @evergreen = LAST_INSERT_ID();
INSERT INTO companies (company_name, industry, website, city, state, notes)
VALUES ('Northstar Analytics', 'Data analytics', 'https://example.org', 'New York', 'NY', 'Fictional demo company.');
SET @northstar = LAST_INSERT_ID();
INSERT INTO companies (company_name, industry, city, state)
VALUES ('Brightpath Studio', 'Design', 'Philadelphia', 'PA');
SET @brightpath = LAST_INSERT_ID();
INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, date_posted, requirements)
VALUES (@evergreen, 'Software Developer', 'Full-time', 80000, 110000, '2026-11-01', JSON_ARRAY('Python', 'SQL', 'Flask'));
SET @developer = LAST_INSERT_ID();
INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, date_posted, requirements)
VALUES (@northstar, 'Data Analyst', 'Full-time', 65000, 90000, '2026-11-03', JSON_ARRAY('Python', 'SQL', 'Tableau'));
SET @analyst = LAST_INSERT_ID();
INSERT INTO jobs (company_id, job_title, job_type, date_posted, requirements)
VALUES (@brightpath, 'Web Development Intern', 'Internship', '2026-11-04', JSON_ARRAY('HTML', 'CSS', 'JavaScript'));
SET @intern = LAST_INSERT_ID();
INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data)
VALUES (@developer, '2026-11-06', 'Interview', 'developer-v2', TRUE,
        JSON_ARRAY(JSON_OBJECT('date', '2026-11-20T10:00', 'format', 'Video', 'interviewer', 'Alex Morgan', 'notes', 'Prepare a project walkthrough.'))),
       (@analyst, '2026-11-07', 'Applied', 'analyst-v1', FALSE, JSON_ARRAY()),
       (@intern, '2026-11-08', 'Screening', 'general-v1', TRUE, JSON_ARRAY()),
       (@developer, '2026-10-15', 'Offer', 'developer-v1', TRUE, JSON_ARRAY()),
       (@analyst, '2026-10-12', 'Rejected', 'analyst-v1', FALSE, JSON_ARRAY()),
       (@intern, '2026-10-10', 'Withdrawn', 'general-v1', FALSE, JSON_ARRAY());
INSERT INTO contacts (company_id, contact_name, title, email, notes)
VALUES (@evergreen, 'Alex Morgan', 'Technical recruiter', 'alex@example.com', 'Ask about the interview format.'),
       (@northstar, 'Jordan Lee', 'Recruiter', 'jordan@example.org', 'Met at a fictional career fair.');
COMMIT;
