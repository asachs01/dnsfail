from flask import Blueprint, jsonify, current_app, request, send_from_directory
from datetime import datetime

api = Blueprint('api', __name__, url_prefix='/api/v1')

# Add root route to serve index.html
@api.route('/')
def index():
    return send_from_directory('webui/static', 'index.html')

@api.route('/status')
def get_status():
    counter = current_app.counter_instance
    if not counter:
        return jsonify({
            'error': 'Counter instance not initialized'
        }), 500
        
    duration = datetime.now() - counter.last_reset
    time_line1, time_line2 = counter.format_duration(duration)
    
    return jsonify({
        'status': 'ok',
        'last_reset': counter.last_reset.isoformat(),
        'uptime': {
            'total_seconds': int(duration.total_seconds()),
            'formatted': {
                'line1': time_line1,
                'line2': time_line2
            }
        }
    })

@api.route('/reset', methods=['POST'])
def reset_counter():
    counter = current_app.counter_instance
    if not counter:
        return jsonify({
            'error': 'Counter instance not initialized'
        }), 500
    
    counter.last_reset = datetime.now()
    return jsonify({
        'status': 'ok',
        'message': 'Counter reset successfully',
        'timestamp': counter.last_reset.isoformat()
    })

@api.route('/health')
def health_check():
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    }) 