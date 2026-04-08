# Requirements Document: SSO Role-Based Access Control System

## Introduction

This document specifies the requirements for implementing a three-tier role-based access control system integrated with Casdoor SSO for the CheersAI platform. The system extracts user roles from SSO authentication and enforces permissions across both backend APIs and frontend interfaces.

The system supports three roles:
- **Admin (admin/owner)**: Full access to all 8 menu items including audit logs
- **Technician (technician/editor)**: Access to 7 menu items, excluding audit logs
- **User (user/normal)**: Access to 5 menu items with read-only permissions for knowledge base and app center

## Glossary

- **SSO**: Single Sign-On authentication service (Casdoor)
- **System_Role**: Internal role representation ('admin', 'editor', 'normal')
- **Workspace_Role**: Role within a specific workspace ('owner', 'admin', 'editor', 'normal', 'dataset_operator')
- **Account**: User account entity in the database
- **Workspace**: Tenant workspace that contains resources
- **Permission_Decorator**: Backend function decorator that enforces role-based access control
- **AppContext**: Frontend React context that stores user and workspace information
- **SSO_Token_Exchange**: Process of exchanging OAuth authorization code for access token
- **Role_Sync**: Process of updating user roles from SSO to database
- **Audit_Log**: Record of security-relevant events and permission checks

## Requirements

### Requirement 1: SSO Role Extraction and Mapping

**User Story:** As a system, I want to extract role information from SSO userinfo, so that I can assign appropriate permissions to users.

#### Acceptance Criteria

1. WHEN the system receives SSO userinfo, THE System SHALL extract the role from either the 'type' or 'role' field
2. WHEN the extracted role is 'admin' or 'owner', THE System SHALL map it to system role 'admin'
3. WHEN the extracted role is 'technician' or 'editor', THE System SHALL map it to system role 'editor'
4. WHEN the extracted role is 'user', 'normal', or NULL, THE System SHALL map it to system role 'normal'
5. WHEN processing role values, THE System SHALL normalize them by converting to lowercase and trimming whitespace
6. THE System SHALL ensure that the mapped role is always one of 'admin', 'editor', or 'normal'

### Requirement 2: SSO Token Exchange and User Information Retrieval

**User Story:** As a user, I want to authenticate via SSO, so that I can access the platform with my organizational credentials.

#### Acceptance Criteria

1. WHEN a user provides an OAuth authorization code, THE System SHALL exchange it for an access token
2. WHEN the access token is obtained, THE System SHALL call the SSO userinfo endpoint to retrieve user information
3. THE System SHALL extract email, name, and role fields from the userinfo response
4. WHEN the SSO userinfo is retrieved, THE System SHALL invoke the role mapping function to determine the system role
5. IF the authorization code is invalid, THEN THE System SHALL return an error message and reject the login
6. IF the SSO service is unavailable, THEN THE System SHALL return a service unavailable error

### Requirement 3: User Account Synchronization

**User Story:** As a system, I want to create or update user accounts based on SSO information, so that user data remains synchronized with the SSO provider.

#### Acceptance Criteria

1. WHEN a user logs in via SSO, THE System SHALL query for an existing account by email address
2. WHEN no existing account is found, THE System SHALL create a new account with the SSO role, set is_sso_user to TRUE, and set status to 'active'
3. WHEN an existing account is found, THE System SHALL update the sso_role field with the current role from SSO
4. IF an existing account has status 'banned', THEN THE System SHALL reject the login and return a 403 error
5. WHEN an existing account has status 'pending', THE System SHALL activate the account and set status to 'active'
6. WHEN creating a new SSO user, THE System SHALL create a default workspace for the user
7. THE System SHALL use database transactions to ensure account synchronization is atomic

### Requirement 4: Workspace Role Synchronization

**User Story:** As a system, I want to synchronize SSO roles to workspace member roles, so that permissions are consistent across the platform.

#### Acceptance Criteria

1. WHEN a user's SSO role is synchronized, THE System SHALL update the user's role in all associated workspaces
2. WHEN mapping system roles to workspace roles, THE System SHALL map 'admin' to 'owner', 'editor' to 'editor', and 'normal' to 'normal'
3. WHEN updating workspace roles, THE System SHALL query all workspace memberships for the user
4. WHEN updating a workspace membership, THE System SHALL set the role field to the mapped workspace role
5. THE System SHALL update the updated_at timestamp for each modified membership
6. IF a user is the only owner of a workspace, THEN THE System SHALL preserve the 'owner' role and not downgrade it
7. THE System SHALL use database transactions to ensure workspace role synchronization is atomic

### Requirement 5: Backend API Permission Verification

