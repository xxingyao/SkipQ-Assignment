#!/usr/bin/env python
"""Seed the SkipQ database with enough data to exercise all four capabilities
in the Question 1 build scope.

    python db_seed/seed.py

Reads the same configuration the application does, so it seeds whichever
database MONGODB_DB names. Drops the SkipQ collections first, so running it
twice produces the same result.
"""
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

from mongoengine import connect, disconnect
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config                                    # noqa: E402
from app.models.users import User, Diner, Vendor                 # noqa: E402
from app.models.fooditem import FoodItem                         # noqa: E402
from app.models.order import FoodOrder, OrderedFood              # noqa: E402
from app.models.payment import Payment                           # noqa: E402
from app.models.notification import Notification                 # noqa: E402
from app.models.token import UserTokens                          # noqa: E402

PASSWORD = 'Password1!'
NOW = datetime.utcnow()


def minutes_ago(n):
    return NOW - timedelta(minutes=n)


def wipe():
    for model in (Notification, Payment, FoodOrder, FoodItem, UserTokens, User):
        model.drop_collection()


def make_order(diner, vendor, lines, status, age_minutes=5,
               queue=None, reason=None, paid_method='PayNow'):
    """Build an order directly in the given status. The seed constructs known
    states; the transition guard is exercised by the tests, not here."""
    entries = []
    for item, quantity in lines:
        unit = item.food_item_price
        entries.append(OrderedFood(
            food_item=item,
            name_at_order=item.food_item_name,
            unit_price_at_order=unit,
            food_quantity=quantity,
            food_subtotal=unit * quantity,
        ))
    stamp = minutes_ago(age_minutes)
    order = FoodOrder(
        diner=diner, vendor=vendor, items=entries,
        order_total_cost=sum(e.food_subtotal for e in entries),
        order_status=status, queue_number=queue, rejection_reason=reason,
        created_at=stamp, status_updated_at=stamp,
    ).save()

    if status != 'PendingPayment':
        payment_status = 'Refunded' if status in ('Rejected', 'Refunded') else 'Paid'
        Payment(order=order, amount=order.order_total_cost, method=paid_method,
                payment_status=payment_status, paid_at=stamp).save()
    return order


