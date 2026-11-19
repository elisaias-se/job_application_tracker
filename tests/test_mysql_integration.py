"""Opt-in end-to-end HTTP/database tests against an isolated, disposable MySQL DB."""
import json
import os
from pathlib import Path
import re
from uuid import uuid4

import mysql.connector
import pytest
from app import create_app

pytestmark = [pytest.mark.integration,
              pytest.mark.skipif(os.getenv('MYSQL_TEST_ENABLE') != '1',
                                 reason='Set MYSQL_TEST_ENABLE=1 to run real MySQL tests.')]
ROOT = Path(__file__).resolve().parents[1]


def sql_statements(filename):
    text = '\n'.join(line for line in (ROOT / filename).read_text().splitlines()
                     if not line.lstrip().startswith(('--', 'CREATE DATABASE', 'USE ')))
    return [statement.strip() for statement in text.split(';') if statement.strip()]


@pytest.fixture(scope='module')
def mysql_app():
    # Never connect to the application database or accept a database name from the environment.
    name = 'job_tracker_test_' + uuid4().hex
    settings = dict(host=os.getenv('MYSQL_TEST_HOST', '127.0.0.1'),
                    port=int(os.getenv('MYSQL_TEST_PORT', '3306')),
                    user=os.getenv('MYSQL_TEST_USER', 'root'),
                    password=os.getenv('MYSQL_TEST_PASSWORD', ''))
    admin = mysql.connector.connect(**settings)
    cursor = admin.cursor(dictionary=True)
    cursor.execute(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    try:
        cursor.execute(f'USE `{name}`')
        for statement in sql_statements('schema.sql'):
            cursor.execute(statement)
        admin.commit()
        app = create_app(dict(TESTING=True, WTF_CSRF_ENABLED=False, SECRET_KEY='integration-test-only',
                              DB_HOST=settings['host'], DB_PORT=settings['port'],
                              DB_USER=settings['user'], DB_PASSWORD=settings['password'], DB_NAME=name))
        yield app, admin
    finally:
        cursor.execute(f'DROP DATABASE `{name}`')
        cursor.close()
        admin.close()


@pytest.fixture
def real_client(mysql_app):
    app, db = mysql_app
    db.rollback()
    cursor = db.cursor()
    for table in ('applications', 'contacts', 'jobs', 'companies'):
        cursor.execute(f'DELETE FROM {table}')
    db.commit()
    cursor.close()
    return app.test_client(), db


def scalar(db, sql):
    db.rollback()  # End any earlier read snapshot before observing HTTP writes.
    cursor = db.cursor()
    cursor.execute(sql)
    value = cursor.fetchone()[0]
    cursor.close()
    return value


def create(client, path, data):
    response = client.post(path, data=data)
    assert response.status_code == 302, response.data.decode()
    assert client.get(response.location).status_code == 200
    return response.location


def test_full_lifecycle_persists_and_restricts_deletion(real_client):
    client, db = real_client
    company = create(client, '/companies/new', dict(company_name="O'Reilly Demo", industry='Software'))
    company_id = int(company.rsplit('/', 1)[1])
    job = create(client, '/jobs/new', dict(job_title='Developer', company_id=company_id,
                 requirements='Python, SQL, Flask', salary_min=0, salary_max=100000, date_posted='2026-11-18'))
    job_id = int(job.rsplit('/', 1)[1])
    contact = create(client, '/contacts/new', dict(contact_name='Pat', company_id=company_id, email='pat@example.com'))
    application = create(client, '/applications/new', dict(job_id=job_id, application_date='2026-11-18',
                         status='Interview', cover_letter_sent='1', interview_date='2026-11-20T10:00',
                         interview_format='Video', interview_interviewer='Pat', interview_notes='Bring portfolio'))
    assert scalar(db, 'SELECT COUNT(*) FROM applications') == 1
    assert scalar(db, 'SELECT cover_letter_sent FROM applications') == 1
    assert json.loads(scalar(db, 'SELECT interview_data FROM applications'))[0]['notes'] == 'Bring portfolio'
    assert json.loads(scalar(db, 'SELECT requirements FROM jobs')) == ['Python', 'SQL', 'Flask']
    assert b'100%' in client.get('/match?skills=Python,SQL,Flask').data
    assert b'O&#39;Reilly Demo' in client.get('/').data
    for path in ('/companies', '/jobs', '/applications', '/contacts', company, job, application, contact):
        assert client.get(path).status_code == 200
    # Restriction must come from real MySQL foreign keys, not a mocked exception.
    assert client.post(company + '/delete').status_code == 302
    assert scalar(db, 'SELECT COUNT(*) FROM companies') == 1
    assert client.post(job + '/delete').status_code == 302
    assert scalar(db, 'SELECT COUNT(*) FROM jobs') == 1
    updated = client.post(application + '/edit', data=dict(job_id=job_id, application_date='2026-11-18',
                          status='Offer', resume_version='v2'))
    assert updated.status_code == 302
    assert scalar(db, 'SELECT status FROM applications') == 'Offer'
    assert json.loads(scalar(db, 'SELECT interview_data FROM applications')) == []
    for path in (application, contact, job, company):
        assert client.post(path + '/delete').status_code == 302
        assert client.get(path).status_code == 404
    for table in ('companies', 'jobs', 'applications', 'contacts'):
        assert scalar(db, f'SELECT COUNT(*) FROM {table}') == 0


def test_seed_all_pages_and_match_example(real_client):
    client, db = real_client
    cursor = db.cursor()
    for statement in sql_statements('seed.sql'):
        cursor.execute(statement)
    cursor.close()
    assert scalar(db, 'SELECT COUNT(*) FROM companies') == 3
    assert scalar(db, 'SELECT COUNT(*) FROM jobs') == 3
    assert scalar(db, 'SELECT COUNT(*) FROM applications') == 6
    for page in ('/', '/companies', '/jobs', '/applications', '/contacts', '/match?skills=Python,SQL,Flask',
                 '/applications?status=Interview', '/jobs?q=Developer'):
        assert client.get(page).status_code == 200
    results = client.get('/match?skills=Python,SQL,Flask').data
    assert b'100%' in results and b'67%' in results and b'Tableau' in results
    cursor = db.cursor()
    for table, pk in (('companies', 'company_id'), ('jobs', 'job_id'),
                      ('applications', 'application_id'), ('contacts', 'contact_id')):
        cursor.execute(f'SELECT {pk} FROM {table}')
        ids = [row[0] for row in cursor.fetchall()]
        for record_id in ids:
            for suffix in ('', '/edit', '/delete'):
                assert client.get(f'/{table}/{record_id}{suffix}').status_code == 200
    cursor.close()


def test_database_constraints_and_recovery(real_client):
    client, db = real_client
    company = create(client, '/companies/new', dict(company_name='Valid'))
    company_id = int(company.rsplit('/', 1)[1])
    cursor = db.cursor()
    with pytest.raises(mysql.connector.IntegrityError):
        cursor.execute('INSERT INTO jobs (company_id, job_title) VALUES (%s, %s)', (2147483647, 'Orphan'))
    db.rollback()
    with pytest.raises(mysql.connector.Error):
        cursor.execute('INSERT INTO jobs (company_id, job_title, salary_min, salary_max) VALUES (%s, %s, %s, %s)',
                       (company_id, 'Invalid salary', 100, 1))
    db.rollback()
    cursor.close()
    assert client.get('/companies').status_code == 200


def test_csrf_round_trip_with_real_database(real_client, mysql_app):
    _, db = real_client
    app, _ = mysql_app
    app.config['WTF_CSRF_ENABLED'] = True
    try:
        client = app.test_client()
        assert client.post('/companies/new', data={'company_name': 'No token'}).status_code == 400
        form = client.get('/companies/new')
        token = re.search(rb'name="csrf_token" value="([^"]+)"', form.data).group(1).decode()
        assert client.post('/companies/new', data={'company_name': 'With token', 'csrf_token': token}).status_code == 302
        assert scalar(db, 'SELECT COUNT(*) FROM companies') == 1
    finally:
        app.config['WTF_CSRF_ENABLED'] = False
