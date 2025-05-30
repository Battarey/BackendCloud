# Description of the tests folder

The `tests` folder contains autotests for checking the API and business logic of the BattareyCloud backend. `pytest` with asynchrony support (`pytest-asyncio`) and the HTTP client `httpx` are used.

## Test structure and purpose
- **integration_tests/** — API integration tests (registration, login, files, folders, cart, sessions, logs, settings, search, preview, etc.)
- **unit_tests/** — unit tests (as needed, template for extension)
- **load_tests/** — load tests using Locust (see below)

## Coverage and CI
- The main API scenarios are covered by integration tests
- For new features, add separate test files similar to existing ones
- It is recommended to run tests on CI (GitHub Actions, GitLab CI, etc.)

## Running integration tests
- SQLite (fast, for CI):
1. In .env:
```
TEST_USE_SQLITE=1
TEST_DATABASE_URL=sqlite+aiosqlite:///./test.db
```
2. Run:
```powershell
pytest BackEnd/tests/integration_tests/
```
- PostgreSQL (default):
- If TEST_USE_SQLITE is not set, tests use PostgreSQL from DATABASE_URL

## Load testing (Locust)
- Install:
```powershell
pip install locust
```
- Run:
```powershell
docker-compose run --rm backend locust -f /app/tests/load_tests/locustfile.py --host=http://backend:8000
```
- Open http://localhost:8089 to manage load

## Sample tests
- Sample tests can be found in the `integration_tests/` folder. Each test file contains a docstring describing the scenarios.
- To test new endpoints, use fixtures from conftest.py (user creation, login, file/folder preparation).

---