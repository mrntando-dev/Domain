from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_cors import CORS
import logging
import os
from config import config
from models import SubdomainManager
from security import SecurityManager, require_api_key, validate_request
from dns_manager import DNSManager

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'production')
app.config.from_object(config[env])

# Initialize extensions
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[app.config['RATE_LIMIT']],
    storage_uri="memory://"
)

cache = Cache(app)
CORS(app, origins=app.config['CORS_ORIGINS'])

# Initialize managers
subdomain_manager = SubdomainManager()
security_manager = SecurityManager()
dns_manager = DNSManager(app.config)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== Routes ====================

@app.route('/')
@cache.cached(timeout=300)
def index():
    """Home page"""
    return render_template('index.html', 
                         supported_tlds=app.config['SUPPORTED_TLDS'],
                         base_domains=app.config['BASE_DOMAINS'])

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Ntando Store Subdomain Manager',
        'version': '1.0.0'
    }), 200

# ==================== API Routes ====================

@app.route('/api/subdomains', methods=['GET'])
@limiter.limit("30 per minute")
def get_subdomains():
    """Get all subdomains"""
    try:
        tld = request.args.get('tld')
        query = request.args.get('q')
        
        if query:
            subdomains = subdomain_manager.search_subdomains(query)
        else:
            all_subdomains = subdomain_manager.get_all_subdomains()
            if tld:
                subdomains = [v for k, v in all_subdomains.items() if v['tld'] == tld]
            else:
                subdomains = list(all_subdomains.values())
        
        return jsonify({
            'success': True,
            'count': len(subdomains),
            'subdomains': subdomains
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching subdomains: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/subdomains/<tld>/<subdomain>', methods=['GET'])
@limiter.limit("60 per minute")
def get_subdomain(tld, subdomain):
    """Get specific subdomain"""
    try:
        subdomain = security_manager.sanitize_subdomain(subdomain)
        result = subdomain_manager.get_subdomain(subdomain, tld)
        
        if result:
            return jsonify({'success': True, 'subdomain': result}), 200
        else:
            return jsonify({'success': False, 'error': 'Subdomain not found'}), 404
            
    except Exception as e:
        logger.error(f"Error fetching subdomain: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/subdomains', methods=['POST'])
@limiter.limit("10 per minute")
@validate_request
def create_subdomain():
    """Create new subdomain"""
    try:
        data = request.get_json()
        
        # Validate required fields
        subdomain = data.get('subdomain')
        tld = data.get('tld')
        
        if not subdomain or not tld:
            return jsonify({'success': False, 'error': 'Subdomain and TLD required'}), 400
        
        # Sanitize and validate
        subdomain = security_manager.sanitize_subdomain(subdomain)
        
        if not security_manager.validate_subdomain(subdomain):
            return jsonify({'success': False, 'error': 'Invalid subdomain format'}), 400
        
        if tld not in app.config['BASE_DOMAINS']:
            return jsonify({'success': False, 'error': 'Invalid TLD'}), 400
        
        # Check if subdomain already exists
        if subdomain_manager.get_subdomain(subdomain, tld):
            return jsonify({'success': False, 'error': 'Subdomain already exists'}), 409
        
        # Prepare configuration
        target_ip = data.get('target', '0.0.0.0')
        record_type = data.get('record_type', 'A')
        ssl_enabled = data.get('ssl_enabled', True)
        
        # Create DNS record if auto_dns is enabled
        dns_record_id = None
        config = subdomain_manager.get_config()
        
        if config.get('auto_dns', True):
            full_subdomain = f"{subdomain}.{app.config['BASE_DOMAINS'][tld]}"
            if dns_manager.create_dns_record(full_subdomain, tld, target_ip, record_type):
                logger.info(f"DNS record created for {full_subdomain}")
        
        # Create subdomain in database
        subdomain_config = {
            'target': target_ip,
            'record_type': record_type,
            'ssl_enabled': ssl_enabled,
            'dns_record_id': dns_record_id,
            'metadata': data.get('metadata', {})
        }
        
        if subdomain_manager.create_subdomain(subdomain, tld, subdomain_config):
            result = subdomain_manager.get_subdomain(subdomain, tld)
            return jsonify({
                'success': True,
                'message': 'Subdomain created successfully',
                'subdomain': result
            }), 201
        else:
            return jsonify({'success': False, 'error': 'Failed to create subdomain'}), 500
            
    except Exception as e:
        logger.error(f"Error creating subdomain: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/subdomains/<tld>/<subdomain>', methods=['PUT'])
@limiter.limit("20 per minute")
@validate_request
def update_subdomain(tld, subdomain):
    """Update subdomain"""
    try:
        subdomain = security_manager.sanitize_subdomain(subdomain)
        data = request.get_json()
        
        # Check if subdomain exists
        if not subdomain_manager.get_subdomain(subdomain, tld):
            return jsonify({'success': False, 'error': 'Subdomain not found'}), 404
        
        # Update configuration
        update_config = {}
        if 'target' in data:
            update_config['target'] = data['target']
        if 'ssl_enabled' in data:
            update_config['ssl_enabled'] = data['ssl_enabled']
        if 'status' in data:
            update_config['status'] = data['status']
        if 'metadata' in data:
            update_config['metadata'] = data['metadata']
        
        if subdomain_manager.update_subdomain(subdomain, tld, update_config):
            result = subdomain_manager.get_subdomain(subdomain, tld)
            return jsonify({
                'success': True,
                'message': 'Subdomain updated successfully',
                'subdomain': result
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to update subdomain'}), 500
            
    except Exception as e:
        logger.error(f"Error updating subdomain: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/subdomains/<tld>/<subdomain>', methods=['DELETE'])
@limiter.limit("10 per minute")
def delete_subdomain(tld, subdomain):
    """Delete subdomain"""
    try:
        subdomain = security_manager.sanitize_subdomain(subdomain)
        
        # Check if subdomain exists
        subdomain_data = subdomain_manager.get_subdomain(subdomain, tld)
        if not subdomain_data:
            return jsonify({'success': False, 'error': 'Subdomain not found'}), 404
        
        # Delete DNS record if exists
        if subdomain_data.get('dns_record_id'):
            dns_manager.delete_dns_record(tld, subdomain_data['dns_record_id'])
        
        # Delete from database
        if subdomain_manager.delete_subdomain(subdomain, tld):
            return jsonify({
                'success': True,
                'message': 'Subdomain deleted successfully'
            }), 200
        else:
            return jsonify({'success': False, 'error': 'Failed to delete subdomain'}), 500
            
    except Exception as e:
        logger.error(f"Error deleting subdomain: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get configuration"""
    try:
        config = subdomain_manager.get_config()
        return jsonify({'success': True, 'config': config}), 200
    except Exception as e:
        logger.error(f"Error fetching config: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/stats', methods=['GET'])
@cache.cached(timeout=60)
def get_stats():
    """Get statistics"""
    try:
        subdomains = subdomain_manager.get_all_subdomains()
        
        stats = {
            'total_subdomains': len(subdomains),
            'by_tld': {},
            'by_status': {},
            'ssl_enabled': 0
        }
        
        for subdomain_data in subdomains.values():
            tld = subdomain_data['tld']
            status = subdomain_data.get('status', 'unknown')
            
            stats['by_tld'][tld] = stats['by_tld'].get(tld, 0) + 1
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            if subdomain_data.get('ssl_enabled'):
                stats['ssl_enabled'] += 1
        
        return jsonify({'success': True, 'stats': stats}), 200
        
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Resource not found'}), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

# ==================== Main ====================

if __name__ == '__main__':
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
