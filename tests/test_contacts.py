from unittest.mock import Mock
import pytest
from mysql.connector import IntegrityError
from app import create_app
from services.entities import ENTITIES
from services.validation import validate

FIELDS = ENTITIES['contacts']['fields']
COMPANIES = [{'company_id': 1, 'company_name': 'Example Co'}]
CONTACT = dict(contact_id=4, company_id=1, contact_name='Pat Smith', title='Recruiter',
               email='pat@example.com', phone='+1 (555) 010-1234',
               linkedin_url='https://www.linkedin.com/in/example', notes='Met at career fair')
BASE = dict(contact_name='Pat Smith', company_id='1')

@pytest.fixture
def client(monkeypatch):
    fake = Mock()
    monkeypatch.setattr('routes.query', fake)
    return create_app({'TESTING': True, 'WTF_CSRF_ENABLED': False}).test_client(), fake

@pytest.mark.parametrize('changes', [
    {'contact_name': ''}, {'contact_name': 'x' * 101}, {'company_id': ''},
    {'company_id': 'abc'}, {'company_id': '-1'}, {'email': 'not-an-email'},
    {'email': 'person@'}, {'email': 'a b@example.com'}, {'email': 'a@@example.com'},
    {'title': 'x' * 101}, {'phone': '1' * 21}, {'linkedin_url': 'javascript:alert(1)'},
    {'linkedin_url': 'https://' + 'x' * 200},
])
def test_invalid_values(changes):
    assert validate(FIELDS, {**BASE, **changes})[1]

def test_optional_fields_and_international_phone():
    values, errors = validate(FIELDS, BASE)
    assert not errors
    assert values['email'] is None
    assert values['notes'] is None
    values, errors = validate(FIELDS, {**BASE, 'phone': '+44 20 7946 0000', 'email': 'pat+jobs@example.co.uk'})
    assert not errors
    assert values['phone'] == '+44 20 7946 0000'

def test_create(client):
    browser, db = client
    db.side_effect = [COMPANIES, 4]
    response = browser.post('/contacts/new', data={**BASE, 'email': 'pat@example.com'})
    assert response.status_code == 302
    assert response.location.endswith('/contacts/4')
    sql, params = db.call_args.args
    assert sql.startswith('INSERT INTO contacts')
    assert params[:2] == ('Pat Smith', 1)
    assert params[3] == 'pat@example.com'

def test_form_company_selection(client):
    browser, db = client
    db.return_value = COMPANIES
    response = browser.get('/contacts/new')
    assert response.status_code == 200
    assert b'Example Co' in response.data
    assert b'type="email"' in response.data
    assert b'type="tel"' in response.data

def test_company_prerequisite(client):
    browser, db = client
    db.return_value = []
    response = browser.get('/contacts/new')
    assert response.status_code == 200
    assert b'before saving a contact' in response.data

def test_unknown_company(client):
    browser, db = client
    db.return_value = COMPANIES
    response = browser.post('/contacts/new', data={**BASE, 'company_id': '99'})
    assert response.status_code == 422
    assert db.call_count == 1

def test_company_removed_during_save(client):
    browser, db = client
    db.side_effect = [COMPANIES, IntegrityError('foreign key')]
    response = browser.post('/contacts/new', data=BASE)
    assert response.status_code == 422
    assert b'Choose another company' in response.data

def test_invalid_form_preserves_input(client):
    browser, db = client
    db.return_value = COMPANIES
    response = browser.post('/contacts/new', data={**BASE, 'email': 'invalid', 'notes': 'Follow up next week'})
    assert response.status_code == 422
    assert b'Follow up next week' in response.data
    assert b'value="invalid"' in response.data
    assert b'value="1" selected' in response.data
    assert db.call_count == 1

def test_list_with_search(client):
    browser, db = client
    db.return_value = [{**CONTACT, 'company_name': 'Example Co'}]
    response = browser.get('/contacts?q=Pat')
    assert response.status_code == 200
    assert b'Pat Smith' in response.data
    assert b'Example Co' in response.data
    sql, params = db.call_args.args
    assert 'JOIN companies' in sql
    assert 'WHERE contact_name LIKE %s' in sql
    assert params == ('%Pat%',)

def test_detail(client):
    browser, db = client
    db.side_effect = [[CONTACT.copy()], COMPANIES]
    response = browser.get('/contacts/4')
    assert response.status_code == 200
    assert b'Example Co' in response.data
    assert b'pat@example.com' in response.data
    assert b'Met at career fair' in response.data
    assert b'href="https://www.linkedin.com/in/example"' in response.data

def test_edit_restores_fields(client):
    browser, db = client
    db.side_effect = [[CONTACT.copy()], COMPANIES]
    response = browser.get('/contacts/4/edit')
    assert response.status_code == 200
    assert b'value="1" selected' in response.data
    assert b'value="Pat Smith"' in response.data
    assert b'Met at career fair' in response.data

def test_update(client):
    browser, db = client
    db.side_effect = [[CONTACT.copy()], COMPANIES, None]
    response = browser.post('/contacts/4/edit', data={**BASE, 'title': 'Senior recruiter'})
    assert response.status_code == 302
    assert db.call_args.args[0].startswith('UPDATE contacts')
    assert db.call_args.args[1][2] == 'Senior recruiter'
    assert db.call_args.args[1][-1] == 4

def test_delete_confirmation_is_read_only(client):
    browser, db = client
    db.return_value = [CONTACT.copy()]
    response = browser.get('/contacts/4/delete')
    assert response.status_code == 200
    assert b'Pat Smith' in response.data
    assert db.call_count == 1
    assert not db.call_args.kwargs.get('write')

def test_delete(client):
    browser, db = client
    db.side_effect = [[CONTACT.copy()], None]
    response = browser.post('/contacts/4/delete')
    assert response.status_code == 302
    assert response.location.endswith('/contacts')
    assert db.call_args.args == ('DELETE FROM contacts WHERE contact_id = %s', (4,))

def test_missing_contact(client):
    browser, db = client
    db.return_value = []
    assert browser.get('/contacts/404').status_code == 404
