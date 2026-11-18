"""Server-side validation independent of browser constraints."""
from urllib.parse import urlsplit

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
        values[name] = raw or None
    return values, errors