**User Story:** As a system, I want to verify user permissions before allowing API access, so that unauthorized operations are prevented.

#### Acceptance Criteria

1. WHEN an API endpoint requires specific roles, THE System SHALL verify the current user's role before processing the request
2. WHEN verifying permissions, THE System SHALL check if the user's workspace role is in the list of allowed roles
3. WHEN a user has role 'owner' or 'admin', THE System SHALL grant access to admin-only endpoints
4. WHEN a user has role 'owner', 'admin', or 'editor', THE System SHALL grant access to editor-level endpoints
5. IF a user's role is not in the allowed roles list, THEN THE System SHALL return a 403 error with message "Insufficient permissions"
6. WHEN an admin-only endpoint is accessed, THE System SHALL require role 'owner' or 'admin'
7. WHEN an editor-level endpoint is accessed, THE System SHALL require role 'owner', 'admin', or 'editor'

### Requirement 6: Frontend SSO Service Integration

**User Story:** As a frontend application, I want to handle SSO authentication flow, so that users can log in and receive role information.

#### Acceptance Criteria

1. WHEN the frontend receives an OAuth authorization code, THE Frontend SHALL call the token exchange API
2. WHEN the token exchange is successful, THE Frontend SHALL receive an access token from the backend
3. THE Frontend SHALL store the authentication token in HttpOnly cookies
4. THE Frontend SHALL retrieve the current workspace information including the user's role
5. THE Frontend SHALL provide methods to check if the user is an admin, editor, or normal user
6. IF the role information is missing from the workspace data, THEN THE Frontend SHALL default to 'normal' role
7. THE Frontend SHALL refresh workspace information when the user switches workspaces

### Requirement 7: Frontend Navigation Menu Control

**User Story:** As a user, I want to see only the menu items I have permission to access, so that the interface is clear and relevant to my role.

#### Acceptance Criteria

1. WHEN a user has role 'owner' or 'admin', THE Frontend SHALL display 8 menu items
2. WHEN a user has role 'editor', THE Frontend SHALL display 7 menu items excluding audit logs
3. WHEN a user has role 'normal', THE Frontend SHALL display 5 menu items (My Agent, Chat, Knowledge Base, App Center, Explore)
4. THE Frontend SHALL hide menu items that the user does not have permission to access
5. THE Frontend SHALL use React useMemo to cache the filtered menu list for performance
6. WHEN the user's role changes, THE Frontend SHALL re-render the navigation menu with the updated permissions
7. THE Frontend SHALL maintain the order of menu items regardless of role

### Requirement 8: Frontend Page-Level Permission Protection

**User Story:** As a system, I want to protect pages that require specific roles, so that unauthorized users cannot access restricted content.

#### Acceptance Criteria

1. WHEN a user accesses the audit logs page, THE Frontend SHALL require role 'owner' or 'admin'
2. WHEN a user accesses the agent management page, THE Frontend SHALL require role 'owner', 'admin', or 'editor'
3. WHEN a user accesses the workflow page, THE Frontend SHALL require role 'owner', 'admin', or 'editor'
4. IF a user does not have the required role for a page, THEN THE Frontend SHALL redirect to a 403 error page
5. THE Frontend SHALL check permissions on page mount using the useRequireRole hook
6. THE Frontend SHALL not render protected page content before permission verification completes
7. THE Frontend SHALL display a user-friendly error message on the 403 page with a link to return home

### Requirement 9: Frontend Feature-Level Permission Control

**User Story:** As a user, I want to see only the action buttons I have permission to use, so that I don't attempt unauthorized operations.

#### Acceptance Criteria

1. WHEN a user views the My Agent page, THE Frontend SHALL show create, edit, and delete buttons only if the user has role 'owner', 'admin', or 'editor'
2. WHEN a user views any page with restricted actions, THE Frontend SHALL hide action buttons that require higher permissions than the user possesses
3. WHEN a user views the App Center page, THE Frontend SHALL show install, configure, and uninstall buttons only if the user has role 'owner', 'admin', or 'editor'
4. THE Frontend SHALL provide a usePermission hook that returns permission flags for common operations
5. THE Frontend SHALL ensure that permission checks for higher roles include all permissions of lower roles (monotonicity)
6. WHEN a user views the Knowledge Base page, THE Frontend SHALL show create, edit, and delete buttons only if the user has role 'owner', 'admin', or 'editor'
7. WHEN a user has role 'normal', THE Frontend SHALL display only view and search functionality for knowledge bases

### Requirement 10: Data Filtering Based on Role

**User Story:** As a system, I want to filter data based on user roles, so that users only see content appropriate to their permission level.

#### Acceptance Criteria

