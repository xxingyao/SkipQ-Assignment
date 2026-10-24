"""Question 6 a) — one order through its whole lifecycle, in a real browser.

Both personas sign in through the UI, and the test asserts on what each screen
shows after every step rather than only at the end. Every wait is a condition
on the page — Playwright's expect() polls until the assertion holds — so the
result does not depend on how fast the machine running it is.

Repeatable: the test places its own order rather than advancing one the seed
created, and it never assumes which menu item is sold out, so running it twice
in a row against the same seeded database gives the same result.

Both applications must be running. See the README.
"""
import re
import urllib.error
import urllib.request

import pytest
from playwright.sync_api import expect, sync_playwright

FRONTEND = 'http://127.0.0.1:3000'
BACKEND = 'http://127.0.0.1:5000'
PASSWORD = 'Password1!'
DINER = 'weiling@skipq.test'
VENDOR = 'ahhock@skipq.test'
STALL = 'Ah Hock Chicken Rice'

# The vendor board renders one column per stage, in this order.
PENDING, PREPARING, READY, COMPLETED = 0, 1, 2, 3

pytestmark = pytest.mark.browser


def reachable(url):
    try:
        urllib.request.urlopen(url, timeout=2)
    except urllib.error.HTTPError:
        return True          # answering, even if it refuses us
    except Exception:
        return False
    return True


@pytest.fixture(autouse=True)
def both_applications_running():
    """A browser test cannot distinguish a missing server from a broken page,
    so it checks the precondition itself rather than failing on a selector."""
    for name, url in (('backend', f'{BACKEND}/api/diner/stalls'),
                      ('frontend', FRONTEND)):
        if not reachable(url):
            pytest.fail(f'The {name} is not running at {url}. '
                        'Start both applications before running this test.')


def sign_in(page, email):
    page.goto(FRONTEND)
    page.get_by_label('Email').fill(email)
    page.get_by_label('Password').fill(PASSWORD)
    page.get_by_role('button', name='Sign in').click()


def column(page, index):
    return page.locator('.col-md-3').nth(index)

def card_for(page, index, number):
    """The one order card carrying this queue number, in that stage's column.
    Matched on the exact ticket text, because the card's text content runs the
    number straight into the status badge with no separator."""
    return column(page, index).locator('.card').filter(
        has=page.get_by_text(f'#{number}', exact=True))

def test_an_order_runs_from_placement_to_collection_in_a_browser():
    """GIVEN a seeded database and both applications running
    WHEN a diner places and pays for an order and the vendor carries it to
         collection, each signing in through the browser
    THEN every screen shows the state that persona needs at each step, and no
         control is offered for a move the guard would refuse."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        # Separate contexts so both personas hold a session at once, as two
        # people on two phones would.
        diner = browser.new_context().new_page()
        vendor = browser.new_context().new_page()
        try:
            carry_one_order(diner, vendor)
        finally:
            browser.close()


def carry_one_order(diner, vendor):
    # --- the diner signs in and sees which stalls are trading -------------
    sign_in(diner, DINER)
    expect(diner.get_by_text(re.compile(r'Signed in as .* — diner'))).to_be_visible()

    closed = diner.locator('.card').filter(has_text='Mei Xiang Laksa')
    expect(closed.get_by_text('Closed')).to_be_visible()
    expect(closed.get_by_role('button', name='Not taking orders')).to_be_disabled()

    # --- the menu shows what cannot be ordered, before it is tried --------
    diner.locator('.card').filter(has_text=STALL) \
         .get_by_role('link', name='View menu').click()
    expect(diner.get_by_role('heading', name=STALL)).to_be_visible()

    # Whichever item the stall has marked sold out — the test does not assume
    # which, so a vendor toggling stock between runs cannot break it.
    sold_out = diner.locator('li').filter(has_text='Sold out').first
    expect(sold_out).to_be_visible()
    expect(sold_out.get_by_role('button', name='+')).to_be_disabled()

    # --- place the order on an item that is orderable ---------------------
    orderable = diner.locator('li').filter(has_not_text='Sold out').first
    orderable.get_by_role('button', name='+').click()
    diner.get_by_role('button', name='Place order').click()

    newest = diner.locator('.card').first
    expect(newest.get_by_text('Awaiting payment')).to_be_visible()
    expect(newest.get_by_text('No queue number yet')).to_be_visible()

    # --- paying issues the queue number -----------------------------------
    newest.get_by_role('button', name='Pay with PayNow').click()
    expect(newest.get_by_text('Waiting for the stall')).to_be_visible()

    queue_line = newest.get_by_text(re.compile(r'^Queue \d+$'))
    expect(queue_line).to_be_visible()
    number = queue_line.inner_text().split()[1]

    # --- the vendor signs in and finds it waiting -------------------------
    sign_in(vendor, VENDOR)
    expect(vendor.get_by_text(re.compile(r'Signed in as .* — stall owner'))).to_be_visible()

    waiting = card_for(vendor, PENDING, number)
    expect(waiting.get_by_text('Waiting for the stall')).to_be_visible()
    expect(waiting.get_by_role('button', name='Accept')).to_be_visible()
    # No control is offered for a move the guard would refuse from this state.
    expect(waiting.get_by_role('button', name='Collected')).to_have_count(0)

    waiting.get_by_role('button', name='Accept').click()

    cooking = card_for(vendor, PREPARING, number)
    expect(cooking.get_by_text('Being prepared')).to_be_visible()
    cooking.get_by_role('button', name='Ready for collection').click()

    ready = card_for(vendor, READY, number)
    expect(ready.get_by_text('Ready to collect')).to_be_visible()

    # --- the diner learns of it on their own screen -----------------------
    diner.reload()
    expect(diner.locator('.card').first.get_by_text('Ready to collect')).to_be_visible()
    expect(diner.get_by_text(
        f'Queue {number} is ready for collection at {STALL}')).to_be_visible()

    # --- collection closes it ---------------------------------------------
    ready.get_by_role('button', name='Collected').click()
    done = card_for(vendor, COMPLETED, number)
    expect(done.get_by_text('Collected')).to_be_visible()