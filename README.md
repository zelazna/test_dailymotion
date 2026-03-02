# User Registration API

A user registration and email verification API built with FastAPI and PostgreSQL.

## Running the application

```bash
docker compose up --build
```

This starts two containers:

- **api** — FastAPI application on http://localhost:8000
- **db** — PostgreSQL 16

The API is ready when `docker compose up` shows the uvicorn startup log. You can also check:

```bash
curl http://localhost:8000/status
```

## Running the tests

```bash
docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm --build test
```

This spins up a dedicated in-memory PostgreSQL database, runs the full test suite, then removes the container. No application containers need to be running beforehand.

## Application Schema

### Database

```mermaid
erDiagram
    users {
        UUID        id           PK
        TEXT        email        UK
        TEXT        password_hash
        BOOLEAN     is_active
        TIMESTAMPTZ created_at
    }
    verification_codes {
        UUID        id         PK
        UUID        user_id    FK
        CHAR4       code
        TIMESTAMPTZ expires_at
        TIMESTAMPTZ created_at
    }
    users ||--o| verification_codes : "has"
```

> `verification_codes.user_id` is a `UNIQUE` index — one code per user at a time.

---

### Application layers

```mermaid
graph TD
    Client["HTTP Client"]

    subgraph API["FastAPI"]
        Routes["Routes"]
        Depends["Dependencies"]
        Models["Pydantic Models"]
    end

    subgraph Services["Service layer"]
        UserService["UserService"]
        ResendClient["ResendClient"]
        HttpPool["httpx.AsyncClient"]
    end

    subgraph DB["Database layer"]
        Pool["asyncpg Pool"]
        UserDB["db/user"]
        CodeDB["db/verification_code"]
    end

    External["Resend API"]
    Postgres[("PostgreSQL")]

    Client --> Routes
    Routes --> Depends
    Routes --> Models
    Depends --> UserService
    UserService --> ResendClient
    UserService --> UserDB
    UserService --> CodeDB
    UserDB --> Pool
    CodeDB --> Pool
    Pool --> Postgres
    ResendClient --> HttpPool
    HttpPool --> External
```

---

### Registration flow

```mermaid
sequenceDiagram
    actor Client
    participant Route as POST /users
    participant Service as UserService
    participant DB as PostgreSQL
    participant Email as Resend API

    Client->>Route: POST /users {email, password}
    Route->>Service: create_user(email, password)
    Service->>Service: hash password (Argon2)
    Service->>DB: BEGIN
    Service->>DB: INSERT users → id
    Service->>DB: INSERT verification_codes (code, expires_at)
    Service->>DB: COMMIT
    Service-->>Route: User
    Route-->>Client: 201 {id, email, created_at}
    Route-)Email: (background) send verification code email
```

---

### Activation flow

```mermaid
sequenceDiagram
    actor Client
    participant Auth as HTTP Basic Auth
    participant Route as POST /users/activate
    participant Service as UserService
    participant DB as PostgreSQL

    Note over Client: Authorization: Basic email:password
    Client->>Auth: POST /users/activate {code}
    Auth->>Service: get_authenticated_user(email, password)
    Service->>DB: SELECT users + verification_codes WHERE email = ?
    DB-->>Service: row
    Service->>Service: verify password (Argon2)
    Service-->>Auth: User
    Auth-->>Route: authenticated User

    Route->>Service: activate_user(user, code)
    Service->>DB: BEGIN
    Service->>DB: SELECT … FOR UPDATE OF users WHERE id = ?
    Note over DB: Row locked — concurrent requests block here

    alt user already active
        Service-->>Route: True (idempotent)
        Route-->>Client: 200 "User activated successfully"
    else no verification code
        Service-->>Route: CodeNotFoundError
        Route-->>Client: 404
    else code expired
        Service-->>Route: CodeExpiredError
        Route-->>Client: 400
    else code mismatch
        Service-->>Route: CodeInvalidError
        Route-->>Client: 400
    else code valid
        Service->>DB: UPDATE users SET is_active = TRUE
        Service->>DB: COMMIT
        Service-->>Route: True
        Route-->>Client: 200 "User activated successfully"
    end
```
