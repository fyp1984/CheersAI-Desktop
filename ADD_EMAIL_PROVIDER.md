# Adding Email Provider to SSO Application

## Current Situation

The `init_data.json` configuration changes do not apply to an existing SSO database. The Email provider must be added manually through the SSO web interface.

## Steps to Add Email Provider

### 1. Access SSO Admin Interface

Open browser and navigate to:
```
http://localhost:18000
```

### 2. Login to SSO

Login with your SSO admin account (or create one if needed).

### 3. Create Email Provider

1. Click **Providers** in the left sidebar
2. Click **Add** button
3. Fill in the form:
   - **Owner**: admin
   - **Name**: provider_email_default
   - **Display name**: Email Default
   - **Category**: Email
   - **Type**: Default (or SMTP)
   - **Host**: smtp.example.com (or your SMTP server)
   - **Port**: 587 (or 465 for SSL)
   - **Username**: (your SMTP username if required)
   - **Password**: (your SMTP password if required)
   - **Title**: CheersAI SSO
   - **Content**: Verification code email template
4. Click **Save**

### 4. Add Provider to Application

1. Click **Applications** in the left sidebar
2. Find and click **app-built-in**
3. Scroll to **Providers** section
4. Click **Add item**
5. Select **provider_email_default** from dropdown
6. Configure:
   - **Can sign up**: ✓
   - **Can sign in**: ✓
   - **Can unlink**: (optional)
   - **Prompted**: (optional)
7. Click **Save**

### 5. Also Add Redirect URIs

While editing the application, scroll to **Redirect URIs** and add:
```
http://localhost:3000/signin?sso=desktop
http://localhost:3000/oauth-callback
http://localhost:9000/callback
```

Click **Save** to apply all changes.

## Verification

After configuration, verify the Email provider is added:

```bash
curl "http://localhost:18000/api/get-application?id=admin/app-built-in"
```

Check that the response includes `provider_email_default` in the providers list.

## Alternative: Use Existing Captcha Provider

The application currently has `provider_captcha_default` configured. If you don't need Email verification, you can use the existing Captcha provider for now.

## Email Provider Configuration Options

### SMTP Settings (for real email)
- **Host**: Your SMTP server (e.g., smtp.gmail.com, smtp.office365.com)
- **Port**: 587 (TLS) or 465 (SSL)
- **Username**: Your email address
- **Password**: Your email password or app-specific password

### Mock Email (for testing)
- **Type**: Mock
- No real SMTP configuration needed
- Emails will be logged but not sent

## Current Application Configuration

- **Application**: app-built-in
- **Client ID**: c98f7150fe9c044bf217
- **Current Providers**: provider_captcha_default
- **Redirect URIs**: (needs to be configured)

## Next Steps

1. Configure Email provider via SSO web interface
2. Add Email provider to app-built-in application
3. Add redirect URIs to app-built-in application
4. Test SSO login flow

---

**Note**: The `init_data.json` changes have been made but won't take effect on an existing database. Manual configuration through the web interface is required.
