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
        