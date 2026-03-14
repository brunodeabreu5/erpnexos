# ERP Paraguay V6 - Authentication Workflow

This document provides detailed flowcharts and documentation for the authentication and authorization system in ERP Paraguay V6.

## Login Process Flow

```mermaid
flowchart TD
    Start([Application Starts]) --> CheckEnv{Admin Password<br/>Configured?}
    CheckEnv --> |No| ErrorEnv[Error: ADMIN_PASSWORD<br/>not set in .env]
    CheckEnv --> |Yes| ValidateConfig[Validate Configuration]

    ErrorEnv --> ExitEnv([Exit Application])

    ValidateConfig --> ConfigValid{Configuration<br/>Valid?}
    ConfigValid --> |No| ErrorConfig[Display Configuration<br/>Validation Errors]
    ConfigValid --> |Yes| InitDatabase[Initialize Database]

    ErrorConfig --> ExitConfig([Exit Application])

    InitDatabase --> CheckTables{Tables<br/>Exist?}
    CheckTables --> |No| CreateTables[Create All Tables]
    CheckTables --> |Yes| CheckAdmin
    CreateTables --> CheckAdmin{Admin User<br/>Exists?}

    CheckAdmin --> |No| CreateAdmin[Create Admin User<br/>from .env]
    CheckAdmin --> |Yes| ShowLogin

    CreateAdmin --> AdminSuccess{Admin Created?}
    AdminSuccess --> |No| ErrorAdmin[Error: Failed to<br/>Create Admin]
    AdminSuccess --> |Yes| ShowLogin[Display Login Window]

    ErrorAdmin --> ExitAdmin([Exit Application])

    ShowLogin --> EnterCredentials[User Enters<br/>Username & Password]
    EnterCredentials --> ValidateInput{Input Valid?}

    ValidateInput --> |Empty Fields| ErrorInput[Error: Username and<br/>Password Required]
    ValidateInput --> |Valid| CheckRateLimit

    ErrorInput --> ShowLogin

    CheckRateLimit{Rate Limit Check} --> Blocked{Account<br/>Locked?}
    Blocked --> |Yes| ShowLocked[Display Account<br/>Locked Message]
    Blocked --> |No| QueryUser

    ShowLocked --> WaitOption{User Action}
    WaitOption --> |Wait| WaitTime[Wait 15 Minutes]
    WaitOption --> |Restart| RestartApp[Restart Application]
    WaitTime --> ShowLogin
    RestartApp --> Start

    QueryUser[Query User from<br/>Database] --> UserExists{User<br/>Exists?}
    UserExists --> |No| LogFailed1[Log Failed Attempt:<br/>User Not Found]
    UserExists --> |Yes| CheckActive

    LogFailed1 --> IncrementFailed1[Increment Failed Counter]
    IncrementFailed1 --> CheckBlockThreshold1{Attempts >= 5?}
    CheckBlockThreshold1 --> |Yes| BlockAccount1[Lock Account for<br/>15 Minutes]
    CheckBlockThreshold1 --> |No| ShowError1
    BlockAccount1 --> ShowLocked
    ShowError1[Show Invalid Credentials] --> ShowLogin

    CheckActive{User<br/>Active?} --> |No| LogFailed2[Log Failed Attempt:<br/>User Inactive]
    CheckActive --> |Yes| VerifyPassword

    LogFailed2 --> IncrementFailed2[Increment Failed Counter]
    IncrementFailed2 --> CheckBlockThreshold2{Attempts >= 5?}
    CheckBlockThreshold2 --> |Yes| BlockAccount2
    CheckBlockThreshold2 --> |No| ShowError2
    BlockAccount2 --> ShowLocked
    ShowError2 --> ShowLogin

    VerifyPassword[Verify Password<br/>Hash Comparison] --> PasswordCorrect{Password<br/>Match?}
    PasswordCorrect --> |No| LogFailed3[Log Failed Attempt:<br/>Invalid Password]
    PasswordCorrect --> |Yes| LogSuccess[Log Successful Login]

    LogFailed3 --> IncrementFailed3[Increment Failed Counter]
    IncrementFailed3 --> CheckBlockThreshold3{Attempts >= 5?}
    CheckBlockThreshold3 --> |Yes| BlockAccount3
    CheckBlockThreshold3 --> |No| ShowError3
    BlockAccount3 --> ShowLocked
    ShowError3 --> ShowLogin

    LogSuccess --> ResetFailed[Reset Failed Counter]
    ResetFailed --> RecordLogin[Record Login in Audit Log]
    RecordLogin --> CreateSession[Create User Session]
    CreateSession --> StartSessionTimer[Start Session Timeout Timer]
    StartSessionTimer --> LoadDashboard[Load Main Dashboard]
    LoadDashboard --> Success([Login Successful])
```

