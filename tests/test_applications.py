import json
from unittest.mock import Mock
import pytest
from werkzeug.datastructures import MultiDict
from mysql.connector import IntegrityError
from app import create_app
from services.entities import ENTITIES, APPLICATION_STATUSES
from services.validation import validate

FIELDS = ENTITIES['applications']['fields']
JOBS = [{'job_id': 2, 'job_title': 'Developer', 'company_name': 'Example Co'}]
APPLICATION = dict(application_id=3, job_id=2, job_title='Developer',
                   application_date='2026-11-18', status='Applied', resume_version='v1',
                   cover_letter_sent=False, interview_data='[]')
BASE = dict(job_id='2', application_date='2026-11-18', status='Applied')

@pytest.fixture
def client(monkeypatch):
    fake = Mock()
    monkeypatch.setattr('routes.query', fake)
    return create_app({'TESTING': True, 'WTF_CSRF_ENABLED': False}).test_client(), fake

@pytest.mark.parametrize('status', APPLICATION_STATUSES)
def test_status_values(status):
    values, errors = validate(FIELDS, {**BASE, 'status': status})
    assert not errors
    assert values['status'] == status

@pytest.mark.parametrize('changes', [
    {'job_id': ''}, {'job_id': '-1'}, {'job_id': 'bad'},
    {'application_date': ''}, {'application_date': '2026-02-30'},
    {'status': ''}, {'status': 'Hired'}, {'resume_version': 'x' * 51},
])
def test_validation(changes):
    assert validate(FIELDS, {**BASE, **changes})[1]

def test_optional_fields_and_checkbox():
    values, errors = validate(FIELDS, BASE)
    assert not errors
    assert values['resume_version'] is None
    assert values['cover_letter_sent'] is False
    assert json.loads(values['interview_data']) == []
    assert validate(FIELDS, {**BASE, 'cover_letter_sent': '1'})[0]['cover_letter_sent'] is True

def test_multiple_interviews():
    form = MultiDict(BASE)
    for when, format, person, note in [('2026-11-20T09:00', 'Video', 'Pat', 'Technical'),
                                     ('2026-11-22T13:30', 'Phone', 'Sam', 'Follow-up')]:
        for key, value in zip(('date', 'format', 'interviewer', 'notes'), (when, format, person, note)):
            form.add('interview_' + key, value)
    values, errors = validate(FIELDS, form)
    assert not errors
    interviews = json.loads(values['interview_data'])
    assert len(interviews) == 2
    assert interviews[1]['interviewer'] == 'Sam'

def test_partial_interview_rejected_and_preserved(client):
    browser, db = client
    db.return_value = JOBS
    response = browser.post('/applications/new', data={**BASE, 'interview_notes': 'Bring portfolio'})
    assert response.status_code == 422
    assert b'Bring portfolio' in response.data
    assert b'valid date and time' in response.data
    assert db.call_count == 1

def test_create(client):
    browser, db = client
    db.side_effect = [JOBS, 3]
    response = browser.post('/applications/new', data={**BASE, 'cover_letter_sent': '1'})
    assert response.status_code == 302
    assert response.location.endswith('/applications/3')
    sql, params = db.call_args.args
    assert sql.startswith('INSERT INTO applications')
    assert params[0] == 2
    assert params[-2] is True
    assert json.loads(params[-1]) == []

def test_unknown_job(client):
    browser, db = client
    db.return_value = JOBS
    assert browser.post('/applications/new', data={**BASE, 'job_id': '99'}).status_code == 422
    assert db.call_count == 1

def test_job_removed_during_create(client):
    browser, db = client
    db.side_effect = [JOBS, IntegrityError('foreign key')]
    response = browser.post('/applications/new', data=BASE)
    assert response.status_code == 422
    assert b'Choose another job' in response.data

def test_new_form_defaults(client):
    browser, db = client
    db.return_value = JOBS
    response = browser.get('/applications/new')
    assert response.status_code == 200
    assert b'<option value="Applied" selected>' in response.data
    assert b'Developer' in response.data
    assert b'Example Co' in response.data
    assert b'interviews.js' in response.data

def test_new_form_without_jobs(client):
    browser, db = client
    db.return_value = []
    response = browser.get('/applications/new')
    assert response.status_code == 200
    assert b'before saving an application' in response.data

def test_edit_restores_interviews(client):
    browser, db = client
    record = {**APPLICATION, 'interview_data': json.dumps([dict(date='2026-11-20T09:00', format='Video', interviewer='Pat', notes='Portfolio')])}
    db.side_effect = [[record], JOBS]
    response = browser.get('/applications/3/edit')
    assert response.status_code == 200
    assert b'Portfolio' in response.data
    assert b'value="2026-11-20T09:00"' in response.data
    assert b'value="2" selected' in response.data

def test_update(client):
    browser, db = client
    db.side_effect = [[APPLICATION.copy()], JOBS, None]
    response = browser.post('/applications/3/edit', data={**BASE, 'status': 'Interview'})
    assert response.status_code == 302
    assert db.call_args.args[0].startswith('UPDATE applications')
    assert db.call_args.args[1][-1] == 3

def test_search_and_status_filter(client):
    browser, db = client
    db.return_value = [{**APPLICATION, 'company_name': 'Example Co'}]
    response = browser.get('/applications?q=Developer&status=Applied')
    assert response.status_code == 200
    assert b'Developer' in response.data
    assert b'Example Co' in response.data
    sql, params = db.call_args.args
    assert 'JOIN jobs' in sql
    assert 'application_date DESC' in sql
    assert params == ('%Developer%', 'Applied')

def test_invalid_filter(client):
    browser, db = client
    assert browser.get('/applications?status=Invalid').status_code == 400
    db.assert_not_called()

def test_detail(client):
    browser, db = client
    db.side_effect = [[APPLICATION.copy()], [dict(job_id=2, company_id=1, job_title='Developer', requirements='[]')], [dict(company_id=1, company_name='Example Co')]]
    response = browser.get('/applications/3')
    assert response.status_code == 200
    assert b'Example Co' in response.data
    assert b'No interviews scheduled' in response.data
    assert b'No</dd>' in response.data

def test_delete_confirmation_and_write(client):
    browser, db = client
    db.return_value = [APPLICATION.copy()]
    response = browser.get('/applications/3/delete')
    assert response.status_code == 200
    assert b'Developer' in response.data
    assert db.call_count == 1
    db.reset_mock()
    db.side_effect = [[APPLICATION.copy()], None]
    assert browser.post('/applications/3/delete').status_code == 302
    assert db.call_args.args == ('DELETE FROM applications WHERE application_id = %s', (3,))
