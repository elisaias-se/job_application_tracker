import json
from unittest.mock import Mock
import pytest
from mysql.connector import IntegrityError
from app import create_app
from services.entities import ENTITIES
from services.validation import validate

FIELDS = ENTITIES['jobs']['fields']
COMPANIES = [{'company_id': 1, 'company_name': 'Example Co'}]
JOB = dict(job_id=2, company_id=1, job_title='Developer', job_type='Full-time',
           salary_min=0, salary_max=100000, job_url=None, date_posted=None,
           requirements='["Python", "SQL"]')

@pytest.fixture
def client(monkeypatch):
    fake = Mock()
    monkeypatch.setattr('routes.query', fake)
    return create_app({'TESTING': True, 'WTF_CSRF_ENABLED': False}).test_client(), fake

@pytest.mark.parametrize('changes', [
    {'salary_min': '-1'}, {'salary_max': '2147483648'}, {'salary_min': 'abc'},
    {'salary_min': '1.5'}, {'salary_min': '900', 'salary_max': '100'},
    {'date_posted': '2026-02-30'}, {'job_type': 'Unknown'}, {'company_id': 'no'},
    {'company_id': '0'}, {'job_url': 'javascript:alert(1)'}, {'job_title': ''},
])
def test_invalid_values(changes):
    _, errors = validate(FIELDS, {'job_title': 'Developer', 'company_id': '1', **changes})
    assert errors

def test_skills_and_zero_salary():
    values, errors = validate(FIELDS, {'job_title': 'Developer', 'company_id': '1',
        'requirements': ' Python, SQL, python, , Flask ', 'salary_min': '0'})
    assert not errors
    assert values['salary_min'] == 0
    assert values['company_id'] == 1
    assert json.loads(values['requirements']) == ['Python', 'SQL', 'Flask']

def test_create(client):
    browser, db = client
    db.side_effect = [COMPANIES, 2]
    response = browser.post('/jobs/new', data={'job_title': 'Developer', 'company_id': '1', 'requirements': 'Python, SQL'})
    assert response.status_code == 302
    assert response.location.endswith('/jobs/2')
    sql, params = db.call_args.args
    assert sql.startswith('INSERT INTO jobs')
    assert json.loads(params[-1]) == ['Python', 'SQL']

def test_missing_company(client):
    browser, db = client
    db.return_value = COMPANIES
    response = browser.post('/jobs/new', data={'job_title': 'Developer', 'company_id': '99'})
    assert response.status_code == 422
    assert b'Select an existing company' in response.data
    assert db.call_count == 1

def test_company_deleted_before_save(client):
    browser, db = client
    db.side_effect = [COMPANIES, IntegrityError('foreign key')]
    response = browser.post('/jobs/new', data={'job_title': 'Developer', 'company_id': '1'})
    assert response.status_code == 422
    assert b'no longer available' in response.data

def test_edit_restores_json_and_zero(client):
    browser, db = client
    db.side_effect = [[JOB.copy()], COMPANIES]
    response = browser.get('/jobs/2/edit')
    assert response.status_code == 200
    assert b'Python, SQL' in response.data
    assert b'value="0"' in response.data
    assert b'value="1" selected' in response.data

def test_update(client):
    browser, db = client
    db.side_effect = [[JOB.copy()], COMPANIES, None]
    response = browser.post('/jobs/2/edit', data={'job_title': 'Senior developer', 'company_id': '1'})
    assert response.status_code == 302
    assert db.call_args.args[0].startswith('UPDATE jobs')
    assert db.call_args.args[1][-1] == 2

def test_list_shows_company_name(client):
    browser, db = client
    db.return_value = [{**JOB, 'company_name': 'Example Co'}]
    response = browser.get('/jobs')
    assert response.status_code == 200
    assert b'Example Co' in response.data
    assert 'JOIN companies' in db.call_args.args[0]

def test_detail_shows_company_and_skills(client):
    browser, db = client
    db.side_effect = [[JOB.copy()], COMPANIES]
    response = browser.get('/jobs/2')
    assert response.status_code == 200
    assert b'Example Co' in response.data
    assert b'Python, SQL' in response.data

def test_delete_job(client):
    browser, db = client
    db.side_effect = [[JOB.copy()], None]
    response = browser.post('/jobs/2/delete')
    assert response.status_code == 302
    assert db.call_args.args == ('DELETE FROM jobs WHERE job_id = %s', (2,))

def test_company_prerequisite_hint(client):
    browser, db = client
    db.return_value = []
    response = browser.get('/jobs/new')
    assert response.status_code == 200
    assert b'before saving a job' in response.data