## Rate Limiting Mechanism

```mermaid
sequenceDiagram
    actor User
    participant UI as Login Window
    participant Auth as Auth Service
    participant RateLimiter as Rate Limiter
    participant DB as Database
    participant Audit as Audit Log

    Note over User,Audit: First Failed Attempt
    User->>UI: Enter invalid credentials
    UI->>Auth: authenticate_user(username, password)
    Auth->>RateLimiter: check_login_blocked(username)
    RateLimiter->>RateLimiter: Check failed attempts in last 15 min
    RateLimiter-->>Auth: Not blocked (0 attempts)
    Auth->>DB: Query user by username
    DB-->>Auth: User found
    Auth->>Auth: Verify password (fail)
    Auth->>RateLimiter: record_failed_attempt(username)
    RateLimiter->>RateLimiter: Add timestamp with success=false
    Auth->>Audit: Log failed attempt
    Auth-->>UI: Authentication failed
    UI-->>User: Show error (1/5 attempts)

    Note over User,Audit: Multiple Failed Attempts (2-4)
    loop Attempts 2-4
        User->>UI: Enter invalid credentials
        UI->>Auth: authenticate_user(username, password)
        Auth->>RateLimiter: check_login_blocked(username)
        RateLimiter->>RateLimiter: Count recent failures (2, 3, 4)
        RateLimiter-->>Auth: Not blocked yet
        Auth->>Auth: Verify password (fail)
        Auth->>RateLimiter: record_failed_attempt(username)
        Auth->>Audit: Log failed attempt
        Auth-->>UI: Authentication failed
        UI-->>User: Show error (X/5 attempts)
    end

    Note over User,Audit: Fifth Failed Attempt - Account Locked
    User->>UI: Enter invalid credentials (5th time)
    UI->>Auth: authenticate_user(username, password)
    Auth->>RateLimiter: check_login_blocked(username)
    RateLimiter->>RateLimiter: Count recent failures (5)
    RateLimiter->>RateLimiter: 5 >= 5, block account
    RateLimiter-->>Auth: BLOCKED - Account locked
    Auth->>Audit: Log account locked event
    Auth-->>UI: Authentication failed - Account locked
    UI-->>User: Show "Account locked for 15 minutes"

    Note over User,Audit: User Tries During Lock Period
    User->>UI: Try to login again
    UI->>Auth: authenticate_user(username, password)
    Auth->>RateLimiter: check_login_blocked(username)
    RateLimiter->>RateLimiter: Check time since last failure
    RateLimiter->>RateLimiter: < 15 minutes, still blocked
    RateLimiter-->>Auth: BLOCKED - Still locked
    Auth-->>UI: Account still locked
    UI-->>User: Show "X minutes remaining"

    Note over User,Audit: 15 Minutes Elapsed - Lock Expires
    User->>UI: Try to login after 15 minutes
    UI->>Auth: authenticate_user(username, password)
    Auth->>RateLimiter: check_login_blocked(username)
    RateLimiter->>RateLimiter: Check time since last failure
    RateLimiter->>RateLimiter: >= 15 minutes, clear old attempts
    RateLimiter->>RateLimiter: Reset counter to 0
    RateLimiter-->>Auth: Not blocked (lock expired)
    Auth->>Auth: Verify password (success this time)
    Auth->>RateLimiter: record_successful_attempt(username)
    RateLimiter->>RateLimiter: Clear all failed attempts
    Auth->>Audit: Log successful login
    Auth-->>UI: Authentication successful
    UI-->>User: Login successful, show dashboard
```

## Session Management Flow

