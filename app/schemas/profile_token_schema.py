from marshmallow import Schema, fields, ValidationError, validates, EXCLUDE

class ProfileTokenSchema(Schema):
    profile_token = fields.String(required=True, error_messages={"required": "profileToken is required"})

    class Meta:
        unknown = EXCLUDE  # Ignore any extra fields

    @validates('profile_token')
    def validate_profile_token(self, value):
        if not value.strip():
            raise ValidationError('profileToken is required')
        