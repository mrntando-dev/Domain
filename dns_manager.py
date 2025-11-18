import requests
import json
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class DNSManager:
    """Manage DNS records across providers"""
    
    def __init__(self, config):
        self.config = config
        self.providers = config.get('DNS_PROVIDERS', {})
    
    def create_dns_record(self, subdomain: str, tld: str, target_ip: str, record_type: str = 'A') -> bool:
        """Create DNS record in Cloudflare"""
        try:
            cloudflare = self.providers.get('cloudflare', {})
            api_token = cloudflare.get('api_token')
            zone_id = cloudflare.get('zone_ids', {}).get(tld)
            
            if not api_token or not zone_id:
                logger.warning(f"DNS provider not configured for {tld}")
                return False
            
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'type': record_type,
                'name': subdomain,
                'content': target_ip,
                'ttl': 120,
                'proxied': True  # Enable Cloudflare proxy for security
            }
            
            url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
            response = requests.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"DNS record created: {subdomain}.{tld}")
                return True
            else:
                logger.error(f"Failed to create DNS record: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"DNS creation error: {str(e)}")
            return False
    
    def update_dns_record(self, subdomain: str, tld: str, target_ip: str, record_id: str) -> bool:
        """Update existing DNS record"""
        try:
            cloudflare = self.providers.get('cloudflare', {})
            api_token = cloudflare.get('api_token')
            zone_id = cloudflare.get('zone_ids', {}).get(tld)
            
            if not api_token or not zone_id:
                return False
            
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'type': 'A',
                'name': subdomain,
                'content': target_ip,
                'ttl': 120,
                'proxied': True
            }
            
            url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}'
            response = requests.put(url, headers=headers, json=data, timeout=10)
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"DNS update error: {str(e)}")
            return False
    
    def delete_dns_record(self, tld: str, record_id: str) -> bool:
        """Delete DNS record"""
        try:
            cloudflare = self.providers.get('cloudflare', {})
            api_token = cloudflare.get('api_token')
            zone_id = cloudflare.get('zone_ids', {}).get(tld)
            
            if not api_token or not zone_id:
                return False
            
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            
            url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}'
            response = requests.delete(url, headers=headers, timeout=10)
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"DNS deletion error: {str(e)}")
            return False
    
    def list_dns_records(self, tld: str) -> List[Dict]:
        """List all DNS records for a domain"""
        try:
            cloudflare = self.providers.get('cloudflare', {})
            api_token = cloudflare.get('api_token')
            zone_id = cloudflare.get('zone_ids', {}).get(tld)
            
            if not api_token or not zone_id:
                return []
            
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            
            url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json().get('result', [])
            return []
            
        except Exception as e:
            logger.error(f"DNS list error: {str(e)}")
            return []