```mermaid
flowchart TD
    Start([User Logs In Successfully]) --> CreateSession[Create Session Object]
    CreateSession --> SetVariables[Set Session Variables:<br/>user_id, username, role]
    SetVariables --> RecordTimestamp[Record session_start_time]
    RecordTimestamp --> RecordActivity[Record last_activity_time]
    RecordActivity --> StartTimer[Start 60-second Timer]

    StartTimer --> MonitorActivity{User Activity Detected?}
    MonitorActivity --> |Yes| UpdateActivity[Update last_activity_time]
    MonitorActivity --> |No| CheckTimeout

    UpdateActivity --> ResetTimer[Reset Timer to 60 seconds]
    ResetTimer --> MonitorActivity

    CheckTimeout[Timer Fires Every 60s] --> CalculateInactivity[Calculate:<br/>now - last_activity_time]
    CalculateInactivity --> CheckThreshold{Inactivity<br/>> 60 minutes?}

    CheckThreshold --> |No| ResetTimer
    CheckThreshold --> |Yes| InitiateLogout[Initiate Auto-Logout]

    InitiateLogout --> ShowWarning[Display Session Expired Warning]
    ShowWarning --> LogEvent[Log Session Timeout in Audit]
    LogEvent --> ClearSession[Clear Session Variables]
    ClearSession --> StopTimer[Stop Session Timer]
    StopTimer --> ShowLogin[Return to Login Screen]
    ShowLogin --> End([Session Terminated])

    %% Manual Logout Flow
    Start -.->|User Clicks Logout| ManualLogout[Manual Logout Requested]
    ManualLogout --> LogManualLogout[Log Manual Logout in Audit]
    LogManualLogout --> ClearSession
```

## Password Hashing and Verification

```mermaid
sequenceDiagram
    actor User
    participant UI as Registration/Setup
    participant Auth as Auth Service
    participant Crypto as bcrypt/Passlib
    participant DB as Database

    Note over User,DB: Password Setup (First Time)
    User->>UI: Enter ADMIN_PASSWORD in .env
    UI->>Auth: create_admin_user()
    Auth->>Auth: Validate password length >= 8
    Auth->>Auth: Read ADMIN_PASSWORD from .env
    Auth->>Crypto: Generate salt
    Crypto-->>Auth: Random salt generated
    Auth->>Crypto: Hash password with bcrypt
    Note over Auth,Crypto: bcrypt uses salt + password<br/>+ cost factor (12 rounds)<br/>+ Blowfish cipher
    Crypto-->>Auth: Password hash (60 chars)
    Auth->>DB: INSERT INTO users (username, password, ...)
    Note over Auth,DB: Stores: username + hash<br/>Never stores plaintext password
    DB-->>Auth: User created successfully
    Auth-->>UI: Admin user created

    Note over User,DB: Login Attempt
    User->>UI: Enter username and password
    UI->>Auth: authenticate_user(username, password)
    Auth->>DB: SELECT * FROM users WHERE username = ?
    DB-->>Auth: User record with password hash
    Auth->>Crypto: verify_password(plain_password, hashed_password)
    Note over Auth,Crypto: bcrypt extracts salt from hash<br/>Hashes plain_password with same salt<br/>Compares hashes in constant time
    Crypto-->>Auth: True (match) or False (no match)

    alt Password matches
        Auth->>Auth: Password correct
        Auth-->>UI: Authentication successful
    else Password doesn't match
        Auth->>Auth: Password incorrect
        Auth->>Auth: Increment failed counter
        Auth-->>UI: Authentication failed
    end
```

## Audit Logging Flow

