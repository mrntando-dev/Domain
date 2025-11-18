import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import threading

class SubdomainManager:
    """Manage subdomains from JSON files"""
    
    def __init__(self, domains_dir='domains'):
        self.domains_dir = domains_dir
        self.subdomains_file = os.path.join(domains_dir, 'subdomains.json')
        self.config_file = os.path.join(domains_dir, 'domain_config.json')
        self.lock = threading.Lock()
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Create domain files if they don't exist"""
        os.makedirs(self.domains_dir, exist_ok=True)
        
        if not os.path.exists(self.subdomains_file):
            self._save_json(self.subdomains_file, {})
        
        if not os.path.exists(self.config_file):
            default_config = {
                'default_target': '0.0.0.0',
                'ssl_enabled': True,
                'auto_dns': True,
                'allowed_tlds': ['net', 'com', 'zw', 'dev', 'id']
            }
            self._save_json(self.config_file, default_config)
    
    def _load_json(self, filepath):
        """Load JSON file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_json(self, filepath, data):
        """Save JSON file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_all_subdomains(self) -> Dict:
        """Get all subdomains"""
        return self._load_json(self.subdomains_file)
    
    def get_subdomain(self, subdomain: str, tld: str) -> Optional[Dict]:
        """Get specific subdomain"""
        subdomains = self.get_all_subdomains()
        key = f"{subdomain}.{tld}"
        return subdomains.get(key)
    
    def create_subdomain(self, subdomain: str, tld: str, config: Dict) -> bool:
        """Create new subdomain"""
        with self.lock:
            subdomains = self.get_all_subdomains()
            key = f"{subdomain}.{tld}"
            
            if key in subdomains:
                return False
            
            subdomains[key] = {
                'subdomain': subdomain,
                'tld': tld,
                'target': config.get('target', '0.0.0.0'),
                'record_type': config.get('record_type', 'A'),
                'ssl_enabled': config.get('ssl_enabled', True),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'status': 'active',
                'dns_record_id': config.get('dns_record_id'),
                'metadata': config.get('metadata', {})
            }
            
            self._save_json(self.subdomains_file, subdomains)
            return True
    
    def update_subdomain(self, subdomain: str, tld: str, config: Dict) -> bool:
        """Update subdomain"""
        with self.lock:
            subdomains = self.get_all_subdomains()
            key = f"{subdomain}.{tld}"
            
            if key not in subdomains:
                return False
            
            subdomains[key].update(config)
            subdomains[key]['updated_at'] = datetime.utcnow().isoformat()
            
            self._save_json(self.subdomains_file, subdomains)
            return True
    
    def delete_subdomain(self, subdomain: str, tld: str) -> bool:
        """Delete subdomain"""
        with self.lock:
            subdomains = self.get_all_subdomains()
            key = f"{subdomain}.{tld}"
            
            if key not in subdomains:
                return False
            
            del subdomains[key]
            self._save_json(self.subdomains_file, subdomains)
            return True
    
    def search_subdomains(self, query: str) -> List[Dict]:
        """Search subdomains"""
        subdomains = self.get_all_subdomains()
        results = []
        
        for key, value in subdomains.items():
            if query.lower() in key.lower() or query.lower() in str(value).lower():
                results.append(value)
        
        return results
    
    def get_config(self) -> Dict:
        """Get domain configuration"""
        return self._load_json(self.config_file)
    
    def update_config(self, config: Dict) -> bool:
        """Update domain configuration"""
        with self.lock:
            current_config = self.get_config()
            current_config.update(config)
            self._save_json(self.config_file, current_config)
            return True
