from datetime import datetime

from app.extensions import db
from app.models.users import Diner
from app.models.order import FoodOrder


class Notification(db.Document):
    meta = {'collection': 'notifications'}

    order = db.ReferenceField(FoodOrder, required=True)
    diner = db.ReferenceField(Diner, required=True)
    notification_message = db.StringField(required=True, max_length=200)
    notification_isread = db.BooleanField(default=False)
    created_at = db.DateTimeField(default=datetime.utcnow)

    @classmethod
    def ready(cls, order):
        return cls(order=order, diner=order.diner,
                   notification_message=(
                       f'Queue {order.queue_number} is ready for collection '
                       f'at {order.vendor.stall_name}')).save()

    @classmethod
    def rejected(cls, order, reason):
        return cls(order=order, diner=order.diner,
                   notification_message=(
                       f'{order.vendor.stall_name} could not fulfil your order: '
                       f'{reason}')).save()

    @staticmethod
    def unread_for(diner):
        return Notification.objects(
            diner=diner, notification_isread=False).order_by('-created_at')
        
    @staticmethod
    def mark_all_read(diner):
        """Marks this diner's unread notifications as read and returns how many
        were marked. Without something setting the flag, the unread list only
        ever grows, so a diner keeps seeing notices for orders already
        collected."""
        return Notification.objects(
            diner=diner, notification_isread=False).update(
                set__notification_isread=True)

    def to_json(self):
        return {
            'id': str(self.id),
            'order_id': str(self.order.id),
            'message': self.notification_message,
            'is_read': self.notification_isread,
            'created_at': self.created_at.isoformat(),
        }
