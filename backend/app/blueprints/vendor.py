from flask import Blueprint, jsonify, request

from app.blueprints.security import current_user, role_required, token_auth
from app.blueprints.lookups import find_or_404
from app.models.errors import NotPermitted, RuleViolation
from app.models.fooditem import FoodItem
from app.models.notification import Notification
from app.models.order import ORDER_STATUSES, FoodOrder
from app.models.payment import Payment

vendor_bp = Blueprint('vendor_bp', __name__, url_prefix='/api/vendor')


@vendor_bp.before_request
def vendor_only():
    """Role check for every route below, declared once. OPTIONS is exempt for
    the reason given in diner.py: a CORS preflight carries no credentials."""
    if request.method == 'OPTIONS':
        return None
    return _require_vendor()


@token_auth.login_required
@role_required('Vendor')
def _require_vendor():
    return None
def _own_item(item_id):
    """SCOPE CHECK: a vendor reaches only their own menu."""
    item = find_or_404(FoodItem, item_id, 'menu item')
    if item.vendor.id != current_user().id:
        raise NotPermitted('That item belongs to another stall')
    return item


def _own_order(order_id):
    """SCOPE CHECK: a vendor reaches only orders placed at their stall."""
    order = find_or_404(FoodOrder, order_id, 'order')
    if order.vendor.id != current_user().id:
        raise NotPermitted('That order was placed at another stall')
    return order


@vendor_bp.route('/stall')
def my_stall():
    return jsonify(current_user().to_json()), 200


@vendor_bp.route('/stall', methods=['PATCH'])
def set_stall_trading():
    accepting = (request.get_json(silent=True) or {}).get('is_accepting_orders')
    if not isinstance(accepting, bool):
        raise RuleViolation('is_accepting_orders must be true or false', 400)
    vendor = current_user()
    vendor.is_accepting_orders = accepting
    vendor.save()
    return jsonify(vendor.to_json()), 200


@vendor_bp.route('/menu')
def my_menu():
    items = FoodItem.for_vendor(current_user())
    return jsonify({'items': [i.to_json() for i in items]}), 200


@vendor_bp.route('/menu', methods=['POST'])
def add_item():
    data = request.get_json(silent=True) or {}
    item = FoodItem(
        vendor=current_user(),
        food_item_name=(data.get('name') or '').strip(),
        food_item_description=data.get('description'),
        food_item_price=data.get('price'),
        food_item_image_url=data.get('image_url'),
    )
    item.save()
    return jsonify(item.to_json()), 201


@vendor_bp.route('/menu/<item_id>', methods=['PATCH'])
def edit_item(item_id):
    item = _own_item(item_id)
    data = request.get_json(silent=True) or {}
    for field, attr in (('name', 'food_item_name'),
                        ('description', 'food_item_description'),
                        ('price', 'food_item_price'),
                        ('image_url', 'food_item_image_url')):
        if field in data:
            setattr(item, attr, data[field])
    item.save()
    return jsonify(item.to_json()), 200


@vendor_bp.route('/menu/<item_id>/availability', methods=['PATCH'])
def set_availability(item_id):
    item = _own_item(item_id)
    available = (request.get_json(silent=True) or {}).get('available')
    if not isinstance(available, bool):
        raise RuleViolation('available must be true or false', 400)
    item.mark_available() if available else item.mark_sold_out()
    return jsonify(item.to_json()), 200


@vendor_bp.route('/orders')
def incoming_orders():
    statuses = request.args.getlist('status') or None
    orders = FoodOrder.for_vendor(current_user(), statuses)
    return jsonify({'orders': [o.to_json() for o in orders]}), 200


@vendor_bp.route('/orders/<order_id>/status', methods=['PATCH'])
def advance_order(order_id):
    order = _own_order(order_id)
    data = request.get_json(silent=True) or {}
    to_status = data.get('status')
    reason = (data.get('reason') or '').strip()

    # A status the system has never heard of is a malformed request (400), not
    # a rule refusing a legal move in the wrong state (409).
    if to_status not in ORDER_STATUSES:
        raise RuleViolation(
            'status must be one of %s' % ', '.join(ORDER_STATUSES), 400)

    if to_status == 'Rejected':
        if not reason:
            raise RuleViolation(
                'A rejection needs a reason the diner can read', 400)
        order.rejection_reason = reason

    # The guard lives in the model, not here (TMA Q3c).
    order.apply_transition(to_status, actor=current_user())

    if to_status == 'PendingCollection':
        Notification.ready(order)
    elif to_status == 'Rejected':
        Notification.rejected(order, reason)
        payment = Payment.for_order(order)
        if payment:
            payment.mark_refunded()

    return jsonify(order.to_json()), 200


@vendor_bp.route('/dashboard')
def dashboard():
    vendor = current_user()
    return jsonify({
        'sales': FoodOrder.daily_sales(vendor),
        'top_items': FoodOrder.top_items(vendor),
        'sold_out': [i.to_json() for i in FoodItem.sold_out_for(vendor)],
    }), 200
