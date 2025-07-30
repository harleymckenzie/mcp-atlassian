"""Service Desk FastMCP server for Atlassian integration."""

import json
import logging
from typing import Annotated, Optional

import requests
from fastmcp import Context, FastMCP
from pydantic import Field

from ..servicedesk import ServiceDeskFetcher
from .dependencies import get_jira_fetcher
from .context import MainAppContext
from ..utils.decorators import check_write_access

logger = logging.getLogger("mcp-atlassian.server.servicedesk")

servicedesk_mcp = FastMCP(
    name="Service Desk MCP Service",
    description="Provides tools for interacting with Atlassian Service Desk.",
)


@servicedesk_mcp.tool(tags={"servicedesk", "read"})
async def servicedesk_get_service_desks(ctx: Context) -> str:
    """Get all available Service Desks."""
    jira = await get_jira_fetcher(ctx)
    
    try:
        servicedesk = ServiceDeskFetcher(jira.config)
        service_desks = servicedesk.get_service_desks()
        return json.dumps(service_desks, indent=2)
    except Exception as e:
        logger.error(f"Error getting service desks: {e}")
        return f"Error: {e}"


@servicedesk_mcp.tool(tags={"servicedesk", "read"})
async def servicedesk_get_request_types(
    ctx: Context,
    service_desk_id: Annotated[Optional[str], Field(description="Service Desk ID (optional if JIRA_DEFAULT_SERVICE_DESK_ID is set)")] = None
) -> str:
    """Get available request types for a Service Desk."""
    jira = await get_jira_fetcher(ctx)
    
    # Use default service desk ID if none provided
    if not service_desk_id:
        service_desk_id = jira.config.default_service_desk_id
        if not service_desk_id:
            return "Error: No service_desk_id provided and JIRA_DEFAULT_SERVICE_DESK_ID not set"
    
    try:
        servicedesk = ServiceDeskFetcher(jira.config)
        request_types = servicedesk.get_request_types(service_desk_id)
        return json.dumps(request_types, indent=2)
    except Exception as e:
        logger.error(f"Error getting request types: {e}")
        return f"Error: {e}"


@servicedesk_mcp.tool(tags={"servicedesk", "read"})
async def servicedesk_get_organizations(
    ctx: Context,
    service_desk_id: Annotated[Optional[str], Field(description="Service Desk ID (optional if JIRA_DEFAULT_SERVICE_DESK_ID is set)")] = None
) -> str:
    """Get available organizations for a Service Desk."""
    jira = await get_jira_fetcher(ctx)
    
    # Use default service desk ID if none provided
    if not service_desk_id:
        service_desk_id = jira.config.default_service_desk_id
        if not service_desk_id:
            return "Error: No service_desk_id provided and JIRA_DEFAULT_SERVICE_DESK_ID not set"
    
    try:
        servicedesk = ServiceDeskFetcher(jira.config)
        orgs = servicedesk.get_organizations(service_desk_id)
        return json.dumps(orgs, indent=2)
    except Exception as e:
        logger.error(f"Error getting organizations: {e}")
        return f"Error: {e}"


@servicedesk_mcp.tool(tags={"servicedesk", "read"})
async def servicedesk_get_organization_users(
    ctx: Context,
    organization_id: Annotated[str, Field(description="Organization ID")],
    start: Annotated[int, Field(description="Starting index for pagination")] = 0,
    limit: Annotated[int, Field(description="Maximum number of users to return")] = 50
) -> str:
    """Get users in a Service Desk organization."""
    jira = await get_jira_fetcher(ctx)
    
    try:
        servicedesk = ServiceDeskFetcher(jira.config)
        users = servicedesk.get_organization_users(organization_id, start, limit)
        return json.dumps(users, indent=2)
    except Exception as e:
        logger.error(f"Error getting organization users: {e}")
        return f"Error: {e}"


@servicedesk_mcp.tool(tags={"servicedesk", "write"})
@check_write_access
async def servicedesk_add_users_to_organization(
    ctx: Context,
    organization_id: Annotated[str, Field(description="Organization ID")],
    usernames: Annotated[str, Field(description="Comma-separated list of usernames or account IDs to add")]
) -> str:
    """Add users to a Service Desk organization.
    
    Args:
        organization_id: The organization ID to add users to
        usernames: Comma-separated list of usernames/account IDs to add
    
    Returns:
        JSON response with operation result
    """
    jira = await get_jira_fetcher(ctx)
    
    try:
        servicedesk = ServiceDeskFetcher(jira.config)
        
        # Parse usernames from comma-separated string
        username_list = [username.strip() for username in usernames.split(',') if username.strip()]
        
        if not username_list:
            return "Error: No valid usernames provided"
        
        result = servicedesk.add_users_to_organization(organization_id, username_list)
        return json.dumps(result, indent=2)
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error adding users to organization: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                return f"HTTP Error {e.response.status_code}: {json.dumps(error_details, indent=2)}"
            except:
                return f"HTTP Error {e.response.status_code}: {e.response.text}"
        return f"HTTP Error: {e}"
    except Exception as e:
        logger.error(f"Error adding users to organization: {e}")
        return f"Error: {e}"


