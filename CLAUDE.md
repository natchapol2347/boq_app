# CLAUDE.md - Woodman BOQ App Coding Guide

## Environment Setup
- Install dependencies: `poetry install` or `pip install -r requirements.txt`
- Run the application: `python main.py`

## Development Workflow
- Format code: `poetry run black .` or `black .`
- Linting: `poetry run flake8` or `flake8`
- Type checking: `poetry run mypy main.py` or `mypy main.py`
- Run tests: `poetry run pytest` or `pytest`
- Run a specific test: `poetry run pytest tests/test_file.py::test_function`

## Code Style Guidelines
- Line length: 88 characters (Black default)
- Python target: 3.9+
- Strict type annotations required
- Follow Black formatting conventions
- Use f-strings for string formatting
- Imports order: standard library, third-party, local application
- Error handling: Use try/except with specific exceptions
- Prefer explicit error messages with logging

## Project Structure
- `main.py`: Core application logic
- `master_data/`: Contains Excel master data files
- `samples/`: Example files for testing
- `uploads/`: Temporary storage for uploaded files
- `output/`: Generated output files

## Project Business Logic
The application automates Bill of Quantities (BOQ) cost calculations for interior construction projects:

1. **Master Data Structure**:
   - Contains supplies with their costs in the master.xlsx file
   - Primary key for each item is the "name" column
   - Sub-items are rows without product codes, typically additional services tied to a supply

2. **Business Need**:
   - Cross-match a blank BOQ (with same format as master data) with master data
   - Fill up costs of each matched item in the blank BOQ
   - Apply markups using percentages defined in self.markup_rates
   - First sheet is summary of costs
   - Each subsequent sheet represents different domains (interior work, electricity, computer room, etc.)

3. **Current Bug**:
   - Final processed BOQ shows zeros despite database being properly populated
   - Debug issues with cost data transfer from database to Excel output

4. **Development Priority**:
   - First ensure backend is tested and flawless in execution
   - Proceed to frontend development only after backend issues are resolved

5. **To run for test**:
   curl -X POST -F "file=@uploads/Blank BOQ AIS ASP Zeer รังสิต-1.xlsx" http://localhost:5000/api/process-boq
   curl -X POST -H "Content-Type: application/json" -d '{"session_id": "YOUR_SESSION_ID"}' http://localhost:5000/api/generate-final-boq
