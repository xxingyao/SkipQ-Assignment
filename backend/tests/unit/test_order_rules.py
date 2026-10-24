"""Unit tests for the order rules.

These run with no database and no Flask application. Each one builds a
FoodOrder in memory and never calls save(), and the one that needs a vendor
identity supplies a mock instead of a stored document. What they prove is the
rule logic itself, isolated from persistence, routing and authentication.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.models.errors import RuleViolation
from app.models.order import (NO_SHOW_AFTER_MINUTES, ORDER_STATUSES,
                              TRANSITIONS, FoodOrder, OrderedFood)

# The transition table is the specification, so the cases are derived from it
# rather than retyped. A move added to or removed from TRANSITIONS changes
# which assertions run, instead of leaving a stale test passing.
ALLOWED = [(frm, to) for frm, tos in TRANSITIONS.items() for to in sorted(tos)]
REFUSED = [(frm, to) for frm in TRANSITIONS for to in ORDER_STATUSES
           if to not in TRANSITIONS[frm]]


@pytest.mark.parametrize('frm,to', ALLOWED)
def test_the_table_permits_every_move_it_declares(frm, to):
    """GIVEN an order in a state the transition table can move out of
    WHEN the guard is asked about a move that table declares
    THEN it permits the move."""
    assert FoodOrder(order_status=frm).can_transition(to) is True


@pytest.mark.parametrize('frm,to', REFUSED)
def test_the_table_refuses_everything_else(frm, to):
    """GIVEN an order in any state
    WHEN the guard is asked about a move the transition table does not declare
    THEN it refuses the move."""
    assert FoodOrder(order_status=frm).can_transition(to) is False


def test_terminal_states_permit_nothing():
    """GIVEN an order that has been collected, refunded or marked no-show
    WHEN every status in the system is offered as a next move
    THEN none of them is permitted."""
    for status in ('Collected', 'Refunded', 'NoShow'):
        order = FoodOrder(order_status=status)
        assert not any(order.can_transition(to) for to in ORDER_STATUSES)


# ---- the guard refuses without writing ---------------------------------

def test_an_illegal_move_raises_and_leaves_the_status_alone():
    """GIVEN an order waiting for the stall to accept it
    WHEN a caller tries to jump it straight to collected
    THEN the guard raises, naming the state it refused from, and the order's
         status is unchanged."""
    order = FoodOrder(order_status='PendingAcceptance')
    with pytest.raises(RuleViolation) as refused:
        order.apply_transition('Collected')
    assert 'PendingAcceptance' in str(refused.value)
    assert order.order_status == 'PendingAcceptance'


def test_an_actor_from_another_stall_is_refused():
    """GIVEN an order belonging to one stall
    WHEN a different stall tries to move it
    THEN the guard refuses and the order's status is unchanged.

    The scope arm of the guard, proved with a mock rather than two stored
    vendors, because the rule only ever reads the identity."""
    order = FoodOrder(order_status='PendingAcceptance')
    order.vendor = Mock(id='stall-a')
    with pytest.raises(RuleViolation):
        order.apply_transition('PendingPreparation', actor=Mock(id='stall-b'))
    assert order.order_status == 'PendingAcceptance'


# ---- the no-show window ------------------------------------------------

def test_no_show_is_refused_inside_the_window():
    """GIVEN an order that became ready less than the no-show window ago
    WHEN its no-show eligibility is checked
    THEN it is not yet eligible."""
    order = FoodOrder(
        order_status='PendingCollection',
        status_updated_at=datetime.utcnow() - timedelta(
            minutes=NO_SHOW_AFTER_MINUTES - 1))
    assert order.is_no_show_eligible() is False


def test_no_show_is_allowed_once_the_window_has_passed():
    """GIVEN an order that became ready more than the no-show window ago
    WHEN its no-show eligibility is checked
    THEN it is eligible."""
    order = FoodOrder(
        order_status='PendingCollection',
        status_updated_at=datetime.utcnow() - timedelta(
            minutes=NO_SHOW_AFTER_MINUTES + 1))
    assert order.is_no_show_eligible() is True


def test_no_show_needs_the_order_to_be_ready_first():
    """GIVEN an order still being prepared, however long ago it was updated
    WHEN its no-show eligibility is checked
    THEN it is not eligible, because no-show applies only once it is ready."""
    order = FoodOrder(
        order_status='PendingPreparation',
        status_updated_at=datetime.utcnow() - timedelta(hours=3))
    assert order.is_no_show_eligible() is False


def test_a_premature_no_show_raises_even_though_the_table_allows_it():
    """GIVEN an order that became ready a minute ago
    WHEN a vendor tries to mark it no-show
    THEN the table permits the move but the guard still refuses it, naming the
         waiting period, which shows the time rule is a second and independent
         condition rather than part of the table."""
    order = FoodOrder(
        order_status='PendingCollection',
        status_updated_at=datetime.utcnow() - timedelta(minutes=1))
    assert order.can_transition('NoShow') is True
    with pytest.raises(RuleViolation) as refused:
        order.apply_transition('NoShow')
    assert str(NO_SHOW_AFTER_MINUTES) in str(refused.value)


# ---- totals ------------------------------------------------------------

def line(subtotal):
    return OrderedFood(name_at_order='x', unit_price_at_order=Decimal('1.00'),
                       food_quantity=1, food_subtotal=Decimal(subtotal))


def test_the_total_is_the_sum_of_the_line_subtotals():
    """GIVEN an order holding three priced lines
    WHEN its total is recalculated
    THEN the total is the sum of those line subtotals."""
    order = FoodOrder(items=[line('3.50'), line('1.20'), line('0.30')])
    assert order.recalculate_total() == Decimal('5.00')


def test_an_order_with_no_lines_totals_zero():
    """GIVEN an order holding no lines
    WHEN its total is recalculated
    THEN the total is zero rather than an error."""
    assert FoodOrder(items=[]).recalculate_total() == 0