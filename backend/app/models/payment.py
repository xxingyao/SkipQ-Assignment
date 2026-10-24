from datetime import datetime

from app.extensions import db
from app.models.errors import RuleViolation
from app.models.order import FoodOrder


PAYMENT_METHODS = ('PayNow', 'Card', 'Wallet')
PAYMENT_STATUSES = ('Pending', 'Paid', 'Failed', 'Refunded')


class Payment(db.Document):
    """Simulated payment: SkipQ records that an order was paid and by what
    method, with no gateway integration (TMA build scope)."""

    meta = {'collection': 'payments'}

    order = db.ReferenceField(FoodOrder, required=True, unique=True)
    amount = db.DecimalField(required=True, precision=2)
    method = db.StringField(required=True, choices=PAYMENT_METHODS)
    payment_status = db.StringField(required=True, choices=PAYMENT_STATUSES,
                                    default='Pending')
    paid_at = db.DateTimeField()

    @staticmethod
    def for_order(order):
        return Payment.objects(order=order).first()

    @classmethod
    def pay(cls, order, method):
        """Availability is binding at payment: an item sold out since it was
        added blocks the payment rather than failing after the diner is charged
        (the persona conflict resolved in GBA Q2c)."""
        if Payment.for_order(order):
            raise RuleViolation('This order has already been paid')
        if not order.vendor.is_accepting_orders:
            raise RuleViolation(
                f'{order.vendor.stall_name} stopped accepting orders')
        for line in order.items:
            if not line.food_item.food_item_availability:
                raise RuleViolation(
                    f'{line.name_at_order} is sold out — amend your order')

        payment = cls(order=order, amount=order.order_total_cost,
                      method=method, payment_status='Paid',
                      paid_at=datetime.utcnow()).save()

        order.queue_number = FoodOrder.next_queue_number(order.vendor)
        order.apply_transition('PendingAcceptance')
        return payment

    def mark_refunded(self):
        self.payment_status = 'Refunded'
        return self.save()
