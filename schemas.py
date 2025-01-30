from marshmallow import Schema, fields, ValidationError, validates, EXCLUDE

class CameraSchema(Schema):
    ip = fields.String(required=True, error_messages={"required": "IP is required"})
    username = fields.String(required=True, error_messages={"required": "Username is required"})
    password = fields.String(required=True, error_messages={"required": "Password is required"})

    class Meta:
        unknown = EXCLUDE  # Ignore any extra fields

    @validates('ip')
    def validate_ip(self, value):
        # Example: Validate IP format (basic check)
        if not value.replace('.', '').isdigit():
            raise ValidationError('Invalid IP address')

    @validates('username')
    def validate_username(self, value):
        # Ensure username is not empty
        if not value.strip():  # Check if the string is empty or contains only whitespace
            raise ValidationError('Username cannot be empty')

    @validates('password')
    def validate_password(self, value):
        # Example: Validate password length
        if len(value) < 8:
            raise ValidationError('Password must be at least 8 characters long')


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


class FocusMoveSchema(Schema):
    focus_speed = fields.Float(required=True, error_messages={"required": "focusSpeed is required"})  # Default to 0.0 if not provided

    class Meta:
        unknown = EXCLUDE  # Ignore any extra fields

    @validates('focus_speed')
    def validate_focus_speed(self, value):
        # Example: Validate focus_speed is within a valid range
        if not -1.0 <= value <= 1.0:
            raise ValidationError('focusSpeed must be between -1.0 and 1.0')
