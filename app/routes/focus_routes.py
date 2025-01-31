from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.schemas.camera_schema import CameraSchema
from app.schemas.focus_schema import FocusMoveSchema
from app.services.onvif_service import focus_move

focus_bp = Blueprint('focus', __name__)


@focus_bp.route('/move', methods=['POST'])
def focus_move_onvif_camera():
    data = request.json
    
    schema = CameraSchema()

    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    ip = validated_data['ip']
    username = validated_data['username']
    password = validated_data['password']

    schema = FocusMoveSchema()

    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    
    focus_speed = validated_data['focus_speed']
    
    # Call service function
    response = focus_move(ip, username, password, focus_speed)
    if "error" in response:
        return jsonify(response), response[1] if isinstance(response, tuple) else 500
    
    return jsonify(response), 200
