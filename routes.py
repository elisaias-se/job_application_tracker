import json
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from mysql.connector import IntegrityError
from database import query
from services.entities import ENTITIES, APPLICATION_STATUSES
from services.validation import validate, interview_rows
from services.dashboard import dashboard_data
from services.matching import normalize_skills, rank_jobs

bp = Blueprint('main', __name__)

@bp.route('/')
def dashboard():
    return render_template('dashboard.html', title='Overview', **dashboard_data())

def entity_config(entity):
    if entity not in ENTITIES:
        abort(404)
    return ENTITIES[entity]

def get_record(entity, record_id):
    config = entity_config(entity)
    sql = ('SELECT applications.*, jobs.job_title FROM applications JOIN jobs USING (job_id) WHERE application_id = %s'
           if entity == 'applications' else f'SELECT * FROM {entity} WHERE {config["pk"]} = %s')
    records = query(sql, (record_id,))
    if not records:
        abort(404)
    record = records[0]
    if entity == 'jobs':
        skills = record.get('requirements') or []
        if isinstance(skills, str):
            skills = json.loads(skills)
        record['requirements'] = ', '.join(skills)
    if entity == 'applications':
        interviews = record.get('interview_data') or []
        record['interview_data'] = json.loads(interviews) if isinstance(interviews, str) else interviews
    return record

@bp.route('/<entity>')
def list_records(entity):
    config = entity_config(entity)
    search = request.args.get('q', '').strip()
    selected_status = request.args.get('status', '') if entity == 'applications' else ''
    if selected_status and selected_status not in APPLICATION_STATUSES:
        abort(400)
    if entity == 'applications':
        sql = ('SELECT applications.*, jobs.job_title, companies.company_name FROM applications '
               'JOIN jobs USING (job_id) JOIN companies USING (company_id)')
    elif entity in ('jobs', 'contacts'):
        sql = f'SELECT {entity}.*, companies.company_name FROM {entity} JOIN companies USING (company_id)'
    else:
        sql = f'SELECT * FROM {entity}'
    conditions, params = [], []
    if search:
        conditions.append(f'{config["label"]} LIKE %s')
        params.append(f'%{search}%')
    if selected_status:
        conditions.append('status = %s')
        params.append(selected_status)
    if conditions:
        sql += ' WHERE ' + ' AND '.join(conditions)
    order = ('application_date DESC, application_id DESC' if entity == 'applications'
             else f'{config["label"]}, {config["pk"]}')
    rows = query(sql + ' ORDER BY ' + order, tuple(params))
    return render_template('records.html', title=config['title'], entity=entity, config=config,
                           rows=rows, search=search, selected_status=selected_status,
                           statuses=APPLICATION_STATUSES)

@bp.route('/<entity>/<int:record_id>')
def detail(entity, record_id):
    config = entity_config(entity)
    record = get_record(entity, record_id)
    if entity in ('jobs', 'contacts'):
        company = get_record('companies', record['company_id'])
        record['company_id'] = company['company_name']
    if entity == 'applications':
        job = get_record('jobs', record['job_id'])
        company = get_record('companies', job['company_id'])
        record['job_title'] = job['job_title']
        record['job_id'] = job['job_title'] + ' · ' + company['company_name']
    return render_template('detail.html', title=config['singular'], entity=entity, config=config, record=record)

@bp.route('/<entity>/new', methods=['GET', 'POST'])
@bp.route('/<entity>/<int:record_id>/edit', methods=['GET', 'POST'])
def edit_record(entity, record_id=None):
    config = entity_config(entity)
    record = get_record(entity, record_id) if record_id is not None else {}
    if entity == 'applications' and record_id is None:
        record = {'status': 'Applied', 'interview_data': []}
    errors = []
    companies = query('SELECT company_id, company_name FROM companies ORDER BY company_name') if entity in ('jobs', 'contacts') else []
    jobs = query('SELECT jobs.job_id, jobs.job_title, companies.company_name FROM jobs JOIN companies USING (company_id) ORDER BY job_title, company_name, job_id') if entity == 'applications' else []
    interviews = record.get('interview_data', [])
    if request.method == 'POST':
        values, errors = validate(config['fields'], request.form)
        if entity in ('jobs', 'contacts') and values.get('company_id') not in {c['company_id'] for c in companies}:
            errors.append('Select an existing company. Add a company first if necessary.')
        if entity == 'applications':
            interviews = interview_rows(request.form)
            if values.get('job_id') not in {job['job_id'] for job in jobs}:
                errors.append('Select an existing job. Add a job first if necessary.')
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
                errors.append('The selected job is no longer available. Choose another job.' if entity == 'applications' else 'The selected company is no longer available. Choose another company.')
            if not errors:
                flash(f'{config["singular"]} saved.', 'success')
                return redirect(url_for('main.detail', entity=entity, record_id=record_id))
        record = request.form.to_dict()
    return render_template('form.html', title=('Edit ' if record_id else 'Add ') + config['singular'], entity=entity, config=config, record=record, errors=errors, companies=companies, jobs=jobs, interviews=interviews), (422 if errors else 200)

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


@bp.route('/match')
def job_match():
    skills = request.args.get('skills', '')
    submitted = 'skills' in request.args
    errors, results = [], []
    if submitted:
        if len(skills) > 5000:
            errors.append('Enter no more than 5,000 characters of skills.')
        elif not normalize_skills(skills):
            errors.append('Enter at least one skill to find matching jobs.')
        else:
            jobs = query('SELECT jobs.*, companies.company_name FROM jobs JOIN companies USING (company_id)')
            results = rank_jobs(jobs, skills)
    return render_template('job_match.html', title='Job match', skills=skills,
                           submitted=submitted, results=results, errors=errors), (422 if errors else 200)
