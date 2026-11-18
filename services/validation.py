"""Server-side validation independent of browser constraints."""
from urllib.parse import urlsplit
from datetime import date, datetime
import json
import re

def validate(fields, form):
    values, errors = {}, []
    for field in fields:
        name, label = field['name'], field['label']
        raw = form.get(name, '').strip()
        if field['required'] and not raw:
            errors.append(f'{label} is required.')
        if field['limit'] and len(raw) > field['limit']:
            errors.append(f'{label} must be at most {field["limit"]} characters.')
        if field['kind'] == 'url' and raw:
            try:
                parts = urlsplit(raw)
                if parts.scheme not in ('http', 'https') or not parts.hostname:
                    raise ValueError
            except ValueError:
                errors.append(f'{label} must be an http:// or https:// URL.')
        if field['kind'] == 'email' and raw and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', raw):
            errors.append(f'{label} must be a valid email address.')
        value = raw or None
        if field['kind'] in ('number', 'company', 'job') and raw:
            minimum = 1 if field['kind'] in ('company', 'job') else 0
            try:
                value = int(raw)
                if not minimum <= value <= 2147483647:
                    raise ValueError
            except ValueError:
                errors.append(f'{label} must be a whole number between {minimum} and 2147483647.')
                value = None
        if field['kind'] == 'select' and raw and raw not in field['choices']:
            errors.append(f'{label} is not a valid option.')
        if field['kind'] == 'date' and raw:
            try:
                value = date.fromisoformat(raw).isoformat()
            except ValueError:
                errors.append(f'{label} must be a valid date.')
        if field['kind'] == 'skills':
            skills = {}
            for skill in raw.split(','):
                skill = skill.strip()
                if skill:
                    skills.setdefault(skill.casefold(), skill)
            value = json.dumps(list(skills.values()))
        if field['kind'] == 'checkbox':
            value = raw in ('on', '1')
        if field['kind'] == 'interviews':
            interviews = interview_rows(form)
            for index, interview in enumerate(interviews, 1):
                try:
                    datetime.fromisoformat(interview['date'])
                except ValueError:
                    errors.append(f'Interview {index} needs a valid date and time.')
                if interview['format'] not in ('Phone', 'Video', 'In-person', 'Other'):
                    errors.append(f'Interview {index} needs a valid format.')
            value = json.dumps(interviews)
        values[name] = value
    low, high = values.get('salary_min'), values.get('salary_max')
    if isinstance(low, int) and isinstance(high, int) and low > high:
        errors.append('Minimum salary cannot exceed maximum salary.')
    return values, errors


def interview_rows(form):
    """Read repeated interview inputs, keeping incomplete rows for validation."""
    names = ('date', 'format', 'interviewer', 'notes')
    columns = [form.getlist('interview_' + name) for name in names] if hasattr(form, 'getlist') else []
    rows = []
    for index in range(max((len(column) for column in columns), default=0)):
        row = {name: (columns[i][index].strip() if index < len(columns[i]) else '')
               for i, name in enumerate(names)}
        if any(row.values()):
            rows.append(row)
    return rows