@servicedesk_mcp.tool(tags={"servicedesk", "read"})
async def servicedesk_get_request_type_fields(
    ctx: Context,
    request_type_id: Annotated[str, Field(description="Request Type ID")],
    service_desk_id: Annotated[Optional[str], Field(description="Service Desk ID (optional if JIRA_DEFAULT_SERVICE_DESK_ID is set)")] = None
) -> str:
    """Get available fields for a specific Service Desk request type."""
    jira = await get_jira_fetcher(ctx)
    
    # Use default service desk ID if none provided
    if not service_desk_id:
        service_desk_id = jira.config.default_service_desk_id
        if not service_desk_id:
            return "Error: No service_desk_id provided and JIRA_DEFAULT_SERVICE_DESK_ID not set"
    
    try:
        servicedesk = ServiceDeskFetcher(jira.config)
        fields = servicedesk.get_request_type_fields(service_desk_id, request_type_id)
        return json.dumps(fields, indent=2)
    except Exception as e:
        logger.error(f"Error getting request type fields: {e}")
        return f"Error: {e}"


@servicedesk_mcp.tool(tags={"servicedesk", "write"})
@check_write_access
async def servicedesk_create_customer_request(
    ctx: Context,
    request_type_id: Annotated[str, Field(description="Request Type ID (e.g., '144' for Access)")],
    summary: Annotated[str, Field(description="Request summary")],
    description: Annotated[str, Field(description="Request description")],
    service_desk_id: Annotated[Optional[str], Field(description="Service Desk ID (optional if JIRA_DEFAULT_SERVICE_DESK_ID is set)")] = None,
    request_field_values: Annotated[Optional[str], Field(description="JSON string of request field values")] = None
) -> str:
    """Create a Service Desk customer request using the proper Service Desk API.
    
    Args:
        request_type_id: The Request Type ID (get from servicedesk_get_request_types)
        summary: The request summary/title
        description: The request description/body
        service_desk_id: The Service Desk ID where the request will be created (optional if JIRA_DEFAULT_SERVICE_DESK_ID is set)
        request_field_values: JSON string of request field values (Service Desk specific fields)
    
    Returns:
        JSON response with created request details
    """
    jira = await get_jira_fetcher(ctx)
    
    # Use default service desk ID if none provided
    if not service_desk_id:
        service_desk_id = jira.config.default_service_desk_id
        if not service_desk_id:
            return "Error: No service_desk_id provided and JIRA_DEFAULT_SERVICE_DESK_ID not set"
    
    try:
        servicedesk = ServiceDeskFetcher(jira.config)
        
        # Parse request field values if provided
        parsed_field_values = {}
        if request_field_values:
            try:
                parsed_field_values = json.loads(request_field_values)
            except json.JSONDecodeError as e:
                return f"Error parsing request_field_values JSON: {e}"
        
        # Create the customer request
        result = servicedesk.create_customer_request(
            service_desk_id=service_desk_id,
            request_type_id=request_type_id,
            summary=summary,
            description=description,
            request_field_values=parsed_field_values
        )
        
        return json.dumps(result, indent=2)
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error creating Service Desk customer request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                return f"HTTP Error {e.response.status_code}: {json.dumps(error_details, indent=2)}"
            except:
                return f"HTTP Error {e.response.status_code}: {e.response.text}"
        return f"HTTP Error: {e}"
    except Exception as e:
        logger.error(f"Error creating Service Desk customer request: {e}")
        return f"Error: {e}"


@servicedesk_mcp.tool(tags={"servicedesk", "write"})
@check_write_access
async def servicedesk_update_issue(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Issue key (e.g., 'CS-12345')")],
    custom_fields: Annotated[str, Field(description="JSON string of custom fields to update")]
) -> str:
    """Update custom fields on an existing Service Desk issue.
    
    Args:
        issue_key: The issue key to update
        custom_fields: JSON string of custom fields to update (e.g., '{"customfield_10500": ["53"]}')
    
    Returns:
        Success/error message
    """
    jira = await get_jira_fetcher(ctx)
    
    try:
        servicedesk = ServiceDeskFetcher(jira.config)
        
        # Parse custom fields
        try:
            parsed_custom_fields = json.loads(custom_fields)
        except json.JSONDecodeError as e:
            return f"Error parsing custom_fields JSON: {e}"
        
        # Update the issue
        result = servicedesk.update_request(issue_key, **parsed_custom_fields)
        
        return f"Issue {issue_key} updated successfully"
        
    except Exception as e:
        logger.error(f"Error updating Service Desk issue: {e}")
        return f"Error: {e}"