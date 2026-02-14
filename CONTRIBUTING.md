# Contributing to Fitness Smarty AI

Thank you for your interest in contributing to Fitness Smarty AI! This document provides guidelines for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in the Issues section
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable
   - Environment details (OS, Python/Node version, etc.)

### Suggesting Features

1. Check existing issues and discussions for similar suggestions
2. Create a new issue with:
   - Clear description of the feature
   - Use cases and benefits
   - Potential implementation approach

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes**:
   - Follow the existing code style
   - Add tests for new features
   - Update documentation as needed
3. **Test your changes**:
   - Run backend tests: `pytest`
   - Run frontend tests: `npm test`
   - Ensure all tests pass
4. **Commit your changes**:
   - Use clear, descriptive commit messages
   - Reference related issues
5. **Push to your fork** and submit a pull request

## Development Setup

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

## Code Style Guidelines

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints for function parameters and return values
- Write docstrings for classes and functions
- Keep functions focused and modular
- Use meaningful variable names

Example:
```python
def calculate_nutrition(food_id: str, portion_g: float) -> NutritionData:
    """
    Calculate nutrition values for a given food portion.
    
    Args:
        food_id: Unique identifier for the food item
        portion_g: Portion size in grams
        
    Returns:
        NutritionData object with calculated values
    """
    # Implementation
```

### TypeScript (Frontend)

- Use functional components with hooks
- Define proper TypeScript interfaces
- Keep components small and reusable
- Use meaningful component and variable names
- Follow React best practices

Example:
```typescript
interface MealCardProps {
  meal: Meal;
  onAnalyze: (mealId: string) => void;
}

const MealCard: React.FC<MealCardProps> = ({ meal, onAnalyze }) => {
  // Implementation
};
```

## Testing Guidelines

### Backend Tests

- Write unit tests for business logic
- Write integration tests for API endpoints
- Use pytest fixtures for test data
- Aim for high test coverage

### Frontend Tests

- Test component rendering
- Test user interactions
- Test API integration
- Use React Testing Library

## Documentation

- Update README.md for significant changes
- Add inline comments for complex logic
- Update API documentation for new endpoints
- Include examples in documentation

## Commit Message Format

Use clear, descriptive commit messages:

```
type: brief description

Detailed explanation if needed

Fixes #issue_number
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat: add meal photo upload functionality

Implemented image upload with validation and storage.
Integrated with meal analysis service.

Fixes #123
```

## Review Process

1. All pull requests require review before merging
2. Address review comments promptly
3. Keep pull requests focused and reasonably sized
4. Ensure CI/CD checks pass

## Questions?

Feel free to open an issue for questions or reach out to the maintainers.

Thank you for contributing! 🎉
