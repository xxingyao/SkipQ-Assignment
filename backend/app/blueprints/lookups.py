from mongoengine.errors import ValidationError

from app.models.errors import NotFound


def find_or_404(model, raw_id, label):
    """A malformed id is a missing record, not a server fault."""
    try:
        found = model.objects(pk=raw_id).first()
    except ValidationError:
        found = None
    if not found:
        raise NotFound('No such %s' % label)
    return found