```mermaid
flowchart TD
    Start([Authentication Event]) --> DetermineType{Event Type}

    DetermineType -->|Login Success| LogSuccess[Log LOGIN_SUCCESS]
    DetermineType -->|Login Failed| LogFailed[Log LOGIN_FAILED]
    DetermineType -->|Account Locked| LogLocked[Log ACCOUNT_LOCKED]
    DetermineType -->|Session Expired| LogExpired[Log SESSION_EXPIRED]
    DetermineType -->|Logout| LogLogout[Log LOGOUT]

    LogSuccess --> GatherData1[Collect Event Data]
    LogFailed --> GatherData2[Collect Event Data]
    LogLocked --> GatherData3[Collect Event Data]
    LogExpired --> GatherData4[Collect Event Data]
    LogLogout --> GatherData5[Collect Event Data]

    GatherData1 --> BuildLog
    GatherData2 --> BuildLog[Build Audit Log Entry]
    GatherData3 --> BuildLog
    GatherData4 --> BuildLog
    GatherData5 --> BuildLog

    BuildLog --> AddTimestamp[Add timestamp (UTC)]
    AddTimestamp --> AddUser[Add user_id and username]
    AddUser --> AddAction[Add action type]
    AddAction --> AddDetails[Add additional details]
    AddDetails --> AddContext[Add request_id and environment]

    AddContext --> FormatJSON[Format as JSON]
    FormatJSON --> WriteLog[Write to app.log]
    WriteLog --> SaveDB[Save to audit_logs table]

    SaveDB --> DBSuccess{Saved Successfully?}
    DBSuccess --> |Yes| End([Audit Log Complete])
    DBSuccess --> |No| LogError[Log Error to Console]
    LogError --> End
```

## Authorization Flow

```mermaid
flowchart TD
    Start([User Requests Action]) --> CheckSession{Valid Session?}
    CheckSession --> |No| RedirectLogin[Redirect to Login]
    CheckSession --> |Yes| GetUserRole

    RedirectLogin --> End([Access Denied])

    GetUserRole[Get User Role from Session] --> RoleType{User Role?}

    RoleType -->|admin| AdminRole[Full Access Granted]
    RoleType -->|seller| SellerRole[Sales Access Only]
    RoleType -->|viewer| ViewerRole[Read-Only Access]

    AdminRole --> CheckAction
    SellerRole --> CheckAction{Action Type?}
    ViewerRole --> CheckAction

    CheckAction -->|Create/Update/Delete| ValidatePermission
    CheckAction -->|Read Only| AllowRead[Allow Access]

    ValidatePermission[Validate Permission] --> SellerCheck{Seller Can<br/>Perform?}
    SellerCheck -->|Yes| AllowAction[Allow Action]
    SellerCheck -->|No| ViewerCheck{Viewer Can<br/>Perform?}

    ViewerCheck -->|Yes| AllowAction
    ViewerCheck -->|No| DenyAccess[Deny Access]

    AllowRead --> LogAccess[Log Access in Audit]
    AllowAction --> LogAccess
    DenyAccess --> LogDenial[Log Access Denial]

    LogAccess --> Grant([Access Granted])
    LogDenial --> End
```

## Security Configuration

```mermaid
flowchart TD
    Start([Application Startup]) --> LoadConfig[Load Configuration from .env]
    LoadConfig --> ValidateEnv{ENVIRONMENT<br/>Set?}

    ValidateEnv --> |No| Error1[Error: ENVIRONMENT<br/>not set]
    ValidateEnv --> |Yes| CheckEnvType{Environment<br/>Type?}

    Error1 --> End([Startup Failed])

    CheckEnvType -->|production| ProdRules[Apply Production Rules]
    CheckEnvType -->|development| DevRules[Apply Development Rules]
    CheckEnvType -->|staging| StagingRules[Apply Staging Rules]

    ProdRules --> CheckDebug{DEBUG = false?}
    CheckDebug --> |Yes| CheckMinPW{MIN_PASSWORD_LENGTH<br/>>= 8?}
    CheckDebug --> |No| Error2[Error: DEBUG must be<br/>false in production]

    Error2 --> End

    CheckMinPW --> |Yes| CheckCompany{COMPANY_NAME<br/>Configured?}
    CheckMinPW --> |No| Error3[Error: MIN_PASSWORD_LENGTH<br/>must be >= 8 in production]

    Error3 --> End

    CheckCompany --> |Yes| ValidateSuccess[Configuration Valid]
    CheckCompany --> |No| Warning1[Warning: Using default<br/>company name]

    Warning1 --> ValidateSuccess

    DevRules --> CheckAdminPW{ADMIN_PASSWORD<br/>Set?}
    CheckAdminPW --> |No| Error4[Error: ADMIN_PASSWORD<br/>required]
    CheckAdminPW --> |Yes| ValidateSuccess

    Error4 --> End

    StagingRules --> CheckStagingConfig{Staging<br/>Config OK?}
    CheckStagingConfig --> |Yes| ValidateSuccess
    CheckStagingConfig --> |No| Error5[Error: Invalid<br/>staging configuration]

    Error5 --> End

    ValidateSuccess --> ApplySettings[Apply Security Settings]
    ApplySettings --> SetTimeout[Set SESSION_TIMEOUT_MINUTES]
    SetTimeout --> SetRateLimit[Set MAX_LOGIN_ATTEMPTS]
    SetRateLimit --> SetBlockTime[Set LOGIN_BLOCK_MINUTES]
    SetBlockTime --> InitializeLogging[Initialize Structured Logging]
    InitializeLogging --> Complete([Startup Complete])
```

