from datetime import date
from unittest.mock import Mock
import pytest
from mysql.connector import OperationalError
from app import create_app
from services.dashboard import dashboard_data
from services.entities import APPLICATION_STATUSES


@pytest.fixture
def db(monkeypatch):
    fake = Mock()
    monkeypatch.setattr('services.dashboard.query', fake)
    return fake


def test_empty_dashboard_data(db):
    db.side_effect = [[dict(companies=0, jobs=0, applications=0, contacts=0)], [], []]
    data = dashboard_data()
    assert data['counts']['applications'] == 0
    assert data['recent'] == []
    assert data['statuses'] == [{'name': name, 'count': 0} for name in APPLICATION_STATUSES]


def test_statuses_fill_missing_categories_in_order(db):
    db.side_effect = [[dict(companies=2, jobs=3, applications=4, contacts=1)],
                      [dict(status='Offer', count=1), dict(status='Applied', count=3)], []]
    data = dashboard_data()
    assert [status['name'] for status in data['statuses']] == list(APPLICATION_STATUSES)
    assert [status['count'] for status in data['statuses']] == [3, 0, 0, 1, 0, 0]
    assert data['counts']['jobs'] == 3


def test_dashboard_empty_state(db):
    db.side_effect = [[dict(companies=0, jobs=0, applications=0, contacts=0)], [], []]
    client = create_app({'TESTING': True}).test_client()
    response = client.get('/')
    assert response.status_code == 200
    assert b'No applications yet' in response.data
    assert b'max="1"' in response.data
    assert b'href="/applications/new"' in response.data
    for status in APPLICATION_STATUSES:
        assert f'aria-label="{status}: 0 of 0 applications"'.encode() in response.data


def test_dashboard_populated(db):
    db.side_effect = [[dict(companies=2, jobs=8, applications=12, contacts=3)],
                      [dict(status='Interview', count=12)],
                      [dict(application_id=9, job_title='Python developer', company_name='Example Co',
                            application_date=date(2026, 11, 18), status='Interview')]]
    response = create_app({'TESTING': True}).test_client().get('/')
    assert response.status_code == 200
    for text in (b'Python developer', b'Example Co', b'2026-11-18', b'href="/applications/9"',
                 b'aria-label="Interview: 12 of 12 applications"', b'<strong>8</strong>'):
        assert text in response.data
    assert b'No applications yet' not in response.data


def test_recent_query_has_stable_order_and_limit(db):
    db.side_effect = [[dict(companies=0, jobs=0, applications=0, contacts=0)], [], []]
    dashboard_data()
    sql = db.call_args.args[0]
    assert 'JOIN jobs USING (job_id)' in sql
    assert 'JOIN companies USING (company_id)' in sql
    assert 'application_date DESC, applications.application_id DESC' in sql
    assert 'LIMIT 5' in sql
    assert all(not call.kwargs.get('write') for call in db.call_args_list)


def test_dashboard_escapes_record_names(db):
    db.side_effect = [[dict(companies=1, jobs=1, applications=1, contacts=0)], [],
                      [dict(application_id=1, job_title='<script>alert(1)</script>',
                            company_name='A & B', application_date='2026-11-18', status='Applied')]]
    response = create_app({'TESTING': True}).test_client().get('/')
    assert b'<script>alert' not in response.data
    assert b'&lt;script&gt;' in response.data
    assert b'A &amp; B' in response.data


def test_dashboard_database_unavailable(db):
    db.side_effect = OperationalError('Cannot connect')
    response = create_app({'TESTING': True}).test_client().get('/')
    assert response.status_code == 503
    assert b'Database unavailable' in response.data
    assert b'Cannot connect' not in response.data
