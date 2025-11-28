# Security Considerations for Dovos

**Last Updated:** November 28, 2025

This document outlines security considerations, vulnerabilities, and recommended mitigations for the Dovos chat conversation archive and search application.

## Executive Summary

Dovos currently operates without authentication, authorization, or most security hardening measures. While acceptable for local development, **the application should NOT be deployed to production or exposed to the internet without addressing the critical security issues outlined below.**

## Current Security Posture

### Architecture Overview
- Flask-based web application with PostgreSQL backend
- Docker containerized deployment with pgvector support
- RAG (Retrieval-Augmented Generation) integration with OpenWebUI
- Full-text search and vector similarity search capabilities
- No authentication or authorization layer

---

## Critical Security Issues

### 1. Authentication & Authorization

**Status:** ❌ Not Implemented

**Issues:**
- No user authentication system (no login, JWT, or session management)
- All API endpoints are publicly accessible
- No role-based access control (RBAC)
- Anyone can read, modify, or delete conversations

**Affected Endpoints:**
- `GET /api/conversations` - List all conversations (no auth required)
- `GET /api/conversation/<id>` - View any conversation (no auth required)
- `DELETE /api/conversation/<id>` - Delete any conversation (no auth required)
- `DELETE /api/clear` - Wipe entire database (no auth required)
- `POST /api/rag/query` - Query conversation data (no auth required)
- `POST /export_to_openwebui/<id>` - Export conversations (no auth required)

**Recommendations:**

**Option 1: API Key Authentication (Quick Win)**
```python
# Add to routes.py or middleware
from functools import wraps
from flask import request, jsonify

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.getenv('API_KEY'):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Apply to sensitive endpoints
@app.route("/api/conversations", methods=["GET"])
@require_api_key
def api_conversations():
    return jsonify(postgres_controller.get_conversations())
```

**Option 2: JWT Token-Based Authentication (Recommended)**
- Implement user registration and login
- Use Flask-JWT-Extended for token management
- Add user-conversation ownership relationships
- Implement proper session management

**Option 3: OAuth2/OIDC Integration**
- Integrate with external identity provider (e.g., Auth0, Keycloak)
- Better for multi-user deployments

---

### 2. Secrets Management

**Status:** ❌ Critical - Hardcoded Secrets

**Issues:**

1. **Hardcoded in Source Code** (`config/__init__.py`):
```python
SECRET_KEY = "your-secret-key-change-this-in-production"
OPENWEBUI_URL = "http://100.116.198.80:3000"
OPENWEBUI_API_KEY = "sk-44016316021243d0b0a00ba36aa0c22e"
```

2. **Real Secrets in `.env.example`**:
```env
POSTGRES_PASSWORD=dovos_password
OPENWEBUI_API_KEY=sk-44016316021243d0b0a00ba36aa0c22e
```

3. **Exposed via Docker**:
- `docker inspect` reveals all environment variables
- Docker logs may contain secrets
- Secrets visible in `docker-compose.yml`

**Risks:**
- Secrets committed to version control history
- Exposed via GitHub/GitLab if repository is public
- Internal network IP addresses exposed (100.116.198.80)
- Anyone with Docker access can extract secrets

**Recommendations:**

**Immediate Actions:**
1. Remove hardcoded secrets from `config/__init__.py`:
```python
# config/__init__.py
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")

OPENWEBUI_URL = os.getenv("OPENWEBUI_URL")
OPENWEBUI_API_KEY = os.getenv("OPENWEBUI_API_KEY")
```

2. Rotate all exposed secrets:
   - Generate new `SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"`
   - Generate new `POSTGRES_PASSWORD`
   - Regenerate OpenWebUI API key

3. Update `.env.example` to use placeholders:
```env
POSTGRES_PASSWORD=CHANGE_ME_TO_SECURE_PASSWORD
OPENWEBUI_API_KEY=your-openwebui-api-key-here
SECRET_KEY=generate-with-secrets-token-hex-32
```

4. Add `.env` to `.gitignore` (already done ✓)

**For Production:**
- Use Docker secrets or Kubernetes secrets
- Use a secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
- Implement secret rotation policies
- Never log secrets

