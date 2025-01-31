from marshmallow import Schema, fields, ValidationError, validates, EXCLUDE

class PTZSchema(Schema):
    profile_token = fields.String(required=True, error_messages={"required": "profileToken is required"})
    pan_speed = fields.Float(required=False, missing=0.0)  # Default to 0.0 if not provided
    tilt_speed = fields.Float(required=False, missing=0.0)  # Default to 0.0 if not provided
    zoom_speed = fields.Float(required=False, missing=0.0)  # Default to 0.0 if not provided

    class Meta:
        unknown = EXCLUDE  # Ignore any extra fields

    @validates('profile_token')
    def validate_profile_token(self, value):
        if not value.strip():
            raise ValidationError('profileToken is required')

    @validates('pan_speed')
    def validate_pan_speed(self, value):
        # Example: Validate pan_speed is within a valid range
        if not -1.0 <= value <= 1.0:
            raise ValidationError('panSpeed must be between -1.0 and 1.0')

    @validates('tilt_speed')
    def validate_tilt_speed(self, value):
        # Example: Validate tilt_speed is within a valid range
        if not -1.0 <= value <= 1.0:
            raise ValidationError('tiltSpeed must be between -1.0 and 1.0')

    @validates('zoom_speed')
    def validate_zoom_speed(self, value):
        # Example: Validate zoom_speed is within a valid range
        if not -1.0 <= value <= 1.0:
            raise ValidationError('zoomSpeed must be between -1.0 and 1.0')
        