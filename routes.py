import json
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from mysql.connector import IntegrityError
from database import query
from services.entities import ENTITIES
from services.validation import validate

bp = Blueprint('main', __name__)

@bp.route('/')
def dashboard():
    return render_template('dashboard.html')

def entity_config(entity):
    if entity not in ENTITIES:
        abort(404)
    return ENTITIES[entity]

def get_record(entity, record_id):
    config = entity_config(entity)
    records = query(f'SELECT * FROM {entity} WHERE {config["pk"]} = %s', (record_id,))
    if not records:
        abort(404)
    record = records[0]
    if entity == 'jobs':
        skills = record.get('requirements') or []
        if isinstance(skills, str):
            skills = json.loads(skills)
        record['requirements'] = ', '.join(skills)
    return record

@bp.route('/<entity>')
def list_records(entity):
    config = entity_config(entity)
    search = request.args.get('q', '').strip()
    sql = ("SELECT jobs.*, companies.company_name FROM jobs JOIN companies USING (company_id)"
           if entity == 'jobs' else f'SELECT * FROM {entity}')
    params = ()
    if search:
        sql += f' WHERE {config["label"]} LIKE %s'
        params = (f'%{search}%',)
    rows = query(sql + f' ORDER BY {config["label"]}, {config["pk"]}', params)
    return render_template('records.html', title=config['title'], entity=entity, config=config, rows=rows, search=search)

@bp.route('/<entity>/<int:record_id>')
def detail(entity, record_id):
    config = entity_config(entity)
    record = get_record(entity, record_id)
    if entity == 'jobs':
        company = get_record('companies', record['company_id'])
        record['company_id'] = company['company_name']
    return render_template('detail.html', title=config['singular'], entity=entity, config=config, record=record)

@bp.route('/<entity>/new', methods=['GET', 'POST'])
@bp.route('/<entity>/<int:record_id>/edit', methods=['GET', 'POST'])
def edit_record(entity, record_id=None):
    config = entity_config(entity)
    record = get_record(entity, record_id) if record_id is not None else {}
    errors = []
    companies = query('SELECT company_id, company_name FROM companies ORDER BY company_name') if entity == 'jobs' else []
    if request.method == 'POST':
        values, errors = validate(config['fields'], request.form)
        if entity == 'jobs' and values.get('company_id') not in {c['company_id'] for c in companies}:
            errors.append('Select an existing company. Add a company first if necessary.')
        if not errors:
            columns = list(values)
            params = tuple(values.values())
            try:
                if record_id is None:
                    sql = f'INSERT INTO {entity} ({", ".join(columns)}) VALUES ({", ".join(["%s"] * len(columns))})'
                    record_id = query(sql, params, write=True)
                else:
                    sql = f'UPDATE {entity} SET {", ".join(c + " = %s" for c in columns)} WHERE {config["pk"]} = %s'
                    query(sql, params + (record_id,), write=True)
            except IntegrityError:
                errors.append('The selected company is no longer available. Choose another company.')
            if not errors:
                flash(f'{config["singular"]} saved.', 'success')
                return redirect(url_for('main.detail', entity=entity, record_id=record_id))
        record = request.form.to_dict()
    return render_template('form.html', title=('Edit ' if record_id else 'Add ') + config['singular'], entity=entity, config=config, record=record, errors=errors, companies=companies), (422 if errors else 200)

@bp.route('/<entity>/<int:record_id>/delete', methods=['GET', 'POST'])
def delete_record(entity, record_id):
    config = entity_config(entity)
    record = get_record(entity, record_id)
    if request.method == 'POST':
        try:
            query(f'DELETE FROM {entity} WHERE {config["pk"]} = %s', (record_id,), write=True)
        except IntegrityError:
            flash('Remove dependent jobs, applications, or contacts before deleting this record.', 'error')
            return redirect(url_for('main.detail', entity=entity, record_id=record_id))
        flash(f'{config["singular"]} deleted.', 'success')
        return redirect(url_for('main.list_records', entity=entity))
    return render_template('delete.html', title='Delete ' + config['singular'], config=config, record=record, entity=entity)
