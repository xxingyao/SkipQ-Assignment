from flask import Blueprint, jsonify, request

from app.blueprints.security import current_user, role_required, token_auth
from app.blueprints.lookups import find_or_404
from app.models.errors import NotPermitted, RuleViolation
from app.models.fooditem import FoodItem
from app.models.notification import Notification
from app.models.order import FoodOrder
from app.models.payment import PAYMENT_METHODS, Payment
from app.models.users import Vendor

diner_bp = Blueprint('diner_bp', __name__, url_prefix='/api/diner')


@diner_bp.before_request
def diner_only():
    """Role check for every route below, declared once.

    A CORS preflight is exempt: the browser sends OPTIONS without credentials
    by design, so checking it would refuse the handshake before the real
    request was ever made. The real request still passes through the guard.
    """
    if request.method == 'OPTIONS':
        return None
    return _require_diner()


@token_auth.login_required
@role_required('Diner')
def _require_diner():
    return None


def _own_order(order_id):
    """SCOPE CHECK: a diner reaches only their own orders."""
    order = find_or_404(FoodOrder, order_id, 'order')
    if order.diner.id != current_user().id:
        raise NotPermitted('That order belongs to another diner')
    return order


@diner_bp.route('/stalls')
def list_stalls():
    return jsonify({'stalls': [v.to_json() for v in Vendor.all_stalls()]}), 200


@diner_bp.route('/stalls/<stall_id>/menu')
def stall_menu(stall_id):
    vendor = find_or_404(Vendor, stall_id, 'stall')
    return jsonify({
        'stall': vendor.to_json(),
        'items': [i.to_json() for i in FoodItem.for_vendor(vendor)],
    }), 200


@diner_bp.route('/orders', methods=['POST'])
def place_order():
    data = request.get_json(silent=True) or {}
    vendor = find_or_404(Vendor, data.get('stall_id'), 'stall')

    lines = []
    for raw in data.get('items') or []:
        item = find_or_404(FoodItem, raw.get('item_id'), 'menu item')
        quantity = raw.get('quantity', 1)
        if not isinstance(quantity, int) or not 1 <= quantity <= 20:
            raise RuleViolation(
                'Quantity for %s must be a whole number from 1 to 20'
                % item.food_item_name, 400)
        lines.append((item, quantity))

    order = FoodOrder.place(current_user(), vendor, lines)
    return jsonify(order.to_json()), 201


@diner_bp.route('/orders/<order_id>/pay', methods=['POST'])
def pay(order_id):
    order = _own_order(order_id)
    method = (request.get_json(silent=True) or {}).get('method', 'PayNow')
    if method not in PAYMENT_METHODS:
        raise RuleViolation(
            'Payment method must be one of %s' % ', '.join(PAYMENT_METHODS), 400)
    Payment.pay(order, method)
    return jsonify(order.to_json()), 201


@diner_bp.route('/orders')
def my_orders():
    orders = FoodOrder.for_diner(current_user())
    return jsonify({'orders': [o.to_json() for o in orders]}), 200


@diner_bp.route('/orders/<order_id>')
def one_order(order_id):
    return jsonify(_own_order(order_id).to_json()), 200


@diner_bp.route('/notifications')
def notifications():
    unread = Notification.unread_for(current_user())
    return jsonify({'notifications': [n.to_json() for n in unread]}), 200

@diner_bp.route('/notifications/read', methods=['POST'])
def dismiss_notifications():
    """POST, not GET, because this changes state. The read flag belongs to the
    diner, so the scope check is the Blueprint's role guard plus current_user()."""
    return jsonify({'marked_read': Notification.mark_all_read(current_user())}), 200