## Password Recovery Flow (Future Enhancement)

```mermaid
flowchart TD
    Start([User Clicks "Forgot Password"]) --> EnterEmail[Enter Email Address]
    EnterEmail --> ValidateEmail{Email Format<br/>Valid?}
    ValidateEmail --> |No| Error1[Error: Invalid Email Format]
    ValidateEmail --> |Yes| QueryUser

    Error1 --> EnterEmail

    QueryUser[Query User by Email] --> UserExists{User<br/>Exists?}
    UserExists --> |No| Error2[Error: No account with<br/>this email]
    UserExists --> |Yes| GenerateToken

    Error2 --> End([Process Complete])

    GenerateToken[Generate Secure Reset Token] --> SaveToken[Save Token to Database<br/>with Expiry]
    SaveToken --> SendEmail[Send Reset Email<br/>with Token Link]
    SendEmail --> DisplayMessage[Display: Check your email]

    DisplayMessage --> UserClicks[User Clicks Email Link]
    UserClicks --> ValidateToken{Token Valid?}
    ValidateToken --> |Expired| Error3[Error: Token expired]
    ValidateToken --> |Invalid| Error4[Error: Invalid token]
    ValidateToken --> |Valid| ShowPasswordForm

    Error3 --> End
    Error4 --> End

    ShowPasswordForm[Display New Password Form] --> EnterNewPassword[Enter New Password]
    EnterNewPassword --> ValidateNewPassword{Password<br/>Valid?}
    ValidateNewPassword --> |Too Short| Error5[Error: Password must be<br/>at least 8 characters]
    ValidateNewPassword --> |Weak| Warning[Warning: Consider using<br/>a stronger password]
    ValidateNewPassword --> |Valid| ConfirmPassword

    Error5 --> EnterNewPassword
    Warning --> ConfirmPassword{User Confirms?}
    ConfirmPassword --> |No| EnterNewPassword
    ConfirmPassword --> |Yes| HashPassword

    HashPassword[Hash New Password] --> UpdateDB[Update Password in Database]
    UpdateDB --> InvalidateTokens[Invalidate All Reset Tokens]
    InvalidateTokens --> LogPasswordChange[Log Password Change in Audit]
    LogPasswordChange --> Success([Password Reset Successful])
```

## Security Best Practices Implemented

### 1. Password Security
- ✅ Bcrypt hashing with cost factor 12
- ✅ Salt automatically generated by bcrypt
- ✅ Minimum password length: 8 characters
- ✅ No plaintext password storage
- ✅ Constant-time comparison to prevent timing attacks

### 2. Rate Limiting
- ✅ 5 failed attempts trigger 15-minute lockout
- ✅ Attempt counter per username
- ✅ Automatic lock expiration after time window
- ✅ Failed attempts logged in audit trail

### 3. Session Management
- ✅ Automatic session timeout after 60 minutes
- ✅ Activity tracking with timestamp updates
- ✅ Session checker runs every 60 seconds
- ✅ Automatic logout on session expiration

### 4. Audit Logging
- ✅ All authentication events logged
- ✅ Structured JSON format for parsing
- ✅ Timestamps in UTC
- ✅ User context included in logs
- ✅ Request tracking with request_id

### 5. Configuration Security
- ✅ No hardcoded credentials
- ✅ Environment-based configuration
- ✅ Production-specific validation rules
- ✅ Configuration validation at startup

### 6. Error Handling
- ✅ Generic error messages to users
- ✅ Detailed logging for debugging
- ✅ No sensitive information in errors
- ✅ Stack traces logged but not shown to users

---

**Document Version:** 1.0
**Last Updated:** 2025-03-14
