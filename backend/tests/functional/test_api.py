"""Functional tests that drive the real application through its HTTP layer.

Each one goes through the Flask test client against a seeded test database, so
unlike the unit tests they exercise routing, token authentication, the role and
scope checks, and persistence together. That is the point: a unit test can
prove a rule is correct, but only a test at this level can prove a route
actually calls it.

The assertions on the dashboard figures assume a freshly seeded database, for
the same reason the seeded-data plan gives in Question 2c: every order is
anchored to the moment the seed ran, and the trading day is bounded in UTC.
"""
import pytest

DINER = 'weiling@skipq.test'
OTHER_DINER = 'kumar@skipq.test'
VENDOR = 'ahhock@skipq.test'
OTHER_VENDOR = 'meixiang@skipq.test'

pytestmark = pytest.mark.usefixtures('seeded')


# ---- authentication ----------------------------------------------------

def test_a_token_is_issued_with_the_role_the_client_needs(client):
    response = client.post('/api/user/gettoken',
                           json={'email': DINER, 'password': 'Password1!'})
    assert response.status_code == 200
    assert response.get_json()['role'] == 'Diner'


def test_a_wrong_password_is_refused_without_saying_which_half_was_wrong(client):
    response = client.post('/api/user/gettoken',
                           json={'email': DINER, 'password': 'wrong'})
    assert response.status_code == 401
    assert response.get_json()['error'] == 'Invalid email or password'


def test_an_unknown_email_gives_the_same_message(client):
    response = client.post('/api/user/gettoken',
                           json={'email': 'nobody@skipq.test',
                                 'password': 'Password1!'})
    assert response.status_code == 401
    assert response.get_json()['error'] == 'Invalid email or password'


def test_a_protected_endpoint_refuses_a_request_with_no_token(client):
    assert client.get('/api/diner/stalls').status_code == 401


# ---- the role check ----------------------------------------------------

def test_a_diner_cannot_reach_a_vendor_endpoint(client, auth):
    response = client.get('/api/vendor/dashboard', headers=auth(DINER))
    assert response.status_code == 403


def test_a_vendor_cannot_reach_a_diner_endpoint(client, auth):
    response = client.get('/api/diner/orders', headers=auth(VENDOR))
    assert response.status_code == 403


# ---- the scope check ---------------------------------------------------

def test_a_diner_cannot_read_another_diners_order(client, auth):
    mine = client.get('/api/diner/orders', headers=auth(DINER))
    order_id = mine.get_json()['orders'][0]['id']

    response = client.get('/api/diner/orders/%s' % order_id,
                          headers=auth(OTHER_DINER))
    assert response.status_code == 403


def test_a_vendor_cannot_move_an_order_from_another_stall(client, auth):
    orders = client.get('/api/vendor/orders', headers=auth(VENDOR))
    order_id = orders.get_json()['orders'][0]['id']

    response = client.patch('/api/vendor/orders/%s/status' % order_id,
                            json={'status': 'PendingPreparation'},
                            headers=auth(OTHER_VENDOR))
    assert response.status_code == 403


# ---- the lifecycle, end to end -----------------------------------------

def place_an_order(client, auth):
    stalls = client.get('/api/diner/stalls', headers=auth(DINER)).get_json()
    stall = next(s for s in stalls['stalls'] if s['is_accepting_orders'])

    menu = client.get('/api/diner/stalls/%s/menu' % stall['id'],
                      headers=auth(DINER)).get_json()
    item = next(i for i in menu['items'] if i['orderable'])

    created = client.post('/api/diner/orders', headers=auth(DINER),
                          json={'stall_id': stall['id'],
                                'items': [{'item_id': item['id'],
                                           'quantity': 2}]})
    assert created.status_code == 201
    return created.get_json(), item


