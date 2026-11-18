"""Allowlisted entity definitions shared by forms and SQL builders."""
def field(name, label, kind='text', required=False, limit=None, choices=()):
    return dict(name=name, label=label, kind=kind, required=required, limit=limit, choices=choices)

APPLICATION_STATUSES = ('Applied', 'Screening', 'Interview', 'Offer', 'Rejected', 'Withdrawn')

ENTITIES = {
    'companies': dict(title='Companies', singular='Company', pk='company_id', label='company_name', fields=[
        field('company_name', 'Company name', required=True, limit=100),
        field('industry', 'Industry', limit=50), field('website', 'Website', 'url', limit=200),
        field('city', 'City', limit=50), field('state', 'State', limit=50), field('notes', 'Notes', 'textarea')]),
    'jobs': dict(title='Jobs', singular='Job', pk='job_id', label='job_title', fields=[
        field('job_title', 'Job title', required=True, limit=100),
        field('company_id', 'Company', 'company', required=True),
        field('job_type', 'Job type', 'select', choices=('Full-time', 'Part-time', 'Contract', 'Internship')),
        field('salary_min', 'Minimum annual salary', 'number'),
        field('salary_max', 'Maximum annual salary', 'number'),
        field('job_url', 'Job posting URL', 'url', limit=300),
        field('date_posted', 'Date posted', 'date'),
        field('requirements', 'Required skills', 'skills')]),
    'applications': dict(title='Applications', singular='Application', pk='application_id', label='job_title', fields=[
        field('job_id', 'Job', 'job', required=True),
        field('application_date', 'Application date', 'date', required=True),
        field('status', 'Status', 'select', required=True, choices=APPLICATION_STATUSES),
        field('resume_version', 'Resume version', limit=50),
        field('cover_letter_sent', 'Cover letter sent', 'checkbox'),
        field('interview_data', 'Interviews', 'interviews')]),
}