1. WHEN a user with role 'normal' queries knowledge bases, THE System SHALL return all knowledge bases with read-only access
2. WHEN a user with role 'normal' searches knowledge base content, THE System SHALL allow the search operation
3. WHEN a user with role 'owner', 'admin', or 'editor' queries knowledge bases, THE System SHALL return all knowledge bases with full access
4. WHEN a user with role 'owner', 'admin', or 'editor' queries agents, THE System SHALL return all agents including unpublished ones
5. WHEN a user with role 'normal' queries agents, THE System SHALL return only published agents
6. THE System SHALL apply role-based filtering at the query level to prevent unauthorized data access
7. THE System SHALL ensure that filtered data cannot be accessed through alternative API endpoints

### Requirement 11: Database Schema for Role Storage

**User Story:** As a system, I want to store role information in the database, so that permissions persist across sessions.

#### Acceptance Criteria

1. THE System SHALL add an sso_role field to the accounts table with type VARCHAR(16) and allowed values 'admin', 'editor', 'normal', or NULL
2. THE System SHALL add an is_sso_user field to the accounts table with type BOOLEAN and default value FALSE
3. THE System SHALL create an index on the sso_role field for query performance
4. THE System SHALL create an index on the is_sso_user field for query performance
5. WHEN migrating existing data, THE System SHALL set sso_role to 'normal' and is_sso_user to FALSE for all existing users
6. THE System SHALL allow SSO users to have NULL password_hash values
7. THE System SHALL ensure that the role field in tenant_account_joins supports values 'owner', 'admin', 'editor', 'normal', and 'dataset_operator'

### Requirement 12: Audit Logging for Permission Events

**User Story:** As a security administrator, I want to track permission-related events, so that I can audit access attempts and detect potential security issues.

#### Acceptance Criteria

1. WHEN a permission check fails, THE System SHALL log the event with user ID, workspace ID, requested endpoint, timestamp, and IP address
2. WHEN a user's role is changed, THE System SHALL log the event with user ID, old role, new role, and timestamp
3. WHEN a user attempts to access an admin-only feature, THE System SHALL log the attempt regardless of success or failure
4. THE System SHALL store audit logs in a dedicated table or logging system
5. WHEN querying audit logs, THE System SHALL require role 'owner' or 'admin'
6. THE System SHALL retain audit logs for a configurable retention period
7. THE System SHALL ensure audit logs cannot be modified or deleted by non-admin users

### Requirement 13: Error Handling for SSO Integration

**User Story:** As a system, I want to handle SSO integration errors gracefully, so that users receive clear feedback when authentication fails.

#### Acceptance Criteria

1. IF the SSO service returns an error during token exchange, THEN THE System SHALL return a descriptive error message to the user
2. IF the SSO userinfo endpoint is unavailable, THEN THE System SHALL return a service unavailable error
3. IF the SSO userinfo does not contain a role field, THEN THE System SHALL default to 'normal' role and log a warning
4. IF a database transaction fails during account synchronization, THEN THE System SHALL rollback the transaction and return an error
5. IF a user's account is banned, THEN THE System SHALL return a 403 error with message "Account is banned"
6. THE System SHALL log all SSO integration errors with sufficient detail for debugging
7. THE System SHALL provide retry mechanisms for transient SSO service failures

### Requirement 14: Security Measures for Role-Based Access Control

**User Story:** As a security administrator, I want the system to implement security best practices, so that role-based access control cannot be bypassed.

#### Acceptance Criteria

1. THE System SHALL store role information in HttpOnly cookies or encrypted JWT tokens to prevent client-side tampering
2. THE System SHALL verify all permissions on the backend and not trust role information sent from the frontend
3. THE System SHALL use a whitelist approach where only explicitly allowed roles can access protected resources
4. THE System SHALL implement CSRF protection for all state-changing operations
5. THE System SHALL use HTTPS for all SSO token exchanges and API communications
6. THE System SHALL set appropriate token expiration times and implement token refresh mechanisms
7. THE System SHALL apply the principle of least privilege by defaulting to 'normal' role when role information is missing or invalid

### Requirement 15: Performance Optimization for Role Checks

**User Story:** As a system, I want to optimize role verification performance, so that permission checks do not significantly impact response times.

#### Acceptance Criteria

1. THE System SHALL encode role information in JWT tokens to avoid database queries on every request
2. THE Frontend SHALL cache the filtered navigation menu using React useMemo
3. THE Frontend SHALL only recompute menu items when the user's role changes
4. THE System SHALL use database indexes on role-related fields to optimize query performance
5. THE System SHALL implement connection pooling for database access
6. THE Frontend SHALL batch permission checks when rendering multiple components
7. THE System SHALL provide a mechanism to force token refresh when roles are updated

