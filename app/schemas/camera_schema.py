from marshmallow import Schema, fields, ValidationError, validates, EXCLUDE
import ipaddress

class CameraSchema(Schema):
    ip = fields.String(required=True, error_messages={"required": "IP is required"})
    username = fields.String(required=True, error_messages={"required": "Username is required"})
    password = fields.String(required=True, error_messages={"required": "Password is required"})

    class Meta:
        unknown = EXCLUDE  # Ignore any extra fields

    @validates('ip')
    def validate_ip(self, value):
        try:
            ipaddress.IPv4Address(value)  # Check if it's a valid IPv4 address
        except ipaddress.AddressValueError:
            raise ValidationError('Invalid IP address format. Expected a valid IPv4 address.')

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
        