---

### 3. Cross-Origin Resource Sharing (CORS)

**Status:** ❌ Wide Open

**Current Implementation** (`app.py:13`):
```python
CORS(app)  # Allows ALL origins
```

**Risk:**
- Any website can make requests to your API
- Enables Cross-Site Request Forgery (CSRF) attacks
- Third-party sites can exfiltrate conversation data

**Recommendations:**

```python
# app.py
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",
            "http://localhost:5001",
            os.getenv("OPENWEBUI_URL", "").rstrip("/")
        ],
        "methods": ["GET", "POST", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

---

### 4. Rate Limiting

**Status:** ❌ Not Implemented

**Risk:**
- API endpoints can be hammered without restriction
- Denial of Service (DoS) attacks
- Resource exhaustion (CPU, memory, database connections)
- Expensive embedding operations can be triggered repeatedly

**Vulnerable Endpoints:**
- `/api/rag/query` - Resource-intensive vector searches
- `/upload` - File processing and embedding generation
- `/api/search` - Database-intensive operations

**Recommendations:**

```python
# Install: pip install Flask-Limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Use Redis for production
)

# Apply different limits to different endpoints
@app.route("/api/rag/query", methods=["POST"])
@limiter.limit("10 per minute")
def api_rag_query():
    # ...

@app.route("/upload", methods=["POST"])
@limiter.limit("5 per hour")
def upload():
    # ...
```

---

## High Priority Security Issues

### 5. Input Validation & Sanitization

**Status:** ⚠️ Minimal/None

**Issues:**
- No input length validation
- No content type validation
- No sanitization of user-provided content
- Query parameters not validated

**Vulnerable Areas:**

1. **Search Queries** (`/api/search`, `/api/rag/query`):
   - No length limits (can cause resource exhaustion)
   - No special character filtering

2. **File Uploads** (`/upload`):
   - No file type validation (check actual content, not just extension)
   - No file size limits
   - No malware scanning
   - No sanitization of uploaded content

3. **Conversation IDs**:
   - UUIDs not validated before database queries
   - Could cause errors or expose error messages

**Recommendations:**

```python
from uuid import UUID
from werkzeug.utils import secure_filename

# Input validation decorator
def validate_json_input(required_fields):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid JSON"}), 400
            
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing field: {field}"}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# UUID validation
def validate_uuid(uuid_string):
    try:
        UUID(uuid_string, version=4)
        return True
    except (ValueError, AttributeError):
        return False

# Query length validation
MAX_QUERY_LENGTH = 10000

@app.route("/api/rag/query", methods=["POST"])
def api_rag_query():
    data = request.get_json()
    query_text = data.get('query', '')
    
    if len(query_text) > MAX_QUERY_LENGTH:
        return jsonify({"error": "Query too long"}), 400
    
    # ... rest of handler

