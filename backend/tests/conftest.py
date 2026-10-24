import os
import base64
import pytest
from dotenv import load_dotenv
from mongoengine.connection import get_connection

load_dotenv()

# The application is pointed at a throwaway database BEFORE it is built, so a
# test run can never touch development data (TMA Q4b). app/config.py reads the
# database name from the environment at import time, which is both what makes
# this possible and why this assignment has to happen above the import below.
TEST_DB = os.getenv('MONGODB_TEST_DB', 'skipq_test')
os.environ['MONGODB_DB'] = TEST_DB

from app import create_app  # noqa: E402


@pytest.fixture(scope='session')
def app():
    application = create_app()
    with application.app_context():
        yield application
        get_connection().drop_database(TEST_DB)


@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def seeded(app):
    """Builds the test database from db_seed/seed.py rather than a second set
    of fixtures, so the functional tests assert against exactly the data a
    marker sees when they seed and click through the application."""
    from db_seed.seed import seed
    seed()
    return True


@pytest.fixture()
def auth(client):
    """Exchanges credentials for a token and returns the Basic auth header
    every protected endpoint expects."""
    def _auth(email, password='Password1!'):
        response = client.post('/api/user/gettoken',
                               json={'email': email, 'password': password})
        assert response.status_code == 200, response.get_json()
        raw = '%s:%s' % (email, response.get_json()['token'])
        return {'Authorization': 'Basic %s'% base64.b64encode(raw.encode()).decode()}
    return _auth