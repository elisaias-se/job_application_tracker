import json
from copy import deepcopy
from unittest.mock import Mock
import pytest
from app import create_app
from services.matching import normalize_skills, rank_jobs


def job(job_id=1, requirements=None, **kwargs):
    return dict(job_id=job_id, job_title='Developer', company_name='Example Co',
                requirements=requirements, **kwargs)


def test_normalization():
    assert normalize_skills(' Python, SQL, python, , Flask ') == ['Python', 'SQL', 'Flask']
    assert normalize_skills([' C++ ', 'C#', 'c++', '', None]) == ['C++', 'C#']
    assert normalize_skills(None) == []


def test_specification_examples():
    results = rank_jobs([job(1, ['Python', 'SQL', 'Flask']),
                         job(2, json.dumps(['Python', 'SQL', 'Tableau']))], 'Python, SQL, Flask')
    assert [r['percentage'] for r in results] == [100, 67]
    assert results[0]['missing'] == []
    assert results[1]['matched'] == ['Python', 'SQL']
    assert results[1]['missing'] == ['Tableau']


def test_denominator_is_required_skills_and_duplicates_do_not_inflate_score():
    result = rank_jobs([job(requirements=['Python', 'PYTHON', 'SQL'])], 'python, python, Flask, Git')[0]
    assert result['required_count'] == 2
    assert result['percentage'] == 50


def test_exact_names_preserve_distinct_technologies():
    result = rank_jobs([job(requirements=['SQL', 'C++', 'C#'])], 'MySQL, C')[0]
    assert result['percentage'] == 0
    assert result['missing'] == ['SQL', 'C++', 'C#']


@pytest.mark.parametrize('requirements', [None, [], '[]', '{}', 'null', 'bad-json', [' ', None], '"Python"'])
def test_jobs_without_skill_arrays_are_unscored(requirements):
    result = rank_jobs([job(requirements=requirements)], 'Python')[0]
    assert result['percentage'] is None
    assert result['required_count'] == 0


def test_zero_matches_before_unscored():
    results = rank_jobs([job(1), job(2, ['SQL']), job(3, ['Python'])], 'Python')
    assert [r['job_id'] for r in results] == [3, 2, 1]
    assert [r['percentage'] for r in results] == [100, 0, None]


def test_rank_uses_unrounded_scores():
    # Both display 67%, but 67/100 must rank ahead of 2/3.
    skills = [f'skill{i}' for i in range(100)]
    results = rank_jobs([job(1, skills[:3]), job(2, skills)], skills[:2] + skills[3:68])
    assert [r['percentage'] for r in results] == [67, 67]
    assert [r['job_id'] for r in results] == [2, 1]


def test_ties_are_stable_and_inputs_unchanged():
    jobs = [job(3, ['SQL'], **{'job_type': 'Contract'}), job(1, ['SQL'])]
    before = deepcopy(jobs)
    assert [r['job_id'] for r in rank_jobs(jobs, 'SQL')] == [1, 3]
    assert jobs == before


def test_empty_skills_do_not_divide_by_zero():
    assert rank_jobs([job(requirements=['Python'])], '')[0]['percentage'] == 0
    assert rank_jobs([], 'Python') == []


@pytest.fixture
def client(monkeypatch):
    fake = Mock(return_value=[])
    monkeypatch.setattr('routes.query', fake)
    return create_app({'TESTING': True}).test_client(), fake


def test_initial_page_does_not_query_database(client):
    browser, db = client
    response = browser.get('/match')
    assert response.status_code == 200
    assert b'Your skills' in response.data
    db.assert_not_called()


@pytest.mark.parametrize('skills', ['', ' , , ', 'x' * 5001])
def test_invalid_skills(client, skills):
    browser, db = client
    assert browser.get('/match', query_string={'skills': skills}).status_code == 422
    db.assert_not_called()


def test_results_page(client):
    browser, db = client
    db.return_value = [job(1, ['Python', 'SQL', 'Tableau']), job(2)]
    response = browser.get('/match?skills=Python,SQL')
    assert response.status_code == 200
    for text in (b'67%', b'2/3 skills', b'Tableau', b'Requirements not specified', b'href="/jobs/1"'):
        assert text in response.data
    assert not db.call_args.kwargs.get('write')


def test_empty_results(client):
    browser, db = client
    response = browser.get('/match?skills=Python')
    assert response.status_code == 200
    assert b'No saved jobs yet' in response.data


def test_html_is_escaped(client):
    browser, db = client
    db.return_value = [job(requirements=['<script>alert(1)</script>'])]
    response = browser.get('/match', query_string={'skills': '<script>alert(1)</script>'})
    assert response.status_code == 200
    assert b'<script>alert' not in response.data
    assert b'&lt;script&gt;' in response.data
