# Google OAuth Setup Guide

## Overview

VeinLine uses **django-allauth** with Google OAuth 2.0 for secure social authentication. This guide walks you through setting up Google authentication for your VeinLine instance.

## Prerequisites

- VeinLine is already installed and running
- You have a Google account
- Access to [Google Cloud Console](https://console.cloud.google.com/)

## Step 1: Create Google OAuth Credentials

### 1.1 Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top
3. Click **NEW PROJECT**
4. Enter "VeinLine" as the project name
5. Click **CREATE**
6. Wait for the project to be created (may take a minute)

### 1.2 Enable Google+ API

1. In the Google Cloud Console, go to **APIs & Services** > **Library**
2. Search for "Google+ API"
3. Click on it and click **ENABLE**

### 1.3 Create OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** (for development/testing)
3. Click **CREATE**
4. Fill in the form:
   - **App name**: VeinLine
   - **User support email**: Your email
   - **Developer contact**: Your email
5. Click **SAVE AND CONTINUE**
6. Click **SAVE AND CONTINUE** on the scopes page (defaults are fine)
7. Click **SAVE AND CONTINUE** on the test users page
8. Review and click **BACK TO DASHBOARD**

### 1.4 Create OAuth Client ID

1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
3. Select **Web application** as the application type
4. Enter "VeinLine" as the name
5. Under **Authorized JavaScript origins**, add:
   - `http://127.0.0.1:8000` (for local development)
   - `http://localhost:8000` (if you use localhost)
   
6. Under **Authorized redirect URIs**, add:
   - `http://127.0.0.1:8000/accounts/google/login/callback/`
   - `http://localhost:8000/accounts/google/login/callback/`

7. Click **CREATE**
8. A popup will show your credentials. Copy:
   - **Client ID**
   - **Client Secret**

⚠️ **Important**: Keep these credentials private! Never commit them to version control.

## Step 2: Configure VeinLine

### 2.1 Update .env File

1. Open the `.env` file in your VeinLine project root
2. Find the Google OAuth section (around line 42):
   ```dotenv
   # Google OAuth (for social login)
   GOOGLE_OAUTH_CLIENT_ID=
   GOOGLE_OAUTH_CLIENT_SECRET=
   ```

3. Add your credentials:
   ```dotenv
   # Google OAuth (for social login)
   GOOGLE_OAUTH_CLIENT_ID=your_client_id_from_google_console
   GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret_from_google_console
   ```

4. Save the file

### 2.2 Restart the Server

**Windows:**
```cmd
start_server.bat
```

**Linux/Mac:**
```bash
./start_server.sh
```

## Step 3: Configure in Django Admin

### 3.1 Access Django Admin

1. Go to `http://127.0.0.1:8000/admin/` in your browser
2. Log in with your admin account (if not logged in)

### 3.2 Add Social Application

1. In the Django admin, find **SOCIAL APPLICATIONS** under the **Social Accounts** section
2. Click **+ Add Social Application**
3. Fill in the form:
   - **Provider**: Select **Google**
   - **Name**: Google OAuth
   - **Client id**: Paste your Client ID from Google Console
   - **Secret key**: Paste your Client Secret from Google Console
   - **Sites**: Select your site (should be `127.0.0.1:8000` or `localhost:8000`)

4. Click **SAVE**

## Step 4: Test Google Login

1. Go to `http://127.0.0.1:8000/login/`
2. You should see a "Continue with Google" button
3. Click the button
4. You'll be redirected to Google's login page
5. Sign in with your Google account
6. Accept the permissions request
7. You should be redirected back to VeinLine and logged in

## Troubleshooting

### "The redirect URI does not match"

**Solution**: Make sure the redirect URI in Google Console matches exactly:
- Check the URL in your browser address bar
- Common issues:
  - Using `localhost` instead of `127.0.0.1` (or vice versa)
  - Port number mismatch
  - Missing trailing slash

Update your Google Console credentials to include both variations:
- `http://127.0.0.1:8000/accounts/google/login/callback/`
- `http://localhost:8000/accounts/google/login/callback/`

### "Client ID not set" or "No credentials found"

**Solution**: 
1. Make sure you've set the `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` in your `.env` file
2. Restart the Django server after updating `.env`
3. Check the [verification script output](#verification)

### "Social application matching query does not exist"

**Solution**: You need to add the Social Application in Django admin (Step 3).

### "Invalid scope" error

**Solution**: The default scopes are already configured correctly in `settings.py`. If you see this error, verify your credentials are correct in the Django admin.

## Verification

Run the verification script to check your setup:

```bash
python verify_google_oauth.py
```

This will check:
- ✓ Django settings are configured
- ✓ Required packages are installed
- ✓ Environment variables are set
- ✓ Templates have the Google login button
- ✓ Database is configured

## Production Deployment

For production deployment, update the following:

### 1. OAuth Redirect URIs

Add your production domain to Google Console:
- In **APIs & Services** > **Credentials**, edit your OAuth client
- Add `https://yourdomain.com/accounts/google/login/callback/`

### 2. Django Settings

Update your `.env` file:
```dotenv
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=your-production-secret-key
```

### 3. OAuth Consent Screen

In Google Console, publish your OAuth consent screen for public use:
1. Go to **OAuth consent screen**
2. Click **PUBLISH APP**
3. Confirm

### 4. Update Site Domain

In Django admin:
1. Go to **Sites** under **Django**
2. Edit the site with ID 1
3. Update the domain to your production domain

## User Roles

When users sign in with Google:
- They are automatically assigned the **Donor** role by default
- Admins can change roles in Django admin under **Users** > **Profile**

## Security Notes

- Never share your Client Secret
- Keep `.env` file out of version control (it's in `.gitignore`)
- Use HTTPS in production
- Regularly review connected applications in your Google account settings

## Additional Resources

- [django-allauth Documentation](https://django-allauth.readthedocs.io/)
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Django Social Authentication](https://django-allauth.readthedocs.io/en/latest/socialaccount/providers/google.html)