def seed():
    wipe()
    pw = generate_password_hash(PASSWORD)

    # --- vendors: two trading, one closed -----------------------------
    ah_hock = Vendor(email='ahhock@skipq.test', password=pw, name='Leow Soon Huat',
                     stall_name='Ah Hock Chicken Rice', venue_type='Food court',
                     is_accepting_orders=True).save()
    mei_xiang = Vendor(email='meixiang@skipq.test', password=pw, name='Tan Mei Xiang',
                       stall_name='Mei Xiang Laksa', venue_type='Food court',
                       is_accepting_orders=False).save()
    tanglin = Vendor(email='tanglin@skipq.test', password=pw, name='Daniel Ong',
                     stall_name='Tanglin Table', venue_type='Restaurant',
                     is_accepting_orders=True).save()

    # --- diners: two, so cross-diner scope can be refused --------------
    weiling = Diner(email='weiling@skipq.test', password=pw, name='Tan Wei Ling').save()
    kumar = Diner(email='kumar@skipq.test', password=pw, name='Kumar Rajan').save()

    # --- menu ----------------------------------------------------------
    chicken_rice = FoodItem(vendor=ah_hock, food_item_name='Steamed Chicken Rice',
                            food_item_description='Poached chicken, chilli, ginger.',
                            food_item_price=Decimal('5.50')).save()
    roast_rice = FoodItem(vendor=ah_hock, food_item_name='Roast Chicken Rice',
                          food_item_description='Roast chicken over fragrant rice.',
                          food_item_price=Decimal('6.00')).save()
    soup = FoodItem(vendor=ah_hock, food_item_name='Chicken Soup',
                    food_item_description='Clear broth with cabbage.',
                    food_item_price=Decimal('2.00')).save()
    # Sold out: the diner must see this before ordering, and payment must refuse it
    braised_egg = FoodItem(vendor=ah_hock, food_item_name='Braised Egg',
                           food_item_description='Soy-braised egg.',
                           food_item_price=Decimal('1.00'),
                           food_item_availability=False).save()

    laksa = FoodItem(vendor=mei_xiang, food_item_name='Katong Laksa',
                     food_item_description='Thick rice noodles in coconut gravy.',
                     food_item_price=Decimal('6.50')).save()

    chop = FoodItem(vendor=tanglin, food_item_name='Hainanese Pork Chop',
                    food_item_description='Breaded chop, tomato gravy.',
                    food_item_price=Decimal('18.00')).save()
    laksa_pasta = FoodItem(vendor=tanglin, food_item_name='Laksa Linguine',
                           food_item_description='Linguine in laksa gravy.',
                           food_item_price=Decimal('22.00')).save()

    # --- orders: every status in ORDER_STATUSES -------------------------
    make_order(weiling, ah_hock, [(chicken_rice, 1)], 'PendingPayment',
               age_minutes=2)

    make_order(weiling, ah_hock, [(chicken_rice, 2), (soup, 1)],
               'PendingAcceptance', age_minutes=6, queue=1)

    make_order(kumar, ah_hock, [(roast_rice, 1)],
               'PendingPreparation', age_minutes=12, queue=2)

    # Ready 45 minutes ago: no-show is permitted
    stale = make_order(weiling, ah_hock, [(chicken_rice, 1)],
                       'PendingCollection', age_minutes=45, queue=3)
    Notification.ready(stale)

    # Ready 5 minutes ago: no-show must be refused
    fresh = make_order(kumar, ah_hock, [(soup, 2)],
                       'PendingCollection', age_minutes=5, queue=4)
    Notification.ready(fresh)

    make_order(weiling, ah_hock, [(roast_rice, 1), (soup, 1)],
               'Collected', age_minutes=90, queue=5)
    make_order(kumar, ah_hock, [(chicken_rice, 3)],
               'Collected', age_minutes=120, queue=6)
    # Contains a now-sold-out item: proves the price and name snapshots hold
    make_order(weiling, ah_hock, [(chicken_rice, 1), (braised_egg, 2)],
               'Collected', age_minutes=150, queue=7)

    rejected = make_order(kumar, ah_hock, [(roast_rice, 2)], 'Rejected',
                          age_minutes=200, queue=8, reason='Ran out of roast chicken')
    Notification.rejected(rejected, rejected.rejection_reason)

    # Refunded and NoShow carry value, so the dashboard's exclusions are visible
    make_order(weiling, ah_hock, [(chicken_rice, 4)], 'Refunded',
               age_minutes=240, queue=9)
    make_order(kumar, ah_hock, [(soup, 1)], 'NoShow',
               age_minutes=300, queue=10)

    # A second vendor's orders, so a cross-vendor read can be refused
    make_order(weiling, tanglin, [(chop, 2)], 'PendingPreparation',
               age_minutes=15, queue=1)
    make_order(kumar, tanglin, [(laksa_pasta, 1)], 'Collected',
               age_minutes=180, queue=2)

    print('Seeded:')
    print(f'  vendors        {Vendor.objects.count()} '
          f'({Vendor.objects(is_accepting_orders=True).count()} trading)')
    print(f'  diners         {Diner.objects.count()}')
    print(f'  menu items     {FoodItem.objects.count()} '
          f'({FoodItem.objects(food_item_availability=False).count()} sold out)')
    print(f'  orders         {FoodOrder.objects.count()}')
    for status in sorted(FoodOrder.objects.distinct('order_status')):
        print(f'      {status:<20} {FoodOrder.objects(order_status=status).count()}')
    print(f'  payments       {Payment.objects.count()}')
    print(f'  notifications  {Notification.objects.count()}')
    print(f"\nAll accounts use the password: {PASSWORD}")


if __name__ == '__main__':
    settings = Config.MONGODB_SETTINGS
    connect(db=settings['db'], host=settings['host'], port=settings['port'])
    try:
        seed()
    finally:
        disconnect()