# File upload validation
ALLOWED_EXTENSIONS = {'json', 'txt', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if not file or file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type"}), 400
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    if file_length > MAX_FILE_SIZE:
        return jsonify({"error": "File too large"}), 400
    file.seek(0)
    
    # Secure the filename
    filename = secure_filename(file.filename)
    
    # ... process file
```

---

### 6. SQL Injection Protection

**Status:** ✅ Good (with caveats)

**Current State:**
- Using SQLAlchemy ORM (protects against most SQL injection)
- Parameterized queries with `text()` (good practice observed)

**Example of Safe Implementation** (`db/repositories/message_repository.py`):
```python
sql_query = text("""
    SELECT ... FROM messages m
    WHERE m.message_search @@ plainto_tsquery('english', :query)
""")
result = self.session.execute(sql_query, {'query': query})
```

**Recommendations:**
- ✅ Continue using parameterized queries
- ✅ Never concatenate user input into SQL strings
- ⚠️ Review any dynamic SQL generation
- ⚠️ Be cautious with string formatting in queries

---

### 7. Network Security

**Status:** ❌ Multiple Exposure Issues

**Issues:**

1. **Exposed PostgreSQL Port** (`docker-compose.yml:14`):
```yaml
ports:
  - "5432:5432"  # Accessible from 0.0.0.0
```
- Database accessible from any network interface
- No firewall rules
- Should only be accessible from application container

2. **Application Binding** (`app.py:35`):
```python
app.run(host='0.0.0.0', port=5001)
```
- Accessible from all network interfaces
- No network isolation

3. **No TLS/HTTPS**:
- All traffic in plaintext
- Credentials, API keys, and conversation data transmitted unencrypted

4. **Internal IP Exposure**:
- Tailscale IP `100.116.198.80` hardcoded in config
- Reveals network topology

**Recommendations:**

1. **Remove PostgreSQL Port Exposure**:
```yaml
# docker-compose.yml
postgres:
  # Remove or comment out ports section
  # ports:
  #   - "5432:5432"
  
  # Database only accessible via Docker network
```

2. **Use Reverse Proxy with TLS**:
```yaml
# Add nginx service to docker-compose.yml
nginx:
  image: nginx:alpine
  ports:
    - "443:443"
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - ./certs:/etc/nginx/certs:ro
  depends_on:
    - dovos-rag
```

3. **Enable PostgreSQL SSL**:
```yaml
postgres:
  environment:
    - POSTGRES_SSL_MODE=require
```

4. **Network Segmentation**:
- Use Docker network isolation
- Implement firewall rules
- Use VPN for remote access (already using Tailscale ✓)

---

### 8. Container Security

**Status:** ⚠️ Basic Hardening Needed

**Current Issues** (`Dockerfile`):

1. **Running as Root**:
```dockerfile
# No USER directive - runs as root
```

2. **No Health Checks** (Docker level)

3. **Broad Base Image**:
```dockerfile
FROM python:3.11-slim
```

**Recommendations:**

```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r dovos && useradd -r -g dovos dovos

# Set working directory
WORKDIR /app

# Install dependencies as root
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=dovos:dovos . .

# Create logs directory with proper permissions
RUN mkdir -p logs && chown -R dovos:dovos logs

# Switch to non-root user
USER dovos

EXPOSE 5001

ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "app.py"]
```

**Additional Container Security:**
- Scan images for vulnerabilities (use `docker scan` or Trivy)
- Use read-only root filesystem where possible
- Drop unnecessary capabilities
- Implement AppArmor/SELinux profiles

---

## Medium Priority Security Issues

### 9. Dependency Management

**Status:** ⚠️ Unpinned Versions

**Current State** (`requirements.txt`):
```txt
flask              # No version specified
flask-cors         # No version specified
sqlalchemy>=2.0    # Minimum version only
```

**Risks:**
- Vulnerable dependencies may be installed
- Breaking changes in minor/patch versions
- Supply chain attacks
- Inconsistent builds across environments

**Recommendations:**

1. **Pin All Dependencies**:
```bash
pip freeze > requirements.txt
```

2. **Use Dependency Scanning**:
```bash
# Install safety
pip install safety

# Check for vulnerabilities
safety check

# Or use pip-audit
pip install pip-audit
pip-audit
```

3. **Automate Dependency Updates**:
- Use Dependabot (GitHub)
- Use Renovate Bot
- Set up automated security scanning in CI/CD

4. **Create `requirements-lock.txt`**:
```txt
# requirements.txt - loose versions for compatibility
flask>=3.0,<4.0
sqlalchemy>=2.0,<3.0

# requirements-lock.txt - exact versions for production
flask==3.0.2
sqlalchemy==2.0.29
```

---

### 10. Logging & Monitoring

**Status:** ⚠️ Minimal

**Current State:**
- Basic error logging in routes (`routes.py:215`)
- No security event logging
- No audit trail
- Logs stored locally (`/app/logs`)

**Missing:**
- Authentication attempts (N/A - no auth yet)
- Failed authorization attempts
- Data access patterns
- Suspicious activity detection
- Rate limit violations

**Recommendations:**

```python
import logging
from logging.handlers import RotatingFileHandler
import json

