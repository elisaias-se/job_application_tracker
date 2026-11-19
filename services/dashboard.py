"""Dashboard summaries computed from the current database records."""
from database import query
from services.entities import APPLICATION_STATUSES


def dashboard_data():
    counts = query('''
        SELECT
            (SELECT COUNT(*) FROM companies) AS companies,
            (SELECT COUNT(*) FROM jobs) AS jobs,
            (SELECT COUNT(*) FROM applications) AS applications,
            (SELECT COUNT(*) FROM contacts) AS contacts
    ''')[0]
    grouped = query('SELECT status, COUNT(*) AS count FROM applications GROUP BY status')
    by_status = {row['status']: row['count'] for row in grouped}
    statuses = [{'name': status, 'count': by_status.get(status, 0)}
                for status in APPLICATION_STATUSES]
    recent = query('''
        SELECT applications.application_id, applications.application_date,
               applications.status, jobs.job_title, companies.company_name
        FROM applications
        JOIN jobs USING (job_id)
        JOIN companies USING (company_id)
        ORDER BY applications.application_date DESC, applications.application_id DESC
        LIMIT 5
    ''')
    return dict(counts=counts, statuses=statuses, recent=recent)
