# IT-BE Code Rules and Standards

A comprehensive guide for all developers contributing to the IT-BE backend system.

**Version**: 1.0  
**Status**: Strict - enforcement required for all PRs  
**Last Updated**: 2026-04-13

---

## 1. Architecture and Module Structure

### 1.1 Module-Based Organization

All features must be implemented as **self-contained Django modules** in \modules/\.

All module must follow this structure:
- models/ directory with __init__.py containing all models
- serializers.py for all serializers
- views.py for all viewsets
- urls.py for route registration
- tests.py for APITestCase tests
- admin.py for Django admin
- migrations/ auto-generated

Do NOT create subfolders like views/ or models/views.py.

### 1.2 Layer Responsibilities

**models/**: Domain entities only
- Define models with all DB fields
- Use model validators for constraints
- Use custom managers for complex queries

**serializers.py**: Data transformation
- Define serializers for API requests/responses
- Use \	o_representation()\ for mapping Vietnamese to English API fields
- Implement field validation in \alidate_<field>()\

**views.py**: HTTP endpoint logic
- Define viewsets with \get_permissions()\ for role checks
- Implement \get_queryset()\ for filtering
- Raise \ValidationError\ for bad params (HTTP 400)
- Keep business logic minimal; delegate to services

**services/**: Domain business logic
- Complex calculations and workflows
- External API calls
- Place in \services/<module_name>_service.py\

**urls.py**: Route registration
- Use DefaultRouter for CRUD
- Register viewsets with consistent basename
- Do NOT inline views

---

## 2. Naming Conventions

### 2.1 Model Names (PascalCase)

✅ Model names in ENGLISH, domain-meaningful:
- HoSoUngVien (Candidate Profile)
- TinTuyenDung (Job Posting)
- DanhGia (Review/Rating)

❌ WRONG:
- CandidateProfile (mix Vietnamese domain with English)
- ho_so_ung_vien (lowercase)

### 2.2 Model Fields (snake_case, Vietnamese)

✅ Use Vietnamese field names for domain mapping:
- ho_ten, so_dien_thoai, ky_nang, luong_mong_muon
- tao_luc (created), cap_nhat_luc (updated)
- Use db_column for explicit FK IDs
- Use db_table = \"UPPERCASE\" for all models

### 2.3 Serializer Names

Match model name + \"Serializer\":
- HoSoUngVienSerializer
- TinTuyenDungSerializer

For variants: HoSoUngVienListSerializer, HoSoUngVienDetailSerializer

### 2.4 ViewSet Names

Match model name + \"ViewSet\":
- HoSoUngVienViewSet
- TinTuyenDungViewSet

### 2.5 URL Basename

English, kebab-case:
\\\python
basename=\"users\"
basename=\"job-posts\"
basename=\"candidate-profile\"
\\\

### 2.6 Private Methods

Prefix with underscore:
\\\python
def _format_salary(self):
    pass
def _build_summary(self):
    pass
\\\

---

## 3. Import Organization

### 3.1 All Absolute Imports

✅ CORRECT:
\\\python
from modules.accounts.models import NguoiDung
from modules.jobs.serializers import TinTuyenDungSerializer
from services.matching_service import compute_score
\\\

❌ WRONG:
\\\python
from . import models  # Relative
from .models import NguoiDung  # Relative
\\\

### 3.2 Import Order

1. Python stdlib (os, sys, decimal, etc.)
2. Django (django.*, rest_framework)
3. Local imports (modules.*, services.*, utils.*)

All alphabetical within groups.

---

## 4. Django/DRF Patterns

### 4.1 Role-Based Permissions

Use \get_permissions()\ to enforce role checks:

\\\python
def get_permissions(self):
    if self.action in [\"list\", \"retrieve\"]:
        return [IsEmployer()]  # Role-based guard
    elif self.action == \"update\":
        return [IsCandidate()]
    return [permissions.IsAuthenticated()]
\\\

### 4.2 Query Parameter Validation

Explicit validation in \get_queryset()\:

\\\python
def get_queryset(self):
    queryset = Model.objects.select_related(\"fk_field\")
    status = self.request.query_params.get(\"status\", \"\").strip() or \"default\"
    
    if status not in self.allowed_statuses:
        raise ValidationError({\"status\": \"Invalid status value\"})
    
    keyword = self.request.query_params.get(\"q\", \"\").strip()
    if keyword:
        queryset = queryset.filter(Q(field1__icontains=keyword) | Q(field2__icontains=keyword))
    
    return queryset
\\\

### 4.3 Response Shaping with to_representation()

Map Vietnamese fields to English API fields:

\\\python
def to_representation(self, instance):
    data = super().to_representation(instance)
    data[\"title\"] = data.get(\"tieu_de\") or \"\"
    data[\"salary\"] = self._format_salary(data.get(\"luong_theo_gio\"))
    data[\"status\"] = self._format_status(data.get(\"trang_thai\"))
    return data

@staticmethod
def _format_salary(value):
    return f\"{value} / hour\" if value else \"Not updated\"
\\\

### 4.4 QuerySet Optimization

Always use \select_related()\ and \prefetch_related()\:

\\\python
queryset = Model.objects.select_related(\"fk_field\").prefetch_related(\"reverse_fk\")
\\\

### 4.5 Use Q Objects for Complex Filters

\\\python
queryset.filter(Q(field1__icontains=kw) | Q(field2__icontains=kw) | Q(field3__icontains=kw))
\\\

---

## 5. Error Handling

### 5.1 HTTP Status Codes

- 200 OK: Success, empty array for no results
- 201 Created: Resource created
- 400 Bad Request: Invalid query params
- 401 Unauthorized: No JWT
- 403 Forbidden: Wrong role
- 404 Not Found: Resource not found
- 409 Conflict: Duplicate/conflict error

### 5.2 Error Format

Always return structured JSON with field-level details:

\\\python
raise ValidationError({\"salary_min\": \"Must be numeric\", \"sort\": \"Invalid option\"})
# Returns HTTP 400 with field details
\\\

### 5.3 Empty Results

Always return 200 with empty array, NEVER error:

\\\json
{
  \"page\": 1,
  \"limit\": 20,
  \"total\": 0,
  \"results\": []
}
\\\

---

## 6. Testing

### 6.1 Test File Location

Each module has \	ests.py\ with \APITestCase\:

\\\python
# modules/profiles/tests.py
from rest_framework.test import APITestCase

class HoSoUngVienViewSetTests(APITestCase):
    def setUp(self):
        self.user = NguoiDung.objects.create_user(...)
    
    def test_list_requires_employer_role(self):
        response = self.client.get(\"/api/v1/candidates\")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
\\\

### 6.2 Test Naming

Descriptive names with scenario and outcome:

\\\python
def test_list_candidates_requires_employer_role(self):
def test_filter_by_salary_returns_matching_results(self):
def test_invalid_sort_param_returns_400(self):
def test_empty_search_returns_200_empty_array(self):
\\\

### 6.3 Test Coverage Checklist

- ✅ Auth (401 unauthenticated, 403 wrong role)
- ✅ Happy path (200 correct data)
- ✅ Invalid input (400 bad params)
- ✅ Not found (404 missing resource)
- ✅ Empty result (200 empty array)
- ✅ Filtering (each filter independent + combined)
- ✅ Sorting (all sort options)
- ✅ Pagination (boundaries)

---

## 7. Git Workflow

### 7.1 Branch Naming

\\\
feature/candidate-listing
feature/matching-score
bugfix/salary-decimal-parse
docs/update-rules
\\\

### 7.2 Commit Messages

Clear, English, descriptive:

\\\
feat: add GET /api/v1/candidates endpoint
fix: handle decimal parsing in salary filter
docs: update code-rules
chore: upgrade requirements
\\\

### 7.3 Pull Request

Every PR must have:
- Clear title and description
- List of changed files
- Migration notes
- Test evidence
- API contract changes (if any)
- At least 2 approvals before merge

---

## 8. Security Guidelines

### 8.1 Never Skip Auth

\\\python
def get_permissions(self):
    return [IsEmployer()]  # Always enforce some permission
\\\

### 8.2 Hide Sensitive Data

\\\python
class NguoiDungSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        fields = [\"id\", \"email\", \"vai_tro\"]  # NO password in response
\\\

### 8.3 Validate All Input

\\\python
class Model(models.Model):
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
\\\

---

## 9. API Endpoint Definition

### 9.1 Endpoint Naming Convention

All endpoints follow REST principles and are versioned:

\\\
GET    /api/v1/resource
POST   /api/v1/resource
GET    /api/v1/resource/{id}
PUT    /api/v1/resource/{id}
PATCH  /api/v1/resource/{id}
DELETE /api/v1/resource/{id}
GET    /api/v1/resource/{id}/related-resource
\\\

✅ CORRECT naming:
- /api/v1/candidates (list)
- /api/v1/candidates/{candidate_id} (detail)
- /api/v1/job-posts/{job_id}/matched-candidates (scoped list)
- /api/v1/applications (create)

❌ WRONG:
- /api/candidate_list (mix snake_case)
- /candidates (no versioning)
- /api/v1/get_candidates (verb in URL)
- /api/v1/candidates/search (non-standard action)

### 9.2 Request Methods

Use correct HTTP methods:

- **GET**: Retrieve data (safe, idempotent)
- **POST**: Create resource (idempotent with request ID)
- **PUT**: Replace entire resource (idempotent)
- **PATCH**: Partial update (idempotent)
- **DELETE**: Remove resource (idempotent)
- HEAD, OPTIONS: Metadata only

### 9.3 Query Parameters

Standard query parameter names (English, lowercase):

\\\python
# Filtering
?q=keyword              # Search text
?status=active          # Enum filter
?location=hanoi         # Category filter
?salary_min=5000        # Range filters
?salary_max=20000

# Sorting
?sort=-updated_at       # Descending (- prefix)
?sort=salary            # Ascending

# Pagination
?page=1                 # 1-indexed
?limit=20               # Items per page (max 100)

# Combined
?q=python&location=hanoi&sort=-updated_at&page=2&limit=50
\\\

### 9.4 Response Structure

All responses follow consistent JSON schema:

**List Response (HTTP 200):**
\\\json
{
  "page": 1,
  "limit": 20,
  "total": 150,
  "results": [
    {
      "id": "uuid-or-pk",
      "name": "value",
      "created_at": "2026-04-13T10:30:00Z",
      "updated_at": "2026-04-13T10:30:00Z"
    }
  ]
}
\\\

**Detail Response (HTTP 200):**
\\\json
{
  "id": "uuid-or-pk",
  "name": "value",
  "description": "...",
  "created_at": "2026-04-13T10:30:00Z",
  "updated_at": "2026-04-13T10:30:00Z",
  "meta": {
    "created_by": "user_id",
    "status": "active"
  }
}
\\\

**Create Response (HTTP 201):**
\\\json
{
  "id": "new-uuid",
  "name": "value",
  "created_at": "2026-04-13T10:30:00Z"
}
\\\

**Error Response (HTTP 400/403/404):**
\\\json
{
  "error": "Bad Request",
  "message": "Invalid query parameters",
  "details": {
    "salary_min": ["Must be numeric"],
    "location": ["Invalid region code"]
  }
}
\\\

### 9.5 Request Body Schema

Standard request body format for POST/PUT/PATCH:

\\\json
{
  "full_name": "Nguyen Van A",
  "email": "contact@example.com",
  "phone": "+84912345678",
  "location": "Ho Chi Minh City",
  "expected_salary": 50000
}
\\\

### 9.6 Timestamp Format

All timestamps use ISO 8601 with UTC timezone:

\\\
2026-04-13T10:30:45Z          ✅ Correct
2026-04-13T10:30:45+00:00     ✅ Acceptable
2026-04-13 10:30:45            ❌ Wrong
13/04/2026 10:30               ❌ Wrong
\\\

Use \timezone.now()\ in serializers:

\\\python
class MySerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    
    def get_created_at(self, obj):
        return obj.tao_luc.isoformat() if obj.tao_luc else None
\\\

### 9.7 HTTP Status Codes

Endpoint should return appropriate status codes:

| Status | Meaning | When |
|--------|---------|------|
| 200 | OK | GET/PUT/PATCH successful, or empty list |
| 201 | Created | POST successful resource creation |
| 204 | No Content | DELETE successful (no body) |
| 400 | Bad Request | Invalid query params or body |
| 401 | Unauthorized | Missing or invalid JWT |
| 403 | Forbidden | Authenticated but wrong role |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate entry or integrity violation |
| 422 | Unprocessable | Validation failed on valid JSON |
| 429 | Rate Limited | Too many requests |
| 500 | Server Error | Unexpected exception |

### 9.8 Versioning Strategy

All APIs use URL-based versioning:

\\\python
# Current version
/api/v1/candidates

# When major breaking changes needed
/api/v2/candidates

# Never support multiple versions in same code
# Create new ViewSet if breaking changes required
\\\

### 9.9 Content Negotiation

Always return JSON:

\\\python
class MyViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer]  # JSON only
    parser_classes = [JSONParser]      # JSON only
\\\

### 9.10 CORS and Content-Type

- Accept: application/json
- Content-Type: application/json
- CORS headers handled by middleware
- No XML, form-data, or custom content types

---

## 10. Code Style

### 10.1 PEP 8 with Black

Format before push:
\\\ash
black modules/
flake8 modules/ --max-line-length=120
\\\

### 10.2 Line Length

Max 120 characters per line.

### 10.3 Type Hints

Recommended in services and complex functions:

\\\python
def create_user(email: str, password: str, vai_tro: str = \"ung_vien\") -> NguoiDung:
    return NguoiDung.objects.create_user(...)

def compute_score(skills: list[str], location: str) -> float:
    return 85.5
\\\

---

## 11. Database Migrations

### 11.1 Always Create Migrations

\\\ash
python manage.py makemigrations
python manage.py migrate
\\\

### 11.2 Migration Naming

Descriptive, never auto-generated:

✅ CORRECT:
\\\
0002_add_avatar_location_to_hosounguien.py
0003_add_availability_slots_json_field.py
\\\

❌ WRONG:
\\\
0002_auto_20260413_1234.py  # Auto-generated, unclear
# Never rewrite applied migrations!
\\\

---

## 12. Documentation

### 12.1 Comments Explain WHY

✅ CORRECT:
\\\python
# Decimal parse ensures float precision in salary ranges
min_salary = Decimal(salary_min)
\\\

❌ WRONG:
\\\python
# Convert string to decimal
min_salary = Decimal(salary_min)
\\\

### 12.2 No Docstrings on Models/Serializers/Views

Code is self-documented via clear naming.

### 12.3 API Docs

Update \docs/contract/\ whenever endpoint signature changes.

---

## 13. Performance Checklist

Before submitting PR:
- ✅ \select_related()\ for all ForeignKey access
- ✅ \prefetch_related()\ for reverse relationships
- ✅ No N+1 queries in list endpoints
- ✅ Pagination implemented for large results
- ✅ Response payload only necessary fields

---

## 14. Definition of Done

Task is done only when:
1. ✅ Code follows all rules in this document
2. ✅ All tests pass (\pytest\
3. ✅ Code formatted with \black\ + passes \flake8\
4. ✅ API contract docs updated (if endpoint changed)
5. ✅ Migration included and tested
6. ✅ No breaking changes to existing APIs
7. ✅ PR reviewed and approved by 2 team members
8. ✅ CI/CD pipeline green

---

## 15. FAQ

**Q: Can I use relative imports?**  
A: No, always absolute imports.

**Q: Should I register all models in admin.py?**  
A: Yes, even if not used immediately.

**Q: Where do I put complex logic?**  
A: In \services/<module>_service.py\, not in views or serializers.

**Q: Do I always need type hints?**  
A: In services yes; in models/serializers/views no.

**Q: How do I handle transactions?**  
A: Use \@transaction.atomic\ decorator.

**Q: Max response payload size?**  
A: Aim for < 1MB; use pagination for large results.

---

## 16. Enforcement

- Code review checklist must reference this document
- Violations: PR blocked until compliant
- Updates: Require approval from tech leads

---

**Contact**: Questions? Ask the tech lead team.

**Last Reviewed**: 2026-04-13
