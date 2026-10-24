from datetime import datetime, timedelta

from app.extensions import db
from app.models.errors import RuleViolation
from app.models.users import Diner, Vendor
from app.models.fooditem import FoodItem


ORDER_STATUSES = (
    'PendingPayment',
    'PendingAcceptance',
    'PendingPreparation',
    'PendingCollection',
    'Collected',
    'Rejected',
    'Refunded',
    'NoShow',
)

# Permitted transitions. Q3c guards against this; Q4a tests both directions.
TRANSITIONS = {
    'PendingPayment':      {'PendingAcceptance'},
    'PendingAcceptance':   {'PendingPreparation', 'Rejected'},
    'PendingPreparation':  {'PendingCollection', 'Refunded'},
    'PendingCollection':   {'Collected', 'NoShow'},
    'Rejected':            {'Refunded'},
    'Collected':           set(),
    'Refunded':            set(),
    'NoShow':              set(),
}

NO_SHOW_AFTER_MINUTES = 30

# Statuses whose value counts towards a vendor's takings.
REVENUE_STATUSES = ('PendingAcceptance', 'PendingPreparation',
                    'PendingCollection', 'Collected', 'NoShow')


class OrderedFood(db.EmbeddedDocument):
    """A line on an order. Name and price are SNAPSHOTS taken when the order is
    placed, so a later price edit never rewrites a past order or its takings."""

    food_item = db.ReferenceField(FoodItem, required=True)
    name_at_order = db.StringField(required=True, max_length=80)
    unit_price_at_order = db.DecimalField(required=True, precision=2)
    food_quantity = db.IntField(required=True, min_value=1, max_value=20)
    food_subtotal = db.DecimalField(required=True, precision=2)


class FoodOrder(db.Document):
    meta = {
        'collection': 'foodOrders',
        'indexes': [('vendor', 'order_status'), ('diner', '-created_at')],
    }

    diner = db.ReferenceField(Diner, required=True)
    vendor = db.ReferenceField(Vendor, required=True)
    items = db.EmbeddedDocumentListField(OrderedFood, required=True)

    order_total_cost = db.DecimalField(required=True, precision=2)
    order_status = db.StringField(required=True, choices=ORDER_STATUSES,
                                  default='PendingPayment')
    queue_number = db.IntField()
    rejection_reason = db.StringField(max_length=200)

    created_at = db.DateTimeField(default=datetime.utcnow)
    status_updated_at = db.DateTimeField(default=datetime.utcnow)

    # ---- rules -------------------------------------------------------

    def can_transition(self, to_status):
        """Pure lookup, no database. This is the method a mocked unit test can
        still prove right (TMA Q4a)."""
        return to_status in TRANSITIONS.get(self.order_status, set())

    def is_no_show_eligible(self):
        if self.order_status != 'PendingCollection':
            return False
        waited = datetime.utcnow() - self.status_updated_at
        return waited >= timedelta(minutes=NO_SHOW_AFTER_MINUTES)

    def apply_transition(self, to_status, actor=None):
        """The guard. Q3c requires this to live in the model, not the routes."""
        if actor is not None and actor.id != self.vendor.id:
            raise RuleViolation('You can only change orders for your own stall')
        if not self.can_transition(to_status):
            raise RuleViolation(
                f'An order that is {self.order_status} cannot become {to_status}')
        if to_status == 'NoShow' and not self.is_no_show_eligible():
            raise RuleViolation(
                f'An order can only be marked no-show '
                f'{NO_SHOW_AFTER_MINUTES} minutes after it is ready')
        self.order_status = to_status
        self.status_updated_at = datetime.utcnow()
        return self.save()

    def recalculate_total(self):
        self.order_total_cost = sum(line.food_subtotal for line in self.items)
        return self.order_total_cost

    # ---- creation ----------------------------------------------------

    @classmethod
    def place(cls, diner, vendor, lines):
        """lines: iterable of (FoodItem, quantity). Snapshots name and price so
        the order is immune to later menu edits."""
        if not vendor.is_accepting_orders:
            raise RuleViolation(f'{vendor.stall_name} is not accepting orders')
        if not lines:
            raise RuleViolation('An order must contain at least one item')

        entries = []
        for food_item, quantity in lines:
            if food_item.vendor.id != vendor.id:
                raise RuleViolation(
                    f'{food_item.food_item_name} is not sold by {vendor.stall_name}')
            if not food_item.is_orderable():
                raise RuleViolation(f'{food_item.food_item_name} is sold out')
            unit = food_item.food_item_price
            entries.append(OrderedFood(
                food_item=food_item,
                name_at_order=food_item.food_item_name,
                unit_price_at_order=unit,
                food_quantity=quantity,
                food_subtotal=unit * quantity,
            ))

        order = cls(diner=diner, vendor=vendor, items=entries)
        order.recalculate_total()
        return order.save()

    def to_json(self):
        return {
            'id': str(self.id),
            'queue_number': self.queue_number,
            'status': self.order_status,
            'vendor_id': str(self.vendor.id),
            'stall_name': self.vendor.stall_name,
            'diner_name': self.diner.name,
            'total': float(self.order_total_cost),
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat(),
            'status_updated_at': self.status_updated_at.isoformat(),
            'items': [
                {
                    'name': line.name_at_order,
                    'unit_price': float(line.unit_price_at_order),
                    'quantity': line.food_quantity,
                    'subtotal': float(line.food_subtotal),
                }
                for line in self.items
            ],
        }

    # ---- reads -------------------------------------------------------

    @staticmethod
    def for_diner(diner):
        return FoodOrder.objects(diner=diner).order_by('-created_at')

    @staticmethod
    def for_vendor(vendor, statuses=None):
        qs = FoodOrder.objects(vendor=vendor)
        if statuses:
            qs = qs.filter(order_status__in=statuses)
        return qs.order_by('created_at')

    @staticmethod
    def next_queue_number(vendor):
        last = FoodOrder.objects(vendor=vendor).order_by('-queue_number').first()
        return (last.queue_number or 0) + 1 if last else 1

    # ---- sales dashboard (the extra story) ---------------------------

    @staticmethod
    def _day_bounds(day=None):
        day = day or datetime.utcnow().date()
        start = datetime(day.year, day.month, day.day)
        return day, start, start + timedelta(days=1)

    @classmethod
    def daily_sales(cls, vendor, day=None):
        """Takings and order count for one trading day. Rejected and Refunded
        orders are excluded, so a refund does not inflate the figures."""
        day, start, end = cls._day_bounds(day)
        orders = list(cls.objects(vendor=vendor,
                                  created_at__gte=start, created_at__lt=end,
                                  order_status__in=REVENUE_STATUSES))
        return {
            'date': day.isoformat(),
            'order_count': len(orders),
            'total_takings': float(sum(o.order_total_cost for o in orders)),
        }

    @classmethod
    def top_items(cls, vendor, day=None, limit=3):
        """Best sellers by quantity, counted from the order's own snapshots."""
        _, start, end = cls._day_bounds(day)
        tally = {}
        for order in cls.objects(vendor=vendor,
                                 created_at__gte=start, created_at__lt=end,
                                 order_status__in=REVENUE_STATUSES):
            for line in order.items:
                tally[line.name_at_order] = tally.get(line.name_at_order, 0) + line.food_quantity
        ranked = sorted(tally.items(), key=lambda kv: kv[1], reverse=True)
        return [{'name': name, 'quantity': qty} for name, qty in ranked[:limit]]