# Structured logging
class SecurityAuditLogger:
    def __init__(self):
        self.logger = logging.getLogger('security')
        handler = RotatingFileHandler(
            'logs/security.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_access(self, user_id, resource, action, status):
        self.logger.info(json.dumps({
            'event': 'resource_access',
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'status': status,
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string
        }))
    
    def log_failed_auth(self, attempt_details):
        self.logger.warning(json.dumps({
            'event': 'failed_authentication',
            'details': attempt_details,
            'ip': request.remote_addr
        }))

security_logger = SecurityAuditLogger()

# Use in routes
@app.route("/api/conversation/<doc_id>", methods=["DELETE"])
def delete_conversation(doc_id):
    security_logger.log_access(
        user_id=get_current_user_id(),
        resource=f"conversation/{doc_id}",
        action="DELETE",
        status="success"
    )
    # ... rest of handler
```

**Centralized Logging:**
- Ship logs to ELK Stack, Splunk, or CloudWatch
- Implement log aggregation for Docker containers
- Set up alerting for suspicious patterns

---

### 11. CSRF Protection

**Status:** ❌ Not Implemented

**Issue:**
- Flask-WTF installed but not configured
- No CSRF tokens on state-changing operations
- POST/DELETE endpoints vulnerable to CSRF attacks

**Affected Endpoints:**
- `POST /upload`
- `POST /export_to_openwebui/<id>`
- `DELETE /api/conversation/<id>`
- `DELETE /api/clear`
- `POST /clear_db`

**Recommendations:**

```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    
    # Enable CSRF protection
    csrf.init_app(app)
    
    # Exempt API endpoints if using token auth
    csrf.exempt("/api/rag/query")
    
    return app
```

For API endpoints with token authentication, CSRF is less critical but still recommended for cookie-based sessions.

---

### 12. Security Headers

**Status:** ❌ Not Implemented

**Missing Headers:**
- `Content-Security-Policy` (CSP)
- `X-Frame-Options`
- `X-Content-Type-Options`
- `Strict-Transport-Security` (HSTS)
- `Referrer-Policy`
- `Permissions-Policy`

**Recommendations:**

```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'"
    )
    return response
```

Or use Flask-Talisman:
```python
from flask_talisman import Talisman

Talisman(app, 
    force_https=True,
    strict_transport_security=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'"],
        'style-src': ["'self'", "'unsafe-inline'"]
    }
)
```

---

## Data Security

### 13. Data Encryption

**Status:** ⚠️ At Rest: Depends on Infrastructure, In Transit: None

**Current State:**
- No application-level encryption
- PostgreSQL data stored in Docker volumes (unencrypted by default)
- No TLS for API communication
- No TLS for database connections

**Sensitive Data:**
- Conversation content (may contain PII, credentials, private info)
- OpenWebUI API keys
- Database credentials

**Recommendations:**

1. **Encrypt Data at Rest:**
```bash
# Enable PostgreSQL encryption
# Use encrypted Docker volumes or host filesystem encryption

# For PostgreSQL tablespace encryption
# Requires PostgreSQL compiled with --with-ssl
```

2. **Encrypt Data in Transit:**
- Enable TLS for Flask application
- Enable SSL for PostgreSQL connections:
```python
DATABASE_URL = "postgresql+psycopg://user:pass@host:5432/db?sslmode=require"
```

3. **Encrypt Sensitive Fields:**
```python
# Use cryptography library for field-level encryption
from cryptography.fernet import Fernet

class EncryptedField:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def encrypt(self, value):
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt(self, value):
        return self.cipher.decrypt(value.encode()).decode()
```

---

### 14. Data Access Controls

**Status:** ❌ No Access Controls

**Issues:**
- No row-level security
- All conversations accessible to all (no auth)
- No data segregation between users
- Export functionality lacks access controls

**Recommendations:**

1. **Implement Row-Level Security (RLS) in PostgreSQL:**
```sql
-- Enable RLS on conversations table
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Create policy for user access
CREATE POLICY user_conversations_policy ON conversations
    USING (user_id = current_setting('app.current_user_id')::uuid);
