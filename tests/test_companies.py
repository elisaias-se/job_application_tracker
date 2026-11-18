from unittest.mock import Mock
import pytest
from mysql.connector import IntegrityError
from app import create_app
from services.entities import ENTITIES
from services.validation import validate

@pytest.fixture
def client(monkeypatch):
    app = create_app({'TESTING': True, 'WTF_CSRF_ENABLED': False})
    fake = Mock(return_value=[])
    monkeypatch.setattr('routes.query', fake)
    return app.test_client(), fake

def test_company_validation():
    fields = ENTITIES['companies']['fields']
    assert validate(fields, {'company_name': '  Acme  '}) == ({'company_name': 'Acme', 'industry': None, 'website': None, 'city': None, 'state': None, 'notes': None}, [])
    assert validate(fields, {'company_name': '', 'website': 'javascript:alert(1)'})[1]
    assert validate(fields, {'company_name': 'x' * 101})[1]

def test_create_uses_bound_parameters(client):
    browser, db = client
    db.return_value = 7
    response = browser.post('/companies/new', data={'company_name': "O'Reilly"})
    assert response.status_code == 302
    assert response.location.endswith('/companies/7')
    sql, params = db.call_args.args
    assert "O'Reilly" not in sql
    assert params[0] == "O'Reilly"

def test_invalid_form_preserves_values(client):
    browser, db = client
    response = browser.post('/companies/new', data={'company_name': '', 'website': 'bad-url'})
    assert response.status_code == 422
    assert b'bad-url' in response.data
    db.assert_not_called()

def test_edit(client):
    browser, db = client
    db.side_effect = [[{'company_id': 3, 'company_name': 'Before'}], None]
    response = browser.post('/companies/3/edit', data={'company_name': 'After'})
    assert response.status_code == 302
    assert db.call_args.args[0].startswith('UPDATE companies')
    assert db.call_args.args[1][-1] == 3

def test_detail_escapes_html(client):
    browser, db = client
    db.return_value = [{'company_id': 1, 'company_name': '<script>alert(1)</script>'}]
    response = browser.get('/companies/1')
    assert response.status_code == 200
    assert b'<script>alert' not in response.data
    assert b'&lt;script&gt;' in response.data

def test_list_search_is_parameterized(client):
    browser, db = client
    assert browser.get('/companies?q=Acme').status_code == 200
    assert db.call_args.args[1] == ('%Acme%',)

def test_missing_and_unknown_records(client):
    browser, db = client
    assert browser.get('/companies/99').status_code == 404
    assert browser.get('/unknown').status_code == 404

def test_delete_get_is_read_only(client):
    browser, db = client
    db.return_value = [{'company_id': 1, 'company_name': 'Acme'}]
    assert browser.get('/companies/1/delete').status_code == 200
    assert db.call_count == 1
    assert not db.call_args.kwargs.get('write')

def test_delete_restricts_dependents(client):
    browser, db = client
    db.side_effect = [[{'company_id': 1, 'company_name': 'Acme'}], IntegrityError('dependent records')]
    assert browser.post('/companies/1/delete').status_code == 302
    with browser.session_transaction() as session:
        assert 'dependent' in session['_flashes'][0][1]

def test_csrf_required():
    browser = create_app({'TESTING': True}).test_client()
    assert browser.post('/companies/new', data={'company_name': 'Acme'}).status_code == 400
