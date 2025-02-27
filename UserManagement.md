# User Management in Chilliwack

## Overview
The Chilliwack application integrates Microsoft authentication and role-based user management using Flask, SQLAlchemy, and Microsoft Authentication Library (MSAL). This document outlines the key components of user management, including authentication, authorization, and session handling.

## Features

### Microsoft Authentication
- Users log in via Microsoft using Office 365 authentication.
- User information is retrieved from Microsoft Graph API.
- Profile details (name, email, role) are stored in the database.

### Role-Based Access Control (RBAC)
- Users are assigned roles (`administrator`, `basicuser`, `privilegeduser`).
- Admin users access the `/admin` dashboard.
- Basic users access the `/dashboard`.

### Session Handling
- After authentication, user details are stored in a session.
- Flask sessions manage user access across pages.

### Database Structure
- **User Table:** Stores user data (ID, name, email, role).
- **Role Table:** Defines roles and permissions.

### Routes
- `/login` → Redirects to Microsoft login.
- `/callback` → Handles authentication response and user database entry.
- `/dashboard` → Displays user profile.
- `/admin` → Restricted to administrators, allowing them to update, remove, and deactivate user.
- `/logout` → Clears session and logs out the user.
  ![image](https://github.com/user-attachments/assets/b47a5f9e-a49d-498f-ae76-f1e8c874b776)

