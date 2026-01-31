# Contributing

Guidelines for contributing to Appart Agent.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Set up development environment
4. Create a feature branch
5. Make your changes
6. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/benjamin-karaoglan/appart-agent.git
cd appart-agent

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/appart-agent.git

# Start development environment
docker-compose up -d
```

## Workflow

### 1. Create a Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/description` | `feature/add-pdf-export` |
| Bug fix | `fix/description` | `fix/login-redirect` |
| Docs | `docs/description` | `docs/api-reference` |
| Refactor | `refactor/description` | `refactor/storage-service` |

### 2. Make Changes

Follow coding standards (see below).

### 3. Test Changes

```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend pnpm test

# Type checking
docker-compose exec backend mypy app/
docker-compose exec frontend pnpm type-check
```

### 4. Commit Changes

Write clear commit messages:

```bash
git add .
git commit -m "feat: add PDF export functionality

- Add PDF generation service
- Create export endpoint
- Add tests for PDF generation"
```

#### Commit Message Format

```
<type>: <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

### 5. Push Changes

```bash
git push origin feature/your-feature-name
```

### 6. Create Pull Request

1. Go to GitHub and create PR
2. Fill in the PR template
3. Request review
4. Address feedback
5. Merge when approved

## Coding Standards

### Python (Backend)

**Style**:
- Follow PEP 8
- Use Black for formatting
- Maximum line length: 100

**Type Hints**:
```python
def process_document(
    document_id: int,
    options: dict[str, Any] | None = None
) -> DocumentResult:
    ...
```

**Docstrings**:
```python
def analyze_document(self, doc: Document) -> Analysis:
    """Analyze a document using AI.
    
    Args:
        doc: Document to analyze
        
    Returns:
        Analysis result with summary and findings
        
    Raises:
        AnalysisError: If analysis fails
    """
```

**Imports**:
```python
# Standard library
import json
from typing import Any

# Third-party
from fastapi import APIRouter
from sqlalchemy.orm import Session

# Local
from app.models import Document
from app.services import DocumentService
```

### TypeScript (Frontend)

**Style**:
- Use ESLint configuration
- Use Prettier for formatting

**Type Definitions**:
```typescript
interface Property {
  id: number;
  address: string;
  postalCode: string;
  askingPrice: number;
}

function PropertyCard({ property }: { property: Property }) {
  // ...
}
```

**Component Structure**:
```typescript
// 1. Imports
import { useState } from 'react';

// 2. Types
interface Props {
  title: string;
}

// 3. Component
export function MyComponent({ title }: Props) {
  // Hooks
  const [state, setState] = useState(false);
  
  // Handlers
  const handleClick = () => { ... };
  
  // Render
  return <div>{title}</div>;
}
```

## Pull Request Guidelines

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Added comments for complex logic
- [ ] Updated documentation
- [ ] No new warnings
```

### Review Process

1. **Automated checks** must pass
2. **At least one approval** required
3. **Address all comments** before merge
4. **Squash and merge** preferred

## Documentation

### When to Update Docs

- Adding new features
- Changing API endpoints
- Modifying configuration
- Fixing incorrect documentation

### Documentation Location

| Content | Location |
|---------|----------|
| API reference | `docs/backend/api-reference.md` |
| Architecture | `docs/architecture/` |
| Setup guides | `docs/getting-started/` |
| Code comments | Inline docstrings |

## Reporting Issues

### Bug Reports

Include:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Logs if applicable

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative approaches considered

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

## Questions?

- Open a GitHub issue
- Check existing documentation
- Review similar PRs for examples