def test_an_order_runs_from_payment_through_to_collection(client, auth):
    order, _ = place_an_order(client, auth)
    assert order['status'] == 'PendingPayment'
    assert order['queue_number'] is None

    paid = client.post('/api/diner/orders/%s/pay' % order['id'],
                       json={'method': 'PayNow'}, headers=auth(DINER))
    assert paid.status_code == 201
    assert paid.get_json()['status'] == 'PendingAcceptance'
    # The seed has already issued queue numbers at this stall, so a payment
    # that started the sequence again would show up here.
    assert paid.get_json()['queue_number'] > 1

    for to_status in ('PendingPreparation', 'PendingCollection', 'Collected'):
        moved = client.patch('/api/vendor/orders/%s/status' % order['id'],
                             json={'status': to_status}, headers=auth(VENDOR))
        assert moved.status_code == 200, moved.get_json()
        assert moved.get_json()['status'] == to_status


def test_marking_an_order_ready_writes_the_diner_a_notification(client, auth):
    order, _ = place_an_order(client, auth)
    client.post('/api/diner/orders/%s/pay' % order['id'],
                json={'method': 'PayNow'}, headers=auth(DINER))
    for to_status in ('PendingPreparation', 'PendingCollection'):
        client.patch('/api/vendor/orders/%s/status' % order['id'],
                     json={'status': to_status}, headers=auth(VENDOR))

    unread = client.get('/api/diner/notifications',
                        headers=auth(DINER)).get_json()['notifications']
    assert any(n['order_id'] == order['id'] for n in unread)

def test_a_dismissed_notification_does_not_come_back(client, auth):
    """The read flag has to be set by something. Without this the unread list
    only grows, and a diner keeps being told about orders already collected."""
    order, _ = place_an_order(client, auth)
    client.post('/api/diner/orders/%s/pay' % order['id'],
                json={'method': 'PayNow'}, headers=auth(DINER))
    for to_status in ('PendingPreparation', 'PendingCollection'):
        client.patch('/api/vendor/orders/%s/status' % order['id'],
                     json={'status': to_status}, headers=auth(VENDOR))

    before = client.get('/api/diner/notifications',
                        headers=auth(DINER)).get_json()['notifications']
    assert any(n['order_id'] == order['id'] for n in before)

    dismissed = client.post('/api/diner/notifications/read', headers=auth(DINER))
    assert dismissed.status_code == 200
    assert dismissed.get_json()['marked_read'] == len(before)

    after = client.get('/api/diner/notifications',
                       headers=auth(DINER)).get_json()['notifications']
    assert after == []

def test_a_rejection_records_the_reason_the_diner_will_read(client, auth):
    order, _ = place_an_order(client, auth)
    client.post('/api/diner/orders/%s/pay' % order['id'],
                json={'method': 'PayNow'}, headers=auth(DINER))

    refused = client.patch('/api/vendor/orders/%s/status' % order['id'],
                           json={'status': 'Rejected'}, headers=auth(VENDOR))
    assert refused.status_code == 400

    rejected = client.patch('/api/vendor/orders/%s/status' % order['id'],
                            json={'status': 'Rejected',
                                  'reason': 'Out of chicken'},
                            headers=auth(VENDOR))
    assert rejected.status_code == 200
    assert rejected.get_json()['rejection_reason'] == 'Out of chicken'


# ---- the rules, as the API enforces them -------------------------------

def test_an_order_cannot_be_placed_at_a_stall_that_is_closed(client, auth):
    stalls = client.get('/api/diner/stalls', headers=auth(DINER)).get_json()
    closed = next(s for s in stalls['stalls'] if not s['is_accepting_orders'])

    menu = client.get('/api/diner/stalls/%s/menu' % closed['id'],
                      headers=auth(DINER)).get_json()

    response = client.post('/api/diner/orders', headers=auth(DINER),
                           json={'stall_id': closed['id'],
                                 'items': [{'item_id': menu['items'][0]['id'],
                                            'quantity': 1}]})
    assert response.status_code == 409


