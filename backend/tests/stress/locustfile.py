"""Question 6 b) — load on the endpoint the Question 5 flows call most often.

GET /api/vendor/orders is the busiest read in those flows. The vendor board is
the one screen a stall owner leaves open for a whole trading period, and it is
refreshed after every order they accept, ready or collect; a diner opens their
own order list only a few times per order, and the stall list once per visit.

Every user signs in as the same stall owner, because that is what the endpoint
under test requires — one vendor reading their own board.

Run it with the backend up and the database seeded:

    mkdir -p q6-performance
    locust -f tests/stress/locustfile.py --host http://127.0.0.1:5000 \\
           --headless -u 20 -r 5 -t 60s --csv q6-performance/vendor-orders
"""
import base64

from locust import HttpUser, between, task

VENDOR = 'ahhock@skipq.test'
PASSWORD = 'Password1!'


class VendorWatchingTheBoard(HttpUser):
    """A stall owner with the order board open, refreshing it as they work."""

    wait_time = between(1, 3)

    def on_start(self):
        # The token is created on first use, so two users starting at the same
        # moment can race and one gets a 409. A single retry settles it.
        for _ in range(2):
            response = self.client.post(
                '/api/user/gettoken',
                json={'email': VENDOR, 'password': PASSWORD},
                name='/api/user/gettoken')
            if response.status_code == 200:
                break
        else:
            response.raise_for_status()

        raw = f"{VENDOR}:{response.json()['token']}"
        self.headers = {
            'Authorization': 'Basic ' + base64.b64encode(raw.encode()).decode(),
        }

    @task
    def read_the_order_board(self):
        self.client.get('/api/vendor/orders', headers=self.headers,
                        name='/api/vendor/orders')