# src/name_address_validator/validators/address_validator.py
"""
Complete Working USPS Address Validator using the working GET method with Method 4 authentication
Enhanced with comprehensive validation helpers and business/residential classification
"""

import requests
import json
import time
import re
from typing import Dict, Optional, Tuple, List

class USPSAddressValidator:
    """Enhanced USPS validator with comprehensive validation helpers"""
    
    # US States for validation
    US_STATES = {
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
    }
    
    def __init__(self, client_id: str, client_secret: str, debug_callback=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.debug_callback = debug_callback or (lambda msg: print(msg))
        
        # API endpoints
        self.auth_url = 'https://apis.usps.com/oauth2/v3/token'
        self.validate_url = 'https://apis.usps.com/addresses/v3/address'
        
        # Token storage
        self._access_token = None
        self._token_expires_at = 0
        
        self._log("🔧 USPS validator initialized")
        if self.client_id:
            self._log(f"🔧 Client ID: {self.client_id[:8]}...{self.client_id[-4:]}")
    
    def _log(self, message: str):
        """Log debug messages"""
        try:
            self.debug_callback(message, "USPS", "INFO")
        except:
            print(message)
    
    def is_configured(self) -> bool:
        """Check if credentials are available"""
        configured = bool(self.client_id and self.client_secret)
        self._log(f"🔧 Configuration check: {'✅ Configured' if configured else '❌ Missing credentials'}")
        return configured
    
    def get_access_token(self) -> Optional[str]:
        """Get access token using Method 4 (credentials in body)"""
        
        # Check cached token
        if (self._access_token and 
            time.time() < (self._token_expires_at - 300)):
            self._log("🔧 Using cached token")
            return self._access_token
        
        # Get new token using Method 4
        self._log("🔧 Requesting new token using Method 4...")
        
        try:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'User-Agent': 'Enterprise-Validator-App/2.0'
            }
            
            # Method 4: Credentials in body (this works!)
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'addresses'
            }
            
            self._log(f"📤 POST {self.auth_url}")
            
            response = requests.post(
                self.auth_url,
                headers=headers,
                data=data,
                timeout=15
            )
            
            self._log(f"📥 Auth Status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                self._access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                self._token_expires_at = time.time() + expires_in
                
                self._log(f"✅ Token obtained, expires in {expires_in} seconds")
                
                return self._access_token
            else:
                self._log(f"❌ Auth failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self._log(f"❌ Auth error: {e}")
            return None
    
    def validate_address(self, address_data: Dict) -> Dict:
        """
        Validate address using USPS API with GET method
        
        Args:
            address_data: Dict with keys: street_address, city, state, zip_code
            
        Returns:
            Dict with validation results
        """
        
        self._log("🏠 Starting address validation...")
        
        # Check configuration
        if not self.is_configured():
            return {
                'success': False,
                'error': 'USPS API not configured',
                'deliverable': False
            }
        
        # Get token
        access_token = self.get_access_token()
        if not access_token:
            return {
                'success': False,
                'error': 'Failed to get access token',
                'deliverable': False
            }
        
        # Extract and validate address components
        street_address = address_data.get('street_address', '').strip()
        city = address_data.get('city', '').strip()
        state = address_data.get('state', '').strip().upper()
        zip_code = str(address_data.get('zip_code', '')).strip()
        
        self._log(f"📍 Input address: {street_address}, {city}, {state} {zip_code}")
        
        # Basic validation
        if not all([street_address, city, state, zip_code]):
            missing = []
            if not street_address: missing.append('street_address')
            if not city: missing.append('city')
            if not state: missing.append('state')
            if not zip_code: missing.append('zip_code')
            
            error_msg = f"Missing required fields: {', '.join(missing)}"
            self._log(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'deliverable': False
            }
        
        # Parse street address for apartment/unit
        street_parts = self._parse_street_address(street_address)
        self._log(f"📍 Parsed - Street: '{street_parts['street']}', Unit: '{street_parts['unit']}'")
        
        # Build query parameters for GET request
        params = {
            'streetAddress': street_parts['street'].upper(),
            'city': city.upper(),
            'state': state.upper(),
            'ZIPCode': zip_code[:5]  # First 5 digits only
        }
        
        # Add unit if present
        if street_parts['unit']:
            params['secondaryAddress'] = street_parts['unit'].upper()
        
        # Add ZIP+4 if present
        if '-' in zip_code and len(zip_code.split('-')) == 2:
            zip_plus4 = zip_code.split('-')[1]
            if len(zip_plus4) == 4 and zip_plus4.isdigit():
                params['ZIPPlus4'] = zip_plus4
                self._log(f"📍 Added ZIP+4: {zip_plus4}")
        
        self._log(f"📤 GET {self.validate_url}")
        
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'User-Agent': 'Enterprise-Validator-App/2.0'
            }
            
            # Use GET with query parameters (this is the fix!)
            response = requests.get(
                self.validate_url,
                headers=headers,
                params=params,
                timeout=15
            )
            
            self._log(f"📥 Validation Status: {response.status_code}")
            
            if response.status_code == 200:
                return self._parse_success_response(response.json())
                
            elif response.status_code == 400:
                try:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get('error', {}).get('message', 'Invalid address format')
                except:
                    error_msg = 'Invalid address format'
                
                self._log(f"❌ 400 Bad Request: {error_msg}")
                return {
                    'success': False,
                    'error': 'Invalid address format',
                    'details': error_msg,
                    'deliverable': False
                }
                
            elif response.status_code == 401:
                # Token expired, clear cache
                self._access_token = None
                self._token_expires_at = 0
                self._log("❌ 401 Unauthorized - token expired")
                return {
                    'success': False,
                    'error': 'Authentication failed',
                    'details': 'Token expired, try again',
                    'deliverable': False
                }
                
            elif response.status_code == 404:
                self._log("❌ 404 Not Found - address not in USPS database")
                return {
                    'success': False,
                    'error': 'Address not found',
                    'details': 'Address not found in USPS database',
                    'deliverable': False
                }
                
            else:
                self._log(f"❌ HTTP {response.status_code}: {response.text}")
                return {
                    'success': False,
                    'error': f'API error: HTTP {response.status_code}',
                    'details': response.text[:200] if response.text else 'Unknown error',
                    'deliverable': False
                }
                
        except requests.exceptions.Timeout:
            self._log("❌ Request timeout")
            return {
                'success': False,
                'error': 'Request timeout',
                'details': 'USPS API did not respond in time',
                'deliverable': False
            }
        except requests.exceptions.ConnectionError:
            self._log("❌ Connection error")
            return {
                'success': False,
                'error': 'Connection error',
                'details': 'Could not connect to USPS API',
                'deliverable': False
            }
        except Exception as e:
            self._log(f"❌ Unexpected error: {e}")
            return {
                'success': False,
                'error': 'Unexpected error',
                'details': str(e),
                'deliverable': False
            }
    
    def _parse_street_address(self, address: str) -> Dict[str, str]:
        """Parse street address into main and unit components"""
        if not address:
            return {'street': '', 'unit': ''}
        
        # Normalize whitespace
        address = ' '.join(address.split())
        
        # Common unit patterns at end of address
        unit_patterns = [
            r'\s+(apartment|apt|suite|ste|unit|#)\s*\.?\s*([a-z0-9\-]+)$',
            r'\s+(building|bldg|floor|fl)\s*\.?\s*([a-z0-9\-]+)$',
            r'\s+([0-9]+[a-z]{1,2})$',  # Like "4B", "12A"
            r'\s+#([a-z0-9\-]+)$'       # "#123"
        ]
        
        for pattern in unit_patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                unit_start = match.start()
                street_part = address[:unit_start].strip()
                unit_part = match.group(0).strip()
                return {'street': street_part, 'unit': unit_part}
        
        return {'street': address, 'unit': ''}
    
    def _parse_success_response(self, response_data: Dict) -> Dict:
        """Parse successful USPS response - FIXED for actual API v3 format"""
        
        self._log("📋 Parsing USPS response...")
        
        # USPS API v3 returns data in this format:
        # {
        #   "address": { ... },
        #   "additionalInfo": { "DPVConfirmation": "Y", ... },
        #   "matches": [ ... ]
        # }
        
        if not response_data.get('address'):
            self._log("❌ No address data in response")
            return {
                'success': False,
                'error': 'No address data in response',
                'deliverable': False
            }
        
        address = response_data.get('address', {})
        additional_info = response_data.get('additionalInfo', {})
        
        # ✅ FIXED: Determine validity based on DPVConfirmation
        # DPVConfirmation "Y" means the address is deliverable
        # DPVConfirmation "N" means not deliverable  
        # DPVConfirmation "D" means address is deliverable but with unit missing
        dpv_confirmation = additional_info.get('DPVConfirmation', '')
        is_deliverable = dpv_confirmation in ['Y', 'D']  # Y = deliverable, D = deliverable but missing unit
        
        self._log(f"📋 DPVConfirmation: {dpv_confirmation}")
        self._log(f"📋 Address deliverable: {is_deliverable}")
        
        # Build standardized address
        street_address = address.get('streetAddress', '')
        if address.get('secondaryAddress'):
            street_address += f" {address.get('secondaryAddress')}"
        
        # Format ZIP code
        zip_code = address.get('ZIPCode', '')
        if address.get('ZIPPlus4'):
            zip_code += f"-{address.get('ZIPPlus4')}"
        
        standardized = {
            'street_address': street_address.strip(),
            'city': address.get('city', ''),
            'state': address.get('state', ''),
            'zip_code': zip_code
        }
        
        self._log(f"📋 Standardized: {standardized['street_address']}, {standardized['city']}, {standardized['state']} {standardized['zip_code']}")
        
        # Extract metadata from additionalInfo
        metadata = {
            'business': additional_info.get('business', 'N') == 'Y',
            'vacant': additional_info.get('vacant', 'N') == 'Y',
            'centralized': additional_info.get('centralDeliveryPoint', 'N') == 'Y',
            'carrier_route': additional_info.get('carrierRoute', ''),
            'delivery_point': additional_info.get('deliveryPoint', ''),
            'dpv_confirmation': dpv_confirmation,
            'dpv_cmra': additional_info.get('DPVCMRA', '')
        }
        
        self._log(f"📋 Metadata: Business={metadata['business']}, Vacant={metadata['vacant']}, Centralized={metadata['centralized']}")
        
        # Calculate confidence based on match quality
        matches = response_data.get('matches', [])
        confidence = 0.6  # Default
        
        if matches:
            match_code = matches[0].get('code', '')
            if match_code == '31':  # Exact match
                confidence = 0.98
            elif match_code in ['32', '33']:  # Good matches
                confidence = 0.85
            elif dpv_confirmation == 'Y':
                confidence = 0.75
        
        result = {
            'success': True,
            'valid': is_deliverable,
            'deliverable': is_deliverable,
            'standardized': standardized,
            'metadata': metadata,
            'confidence': confidence,
            'validation_method': 'usps_api_v3_get_method_fixed',
            'dpv_confirmation': dpv_confirmation,
            'match_info': matches[0] if matches else {}
        }
        
        self._log(f"✅ Validation complete - deliverable: {is_deliverable}")
        return result
    
    # Additional validation helpers for basic field validation
    @staticmethod
    def validate_address_field(address: str, debug_callback=None) -> Tuple[List[str], List[str]]:
        """Validate street address with debug logging"""
        start_time = time.time()
        errors = []
        warnings = []
        
        if debug_callback:
            debug_callback(f"Starting address validation (length: {len(address) if address else 0})")
        
        if not address or not address.strip():
            errors.append("Street address is required")
            if debug_callback:
                debug_callback("Address validation failed - empty field")
            return errors, warnings
        
        address = address.strip()
        
        if len(address) > 100:
            errors.append("Street address cannot exceed 100 characters")
            if debug_callback:
                debug_callback(f"Address validation failed - too long (length: {len(address)})")
        
        if not re.search(r'\d', address):
            warnings.append("Street address should contain a house number")
            if debug_callback:
                debug_callback("Address warning - no house number detected")
        
        # Check for PO Box
        if re.search(r'\b(po|p\.o\.)\s*box\b', address, re.IGNORECASE):
            warnings.append("PO Box addresses may have delivery limitations")
            if debug_callback:
                debug_callback("PO Box detected in address")
        
        duration_ms = int((time.time() - start_time) * 1000)
        if debug_callback:
            if errors:
                debug_callback(f"Address validation completed with {len(errors)} errors ({duration_ms}ms)")
            else:
                debug_callback(f"Address validation passed ({duration_ms}ms)")
        
        return errors, warnings
    
    @staticmethod
    def validate_city_field(city: str, debug_callback=None) -> Tuple[List[str], List[str]]:
        """Validate city with debug logging"""
        start_time = time.time()
        errors = []
        warnings = []
        
        if debug_callback:
            debug_callback("Starting city validation")
        
        if not city or not city.strip():
            errors.append("City is required")
            return errors, warnings
        
        city = city.strip()
        
        if len(city) > 50:
            errors.append("City cannot exceed 50 characters")
        
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", city):
            errors.append("City can only contain letters, spaces, hyphens, apostrophes, and periods")
        
        duration_ms = int((time.time() - start_time) * 1000)
        if debug_callback:
            debug_callback(f"City validation completed ({duration_ms}ms)")
        
        return errors, warnings
    
    @staticmethod
    def validate_state_field(state: str, debug_callback=None) -> Tuple[List[str], List[str]]:
        """Validate state with debug logging"""
        start_time = time.time()
        errors = []
        warnings = []
        
        if debug_callback:
            debug_callback(f"Starting state validation (state: {state})")
        
        if not state or not state.strip():
            errors.append("State is required")
            return errors, warnings
        
        state = state.strip().upper()
        
        if len(state) != 2:
            errors.append("State must be a 2-letter code (e.g., CA, NY, TX)")
        elif state not in USPSAddressValidator.US_STATES:
            errors.append(f"'{state}' is not a valid US state code")
            if debug_callback:
                debug_callback(f"Invalid state code provided: {state}")
        
        duration_ms = int((time.time() - start_time) * 1000)
        if debug_callback:
            debug_callback(f"State validation completed ({duration_ms}ms)")
        
        return errors, warnings
    
    @staticmethod
    def validate_zip_code_field(zip_code: str, debug_callback=None) -> Tuple[List[str], List[str]]:
        """Validate ZIP code with debug logging"""
        start_time = time.time()
        errors = []
        warnings = []
        
        if debug_callback:
            debug_callback("Starting ZIP code validation")
        
        if not zip_code or not zip_code.strip():
            errors.append("ZIP code is required")
            return errors, warnings
        
        zip_code = zip_code.strip()
        
        if not re.match(r'^\d{5}(-\d{4})?$', zip_code):
            errors.append("ZIP code must be 5 digits or 5+4 format (e.g., 12345 or 12345-6789)")
        
        if zip_code == "00000" or zip_code == "00000-0000":
            errors.append("ZIP code cannot be all zeros")
            if debug_callback:
                debug_callback("Invalid ZIP code - all zeros")
        
        duration_ms = int((time.time() - start_time) * 1000)
        if debug_callback:
            debug_callback(f"ZIP validation completed ({duration_ms}ms)")
        
        return errors, warnings