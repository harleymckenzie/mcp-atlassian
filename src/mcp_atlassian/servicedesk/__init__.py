"""Service Desk API integration for mcp-atlassian - FIXED VERSION."""

import json
import logging
from typing import Any, Dict, List, Optional
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class ServiceDeskFetcher:
    """Service Desk API client wrapper."""
    
    def __init__(self, jira_config):
        """Initialize Service Desk client using existing Jira configuration."""
        self.config = jira_config
        self.base_url = jira_config.url.rstrip('/')
        
        # Handle different auth types
        if hasattr(jira_config, 'username') and hasattr(jira_config, 'api_token'):
            self.auth = HTTPBasicAuth(jira_config.username, jira_config.api_token)
        elif hasattr(jira_config, 'personal_token'):
            self.auth = HTTPBasicAuth('', jira_config.personal_token)
        else:
            raise ValueError("No valid authentication method found in Jira config")
            
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to Service Desk API."""
        url = f"{self.base_url}/rest/servicedeskapi/{endpoint}"
        
        # Add debugging
        logger.debug(f"Making {method} request to: {url}")
        if 'json' in kwargs:
            logger.debug(f"Request body: {json.dumps(kwargs['json'], indent=2)}")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                headers=self.headers,
                **kwargs
            )
            
            # Log response details for debugging
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            # If we get a 400, log the full error response
            if response.status_code == 400:
                logger.error(f"400 Bad Request. Response text: {response.text}")
                try:
                    error_json = response.json()
                    logger.error(f"Error JSON: {json.dumps(error_json, indent=2)}")
                except:
                    pass
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Service Desk API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
            raise
    
    def get_service_desks(self) -> List[Dict[str, Any]]:
        """Get all service desks."""
        return self._make_request('GET', 'servicedesk').get('values', [])
    
    def get_request_types(self, service_desk_id: str) -> List[Dict[str, Any]]:
        """Get request types for a service desk."""
        return self._make_request('GET', f'servicedesk/{service_desk_id}/requesttype').get('values', [])
    
    def get_organisations(self, service_desk_id: str) -> List[Dict[str, Any]]:
        """Get organisations for a service desk."""
        return self._make_request('GET', f'servicedesk/{service_desk_id}/organization').get('values', [])

    def get_organization_users(self, organization_id: str, start: int = 0, limit: int = 50) -> Dict[str, Any]:
        """Get users in a Service Desk organization.
        
        Args:
            organization_id: The organization ID
            start: Starting index for pagination (default: 0)
            limit: Maximum number of users to return (default: 50)
        
        Returns:
            Dict containing users list and pagination info
        """
        params = {
            'start': start,
            'limit': limit
        }
        
        return self._make_request('GET', f'organization/{organization_id}/user', params=params)

    def add_users_to_organization(self, organization_id: str, usernames: List[str]) -> Dict[str, Any]:
        """Add users to a Service Desk organization.
        
        Args:
            organization_id: The organization ID to add users to
            usernames: List of usernames/account IDs to add to the organization
        
        Returns:
            Dict containing the operation result
        """
        request_data = {
            "usernames": usernames
        }
        
        logger.info(f"Adding users {usernames} to organization {organization_id}")
        
        return self._make_request('POST', f'organization/{organization_id}/user', json=request_data)
    
    def get_request_type_fields(self, service_desk_id: str, request_type_id: str) -> List[Dict[str, Any]]:
        """Get request fields for a specific request type."""
        return self._make_request('GET', f'servicedesk/{service_desk_id}/requesttype/{request_type_id}/field').get('requestTypeFields', [])
    
    def create_customer_request(self, service_desk_id: str, request_type_id: str, 
                               summary: str, description: str,
                               request_field_values: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a Service Desk customer request using the proper Service Desk API."""
        
        # Build the request field values with summary and description
        field_values = {
            "summary": summary,
            "description": description
        }
        
        # Add any additional custom field values if provided
        if request_field_values:
            field_values.update(request_field_values)
        
        # Build the request data according to Service Desk API spec
        # CRITICAL: serviceDeskId and requestTypeId must be STRINGS, not integers
        request_data = {
            "serviceDeskId": str(service_desk_id),  # Ensure string
            "requestTypeId": str(request_type_id),  # Ensure string  
            "requestFieldValues": field_values
        }
        
        # Log the exact request data for debugging
        logger.info(f"Creating Service Desk request with data: {json.dumps(request_data, indent=2)}")
        
        # Use Service Desk API endpoint
        return self._make_request('POST', 'request', json=request_data)
    
    def update_request(self, issue_key: str, **fields) -> Dict[str, Any]:
        """Update a Service Desk request."""
        # Use Jira API for updates
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        update_data = {"fields": fields}
        
        logger.debug(f"Updating issue {issue_key} with data: {json.dumps(update_data, indent=2)}")
        
        response = requests.put(
            url=url,
            auth=self.auth,
            headers=self.headers,
            json=update_data
        )
        
        if response.status_code != 204:  # Updates typically return 204 No Content
            logger.error(f"Update failed with status {response.status_code}: {response.text}")
        
        response.raise_for_status()
        return {"status": "updated"}