def test_the_same_order_cannot_be_paid_for_twice(client, auth):
    order, _ = place_an_order(client, auth)
    first = client.post('/api/diner/orders/%s/pay' % order['id'],
                        json={'method': 'PayNow'}, headers=auth(DINER))
    second = client.post('/api/diner/orders/%s/pay' % order['id'],
                         json={'method': 'PayNow'}, headers=auth(DINER))
    assert (first.status_code, second.status_code) == (201, 409)


def test_an_unknown_status_is_a_bad_request_not_a_refused_rule(client, auth):
    orders = client.get('/api/vendor/orders', headers=auth(VENDOR))
    order_id = orders.get_json()['orders'][0]['id']

    response = client.patch('/api/vendor/orders/%s/status' % order_id,
                            json={'status': 'Teleported'},
                            headers=auth(VENDOR))
    assert response.status_code == 400


def test_the_guard_is_wired_to_the_route_not_just_present_on_the_model(
        client, auth):
    """The unit tests prove apply_transition refuses an illegal move. This
    proves the vendor endpoint actually goes through it."""
    order, _ = place_an_order(client, auth)
    client.post('/api/diner/orders/%s/pay' % order['id'],
                json={'method': 'PayNow'}, headers=auth(DINER))

    response = client.patch('/api/vendor/orders/%s/status' % order['id'],
                            json={'status': 'Collected'}, headers=auth(VENDOR))
    assert response.status_code == 409
    assert 'cannot become Collected' in response.get_json()['error']


# ---- the price snapshot ------------------------------------------------

def test_editing_the_menu_does_not_rewrite_an_order_already_placed(
        client, auth):
    """Only a test that persists an order and then changes the menu behind it
    can show this; the rule lives in how the data is written, not in a branch
    a unit test could reach."""
    order, item = place_an_order(client, auth)
    total_before = order['total']

    raised = client.patch('/api/vendor/menu/%s' % item['id'],
                          json={'price': float(item['price']) + 5},
                          headers=auth(VENDOR))
    assert raised.status_code == 200

    reread = client.get('/api/diner/orders/%s' % order['id'],
                        headers=auth(DINER)).get_json()
    assert reread['total'] == total_before
    assert reread['items'][0]['unit_price'] == item['price']


# ---- the dashboard -----------------------------------------------------

def test_the_dashboard_counts_only_the_callers_own_stall(client, auth):
    mine = client.get('/api/vendor/dashboard',
                      headers=auth(VENDOR)).get_json()
    other = client.get('/api/vendor/dashboard',
                       headers=auth('tanglin@skipq.test')).get_json()
    assert mine['sales']['order_count'] != other['sales']['order_count']


def test_the_dashboard_excludes_refunded_and_rejected_takings(client, auth):
    sales = client.get('/api/vendor/dashboard',
                       headers=auth(VENDOR)).get_json()['sales']
    # The seed puts $22.00 of Refunded and $12.00 of Rejected value at this
    # stall. Both appear in the order list and neither may appear here.
    assert sales['order_count'] == 8
    assert sales['total_takings'] == 62.5


def test_the_top_items_come_back_ranked(client, auth):
    top = client.get('/api/vendor/dashboard',
                     headers=auth(VENDOR)).get_json()['top_items']
    counts = [entry['quantity'] for entry in top]
    assert counts == sorted(counts, reverse=True)
    assert len(top) <= 3


def test_a_vendor_with_no_orders_gets_an_empty_dashboard(client, auth):
    sales = client.get('/api/vendor/dashboard',
                       headers=auth(OTHER_VENDOR)).get_json()['sales']
    assert sales['order_count'] == 0
    assert sales['total_takings'] == 0


def test_the_sold_out_list_names_the_item_the_seed_marked_unavailable(
        client, auth):
    board = client.get('/api/vendor/dashboard',
                       headers=auth(VENDOR)).get_json()
    assert [i['name'] for i in board['sold_out']] == ['Braised Egg']