"""Allowlisted entity definitions shared by forms and SQL builders."""
def field(name, label, kind='text', required=False, limit=None, choices=()):
    return dict(name=name, label=label, kind=kind, required=required, limit=limit, choices=choices)

ENTITIES = {
    'companies': dict(title='Companies', singular='Company', pk='company_id', label='company_name', fields=[
        field('company_name', 'Company name', required=True, limit=100),
        field('industry', 'Industry', limit=50), field('website', 'Website', 'url', limit=200),
        field('city', 'City', limit=50), field('state', 'State', limit=50), field('notes', 'Notes', 'textarea')]),
}
