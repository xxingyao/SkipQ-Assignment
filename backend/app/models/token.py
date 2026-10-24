from datetime import datetime

from app.extensions import db


class UserTokens(db.Document):
    """API token issued by /api/user/gettoken and checked on every protected
    endpoint. Adapted from the lab: the email field was 30 characters, too short
    for the addresses SkipQ seeds."""

    meta = {'collection': 'tokens'}

    email = db.EmailField(max_length=120, required=True, unique=True)
    token = db.StringField(required=True)
    created_at = db.DateTimeField(default=datetime.utcnow)

    @staticmethod
    def getToken(email):
        return UserTokens.objects(email=email).first()

    @staticmethod
    def createToken(email, token):
        existing = UserTokens.getToken(email)
        if not existing:
            existing = UserTokens(email=email, token=token).save()
        return existing
