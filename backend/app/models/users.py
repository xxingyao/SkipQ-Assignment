from app.extensions import db


class User(db.Document):
    """Base account. Diner and Vendor inherit from this, so email is unique
    across both roles (GBA Q4a feature F6)."""

    meta = {'collection': 'appUsers', 'allow_inheritance': True}

    email = db.EmailField(max_length=120, required=True, unique=True)
    password = db.StringField(required=True)
    name = db.StringField(max_length=80)

    @staticmethod
    def getUser(email):
        return User.objects(email=email).first()

    @staticmethod
    def getUserById(user_id):
        return User.objects(pk=user_id).first()

    @property
    def role(self):
        return type(self).__name__


class Diner(User):
    pass


class Vendor(User):
    """A stall or restaurant. is_accepting_orders implements US-12, which the
    GBA class diagram never captured."""

    stall_name = db.StringField(max_length=80, required=True)
    venue_type = db.StringField(choices=('Food court', 'Restaurant'))
    is_accepting_orders = db.BooleanField(default=True)

    @staticmethod
    def open_stalls():
        return Vendor.objects(is_accepting_orders=True)

    @staticmethod
    def all_stalls():
        return Vendor.objects()

    def to_json(self):
        return {
            'id': str(self.id),
            'stall_name': self.stall_name,
            'venue_type': self.venue_type,
            'is_accepting_orders': self.is_accepting_orders,
        }
