# Testing & Error Boundary Architecture

**Project**: Performance-Safe Rightsizing Simulator  
**Reference**: `DOC-TEST-RESILIENCE-2026`  
**Scope**: Unit Testing Strategies, Test Coverage, Frontend Error Boundaries & Backend Exception Resilience  

---

## 1. Unit Testing Architecture

The Rightsizing Simulator utilizes **Pytest** for backend analytical verification and test-driven validation of ML algorithms, scaling formulas, and multi-scenario experiments.

### 1.1 Test Philosophy & Verification Dimensions
1. **Mathematical Invariant Verification**: Rightsizing decisions must conform to strict physical and operational constraints:
   - Scaling ratios $S_{cpu} = \frac{vCPU_{target}}{vCPU_{current}}$ must be strictly positive.
   - Percentile estimations ($P_{50}, P_{90}, P_{95}, P_{99}$) must satisfy monotonic ordering: $P_{50} \le P_{90} \le P_{95} \le P_{99}$.
   - Calculated risk scores must be clamped to the range $[0.0, 100.0]$.
2. **Deterministic Trend Modeling**: Scikit-Learn Ordinary Least Squares (OLS) linear regression must reliably classify directional momentum (`stable`, `increasing`, `decreasing`) and compute the coefficient of determination ($R^2$).
3. **Multi-Objective Composite Scoring**: Experiments must accurately balance monthly financial savings against risk scores according to configured preference weights ($w_{savings}$). Overly aggressive downscaling (e.g. 75% savings with 98% P99 CPU saturation) must be penalized below safe, moderate alternatives.
4. **Boundary & Edge-Case Protection**:
   - Zero-length metric arrays must yield graceful default values rather than dividing by zero or raising uncaught runtime exceptions.
   - Telemetry outliers and noise must be clamped to valid hardware envelopes.

---

### 1.2 Test Suite Structure (`backend/tests/`)

```
backend/tests/
├── conftest.py                       # Global test fixtures & database session mocks
├── test_rightsizing_engine.py        # ML scaling, OLS trend regression, and risk scoring
├── test_experiment_engine.py         # Multi-scenario A/B ranking & composite scores
└── test_event_injection.py           # Out-of-order, delayed, and duplicate telemetry events
```

#### Test Suite Inventory & Coverage:

| Test Identifier | Test Function | Target Service | Purpose / Assertion |
| :--- | :--- | :--- | :--- |
| `TC-RS-001` | `test_percentile_safe_empty_and_valid` | `rightsizing_engine` | Asserts graceful fallback ($0.0$) on empty arrays and exact percentile accuracy on valid inputs. |
| `TC-RS-002` | `test_pct_above_threshold` | `rightsizing_engine` | Validates frequency estimation of data points exceeding safety thresholds. |
| `TC-RS-003` | `test_risk_score_and_classification_boundaries` | `rightsizing_engine` | Verifies risk formula bounds and exact four-tier classification (`low`, `medium`, `high`, `critical`). |
| `TC-RS-004` | `test_linear_regression_trend_detection` | `rightsizing_engine` | Verifies Scikit-Learn linear regression fit, slope per hour, and $R^2$ goodness-of-fit. |
| `TC-RS-005` | `test_resource_scaling_and_projection` | `rightsizing_engine` | Validates instance hardware capacity ratios and projected utilization time series. |
| `TC-RS-006` | `test_full_rightsizing_simulation_run` | `rightsizing_engine` | End-to-end simulation execution verifying cost savings, ROI months, and recommendation verdicts. |
| `TC-EXP-001` | `test_composite_score_weighting` | `experiment_engine` | Validates that composite scoring penalizes dangerous downscaling even when financial savings are high. |
| `TC-EXP-002` | `test_verdict_mapping` | `experiment_engine` | Verifies operational verdict strings corresponding to four risk tiers. |
| `TC-EXP-003` | `test_multi_scenario_experiment_execution` | `experiment_engine` | Runs multi-scenario comparison and validates candidate ranking and summary generation. |
| `TC-EVT-001` | `test_delayed_events_handling` | `event_recovery` | Verifies timestamp parsing and validation for historical delayed telemetry ingestion. |
| `TC-EVT-002` | `test_duplicate_event_handling` | `event_recovery` | Asserts deduplication logic across repeated event payloads. |
| `TC-EVT-003` | `test_out_of_order_events` | `event_recovery` | Verifies temporal sorting of out-of-order telemetry streams. |

---

### 1.3 How to Run the Unit Tests

Execute Pytest from the `backend/` directory:

