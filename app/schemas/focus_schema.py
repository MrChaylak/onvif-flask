from marshmallow import Schema, fields, ValidationError, validates, EXCLUDE

class FocusMoveSchema(Schema):
    focus_speed = fields.Float(required=True, error_messages={"required": "focusSpeed is required"})  # Default to 0.0 if not provided

    class Meta:
        unknown = EXCLUDE  # Ignore any extra fields

    @validates('focus_speed')
    def validate_focus_speed(self, value):
        # Example: Validate focus_speed is within a valid range
        if not -1.0 <= value <= 1.0:
            raise ValidationError('focusSpeed must be between -1.0 and 1.0')