```

2. **Add User Ownership:**
```python
# Add user_id column to conversations table
# Migration required
class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    # ... other fields
```

---

## Compliance & Privacy

### 15. Privacy Considerations

**Sensitive Data Types in Conversations:**
- Personal Identifiable Information (PII)
- API keys, passwords, credentials
- Business confidential information
- Health information (if applicable)
- Financial data

**Recommendations:**

1. **Data Minimization:**
   - Only store necessary data
   - Implement data retention policies
   - Add conversation expiration/archival

2. **PII Detection & Redaction:**
```python
import re

def detect_pii(text):
    patterns = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    }
    
    findings = {}
    for pii_type, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            findings[pii_type] = matches
    
    return findings

def redact_pii(text):
    # Implement redaction logic
    pass
```

3. **Right to Erasure:**
   - Implement complete data deletion (already have DELETE endpoint)
   - Ensure cascading deletes work properly
   - Verify embeddings are deleted with messages

4. **Data Export:**
   - Provide user data export functionality (partially implemented)
   - Include all associated metadata

---

## Deployment Security

### 16. Production Deployment Checklist

**Before Deploying to Production:**

- [ ] Enable authentication & authorization
- [ ] Rotate all secrets and use environment variables
- [ ] Configure CORS to allow only trusted origins
- [ ] Implement rate limiting
- [ ] Add input validation to all endpoints
- [ ] Remove PostgreSQL port exposure
- [ ] Enable TLS/HTTPS
- [ ] Run containers as non-root user
- [ ] Pin all dependency versions
- [ ] Enable security logging and monitoring
- [ ] Configure CSRF protection
- [ ] Add security headers
- [ ] Enable database connection encryption
- [ ] Set up firewall rules
- [ ] Configure backup strategy
- [ ] Implement intrusion detection
- [ ] Set up vulnerability scanning
- [ ] Review and test disaster recovery plan
- [ ] Conduct security audit/penetration testing

---

## Security Testing

### 17. Recommended Security Tests

**Automated Testing:**

1. **Static Analysis:**
```bash
# Install bandit for Python security linting
pip install bandit

# Run security scan
bandit -r . -ll

# Install semgrep
pip install semgrep

# Run semgrep security rules
semgrep --config=auto .
```

2. **Dependency Scanning:**
```bash
pip install safety pip-audit

safety check
pip-audit
```

3. **Container Scanning:**
```bash
# Install trivy
brew install trivy  # or appropriate install method

# Scan Docker image
trivy image dovos-rag-api
```

**Manual Testing:**

1. **Authentication Bypass Attempts**
2. **SQL Injection Testing**
3. **CSRF Token Validation**
4. **Rate Limit Verification**
5. **Input Fuzzing**
6. **API Enumeration**
7. **Privilege Escalation Tests**

---

## Incident Response

### 18. Security Incident Procedures

**Preparation:**
1. Maintain security contact information
2. Document escalation procedures
3. Prepare communication templates
4. Establish backup/restore procedures

**Detection:**
- Monitor logs for suspicious activity
- Set up alerting for anomalies
- Track failed authentication attempts
- Monitor resource usage spikes

**Response:**
1. Isolate affected systems
2. Preserve evidence (logs, snapshots)
3. Assess scope and impact
4. Contain the incident
5. Eradicate threat
6. Recover systems
7. Post-incident review

**Key Contacts:**
- Security team lead: [TBD]
- Infrastructure team: [TBD]
- Legal/Compliance: [TBD]

---

## References & Resources

### Security Best Practices
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Project](https://owasp.org/www-project-api-security/)
- [Flask Security Considerations](https://flask.palletsprojects.com/en/latest/security/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)

### Tools
- **Static Analysis:** Bandit, Semgrep
- **Dependency Scanning:** Safety, pip-audit, Snyk
- **Container Scanning:** Trivy, Clair, Anchore
- **Penetration Testing:** OWASP ZAP, Burp Suite
- **Secrets Detection:** TruffleHog, GitLeaks

---

## Changelog

- **2025-11-28:** Initial security assessment and documentation

---

## Contact

For security concerns or to report vulnerabilities, please contact:
- Security Email: [TBD]
- Project Maintainer: [TBD]

**Please do not disclose security vulnerabilities publicly until they have been addressed.**
