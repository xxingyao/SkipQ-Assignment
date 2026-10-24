from app.extensions import db
from app.models.users import Vendor


class FoodItem(db.Document):
    """A menu item belonging to one vendor (GBA Q4a feature F1)."""

    meta = {'collection': 'foodItems'}

    vendor = db.ReferenceField(Vendor, required=True, reverse_delete_rule=db.CASCADE)
    food_item_name = db.StringField(min_length=1, max_length=80, required=True)
    food_item_description = db.StringField(max_length=500)
    food_item_price = db.DecimalField(required=True, min_value=0.01,
                                      max_value=9999, precision=2)
    food_item_image_url = db.StringField()
    food_item_availability = db.BooleanField(default=True)

    @staticmethod
    def for_vendor(vendor):
        return FoodItem.objects(vendor=vendor)

    @staticmethod
    def available_for_vendor(vendor):
        return FoodItem.objects(vendor=vendor, food_item_availability=True)

    @staticmethod
    def sold_out_for(vendor):
        return FoodItem.objects(vendor=vendor, food_item_availability=False)

    def mark_sold_out(self):
        self.food_item_availability = False
        return self.save()

    def mark_available(self):
        self.food_item_availability = True
        return self.save()

    def is_orderable(self):
        """Both the item and its stall must be open. One place owns this rule."""
        return self.food_item_availability and self.vendor.is_accepting_orders

    def to_json(self):
        return {
            'id': str(self.id),
            'vendor_id': str(self.vendor.id),
            'name': self.food_item_name,
            'description': self.food_item_description,
            'price': float(self.food_item_price),
            'image_url': self.food_item_image_url,
            'available': self.food_item_availability,
            'orderable': self.is_orderable(),
        }
