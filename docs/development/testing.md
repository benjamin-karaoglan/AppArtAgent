# Testing

Guide to running and writing tests for Appart Agent.

## Overview

| Test Type | Framework | Location |
|-----------|-----------|----------|
| Backend Unit | pytest | `backend/tests/` |
| Backend Integration | pytest | `backend/tests/` |
| Frontend Unit | Jest | `frontend/__tests__/` |
| E2E | Playwright | `e2e/` (planned) |

## Running Tests

### Backend Tests

```bash
# Docker
docker-compose exec backend pytest

# Local
cd backend
source .venv/bin/activate
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_dvf_service.py -v

# Specific test function
pytest tests/test_dvf_service.py::test_address_parsing -v

# Run only failed tests
pytest --lf
```

### Frontend Tests

```bash
# Docker
docker-compose exec frontend pnpm test

# Local
cd frontend
pnpm test

# Watch mode
pnpm test:watch

# With coverage
pnpm test:coverage
```

## Backend Testing

### Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_dvf_service.py  # DVF service tests
├── test_api/            # API endpoint tests
│   ├── test_analysis.py
│   ├── test_documents.py
│   └── test_properties.py
└── test_services/       # Service unit tests
    ├── test_ai_services.py
    └── test_storage.py
```

### Writing Tests

#### Basic Test

```python
# tests/test_dvf_service.py
import pytest
from app.services.dvf_service import DVFService

def test_address_parsing():
    """Test address normalization."""
    result = DVFService.normalize_address("56 rue notre-dame des champs")
    assert result == "56 RUE NOTRE-DAME DES CHAMPS"
```

#### Async Test

```python
import pytest
from app.services.ai.document_analyzer import DocumentAnalyzer

@pytest.mark.asyncio
async def test_document_classification():
    """Test document type classification."""
    analyzer = DocumentAnalyzer()
    result = await analyzer.classify_document(
        images=[test_image],
        filename="pv_ag_2024.pdf"
    )
    assert result["document_type"] in ["pv_ag", "diagnostic", "tax", "charges"]
```

#### Database Test

```python
import pytest
from sqlalchemy.orm import Session
from app.models.property import Property

def test_create_property(db_session: Session):
    """Test property creation."""
    property = Property(
        address="56 Rue Notre-Dame des Champs",
        postal_code="75006",
        city="Paris",
        asking_price=850000
    )
    db_session.add(property)
    db_session.commit()
    
    assert property.id is not None
    assert property.price_per_sqm is None  # Surface not set
```

### Fixtures

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base

@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    from app.models.user import User
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User"
    )
    db_session.add(user)
    db_session.commit()
    return user
```

### Mocking

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_document_analysis_with_mock():
    """Test with mocked AI service."""
    with patch('app.services.ai.document_analyzer.DocumentAnalyzer') as MockAnalyzer:
        mock_instance = MockAnalyzer.return_value
        mock_instance.analyze_document = AsyncMock(return_value={
            "summary": "Test summary",
            "key_findings": ["Finding 1"]
        })
        
        # Test your code that uses DocumentAnalyzer
        result = await process_document(test_doc)
        
        assert result["summary"] == "Test summary"
```

## Frontend Testing

### Test Structure

```
frontend/
├── __tests__/
│   ├── components/
│   │   └── Header.test.tsx
│   └── lib/
│       └── api.test.ts
└── src/
    └── components/
        └── Header.tsx
```

### Writing Tests

#### Component Test

```tsx
// __tests__/components/Header.test.tsx
import { render, screen } from '@testing-library/react';
import { Header } from '@/components/Header';

describe('Header', () => {
  it('renders logo', () => {
    render(<Header />);
    expect(screen.getByText('Appart Agent')).toBeInTheDocument();
  });

  it('shows login when not authenticated', () => {
    render(<Header />);
    expect(screen.getByText('Login')).toBeInTheDocument();
  });
});
```

#### Hook Test

```tsx
// __tests__/hooks/useAuth.test.tsx
import { renderHook, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';

describe('useAuth', () => {
  it('provides authentication state', () => {
    const wrapper = ({ children }) => (
      <AuthProvider>{children}</AuthProvider>
    );
    
    const { result } = renderHook(() => useAuth(), { wrapper });
    
    expect(result.current.user).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});
```

#### API Test

```tsx
// __tests__/lib/api.test.ts
import { api } from '@/lib/api';

describe('api', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  it('makes GET request with auth header', async () => {
    (fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: 'test' })
    });

    await api.get('/properties');

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/properties'),
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          'Authorization': expect.any(String)
        })
      })
    );
  });
});
```

## Test Coverage

### Backend Coverage Report

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Frontend Coverage Report

```bash
pnpm test:coverage
open coverage/lcov-report/index.html
```

### Coverage Targets

| Area | Target | Current |
|------|--------|---------|
| Backend overall | 80% | TBD |
| API endpoints | 90% | TBD |
| AI services | 70% | TBD |
| Frontend components | 80% | TBD |

## CI/CD Integration

Tests run automatically on pull requests:

```yaml
# .github/workflows/test.yml
name: Tests
on: [pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: |
          cd backend
          uv pip install -e ".[dev]"
          pytest --cov=app
  
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - run: |
          cd frontend
          pnpm install
          pnpm test
```