```bash
# Navigate to backend
cd backend

# Run all unit tests with verbose output
python -m pytest -v

# Run a specific test suite
python -m pytest -v tests/test_rightsizing_engine.py

# Run with test coverage report
python -m pytest --cov=app tests/
```

**Verified Test Execution Output**:
```
============================= test session starts =============================
platform win32 -- Python 3.9.11, pytest-8.4.2, pluggy-1.6.0
rootdir: C:\Users\apsar\OneDrive\Desktop\ralle project\rightsizing-simulator\backend
configfile: pytest.ini
collected 9 items

tests/test_rightsizing_engine.py::test_percentile_safe_empty_and_valid PASSED [ 11%]
tests/test_rightsizing_engine.py::test_pct_above_threshold PASSED        [ 22%]
tests/test_rightsizing_engine.py::test_risk_score_and_classification_boundaries PASSED [ 33%]
tests/test_rightsizing_engine.py::test_linear_regression_trend_detection PASSED [ 44%]
tests/test_rightsizing_engine.py::test_resource_scaling_and_projection PASSED [ 55%]
tests/test_rightsizing_engine.py::test_full_rightsizing_simulation_run PASSED [ 66%]
tests/test_experiment_engine.py::test_composite_score_weighting PASSED   [ 77%]
tests/test_experiment_engine.py::test_verdict_mapping PASSED             [ 88%]
tests/test_experiment_engine.py::test_multi_scenario_experiment_execution PASSED [100%]

======================== 9 passed, 8 warnings in 1.54s ========================
```

---

## 2. Frontend Error Boundary Architecture

### 2.1 Problem & Motivation
In complex client-side Single Page Applications featuring interactive SVG/Canvas charts (Chart.js), nested sliders, and asynchronous API calls, unexpected runtime exceptions (such as undefined telemetry values, chart rendering race conditions, or corrupted local storage keys) can trigger React unmount cascading. Without an error boundary, a minor error in a single component unmounts the entire React component tree, leaving the user with a blank white screen.

### 2.2 Component Implementation (`frontend/src/components/ErrorBoundary.tsx`)
The simulator implements an enterprise **React Error Boundary** utilizing class component lifecycle methods:

```tsx
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  // 1. Static lifecycle hook updates state so the next render shows the fallback UI
  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error }
  }

  // 2. Lifecycle hook captures stack trace and logs diagnostic telemetry
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('[ErrorBoundary caught exception]:', error, errorInfo)
    this.setState({ errorInfo })
  }

  // 3. User-triggered recovery resets error state and reloads the application
  handleReset = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    window.location.reload()
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="error-boundary-card">
          <h2>Application Error Encountered</h2>
          <p>A client-side runtime exception was intercepted by the Error Boundary.</p>
          <pre>{this.state.error?.message}</pre>
          <button onClick={this.handleReset}>↺ Reload Application</button>
        </div>
      )
    }
    return this.props.children
  }
}
```

### 2.3 Component Tree Mounting
The `ErrorBoundary` is mounted at the root of the application in `frontend/src/App.tsx`, wrapping the `BrowserRouter`, `AuthProvider`, and all application routes:

```tsx
export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            {/* Protected Routes */}
            <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route index element={<Dashboard />} />
              <Route path="upload" element={<UploadData />} />
              <Route path="simulator" element={<Simulator />} />
              <Route path="experiments" element={<Experiments />} />
              <Route path="reports" element={<Reports />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  )
}
```

---

## 3. Backend Exception Resilience & Error Boundaries

### 3.1 Global Exception Handlers (`backend/app/main.py`)
To prevent raw Python tracebacks, database connection strings, or internal file paths from leaking to HTTP clients, the backend implements three-tier global error boundaries:

```python
# 1. Standard HTTP Exception Boundary (4xx / 5xx)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": exc.detail,
            "path": request.url.path,
        },
    )

# 2. Pydantic Request Validation Error Boundary (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "status_code": 422,
            "message": "Input validation error in request body or query parameters",
            "details": exc.errors(),
            "path": request.url.path,
        },
    )

# 3. Unhandled System Exception Catch-All (500)
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "status_code": 500,
            "message": "An unexpected internal server error occurred. The incident has been logged.",
            "path": request.url.path,
        },
    )
```

### 3.2 Transactional Rollback Guards
All database writes within route handlers and services operate inside asynchronous context managers (`async with db.begin():`). If an unhandled exception occurs at any point during a multi-row insertion (e.g. during a chunked CSV telemetry upload), the database session automatically issues an atomic `ROLLBACK`. This prevents partial writes and database inconsistency.
