# AntiGravity - Technical Debt & Issues
**Data:** 2026-01-27

This document tracks current technical debt, architectural challenges, and security issues in the AntiGravity project.

---

## 🔧 Technical Debt

### 1. No Validation on Settings
**Severity:** Medium
**Impact:** User experience, error prevention

**Description:**
- Settings dialog accepts invalid inputs (e.g., negative ports).
- No validation before saving.
- Can lead to runtime errors.

**Recommendation:**
- Add input validators (QIntValidator, QRegExpValidator).
- Validate on save and show clear error messages.
- Test connections before accepting settings.

### 2. Missing Requirements.txt
**Severity:** Low
**Impact:** Compatibility with pip users

**Description:**
- Only `pyproject.toml` and `uv.lock` provided.
- Users without `uv` need to manually extract dependencies.
- Reduces accessibility.

**Recommendation:**
- Generate `requirements.txt` from pyproject.toml.
- Include in repository.
- Document both installation methods.

### 3. No API Documentation
**Severity:** Medium
**Impact:** Developer experience

**Description:**
- No docstrings for many methods.
- No generated API documentation.
- Difficult for contributors to understand code.

**Recommendation:**
- Add comprehensive docstrings (Google/NumPy style).
- Generate docs with Sphinx.
- Include architecture diagrams.

### 4. No Performance Metrics
**Severity:** Low
**Impact:** Optimization efforts

**Description:**
- No timing data for LLM calls.
- No metrics on context assembly time.
- Can't identify bottlenecks.

**Recommendation:**
- Add performance logging.
- Track LLM response times.
- Monitor memory usage.

---

## 🧩 Architecture & Performance

### 5. No Graph Size Limits
**Severity:** Medium
**Impact:** Performance, memory usage

**Description:**
- No limits on number of nodes or connections.
- Could lead to performance degradation.
- No warnings for large graphs.

**Recommendation:**
- Profile performance with large graphs (100+ nodes).
- Add optional limits or warnings.
- Optimize rendering for large scenes.

### 6. Full Graph Refresh on Updates
**Severity:** Low
**Impact:** Performance with many nodes

**Description:**
- `refresh_visuals()` clears and rebuilds entire scene.
- Inefficient for single node updates.
- Could cause flicker or lag.

**Recommendation:**
- Implement incremental updates.
- Only refresh affected nodes/wires.
- Use dirty flags for rendering optimization.

### 7. No Lazy Loading for Large Outputs
**Severity:** Low
**Impact:** Memory usage, rendering performance

**Description:**
- Full output text stored and rendered in nodes.
- Large outputs (10k+ chars) could impact performance.
- No truncation or pagination.

**Recommendation:**
- Truncate display with "Show More" option.
- Implement virtual scrolling for large texts.
- Add output size warnings.

### 8. Tight Coupling in MainWindow ✅ RESOLVED
**Severity:** Medium  
**Impact:** Maintainability, testability  
**Status:** ✅ **Resolved** - Controller layer implemented (2026-01-28)

**Description:**
- `AntiGravityWindow` had 460+ lines with many responsibilities.
- Handled graph logic, UI updates, and worker management.
- Difficult to test and modify.

**Resolution:**
Implemented MVP (Model-View-Presenter) pattern with controller layer:

1. **GraphController** (`core/graph_controller.py`) - 220 lines
   - Manages all graph file operations (create, load, save, merge)
   - Handles dirty state tracking and file path management
   - Fully tested with 33 unit tests

2. **TabController** (`core/tab_controller.py`) - 280 lines
   - Manages tab lifecycle (create, close, activate)
   - Coordinates between tabs and graph controllers
   - Emits signals for UI synchronization
   - Fully tested with 37 unit tests

3. **Test Infrastructure**
   - Created comprehensive pytest fixtures in `tests/conftest.py`
   - 88 new tests total (70 unit tests + 18 integration tests)
   - All tests passing, 100% coverage on controller operations

**Benefits:**
- ✅ Clear separation of concerns (business logic vs UI)
- ✅ Easy to test without UI dependencies
- ✅ Reusable controllers for future features
- ✅ Foundation for incremental MainWindow refactoring

**Next Steps (Optional):**
- Integrate controllers into MainWindow incrementally
- Remove duplicated business logic from MainWindow
- Expected line reduction: 460 → ~250 lines

### 9. Limited Graph Validation
**Severity:** Medium
**Impact:** Data integrity

**Description:**
- No cycle detection (relies on DAG assumption).
- No validation of link consistency.
- Could allow invalid graph states.

**Recommendation:**
- Add cycle detection on link creation.
- Validate graph integrity on load.
- Implement graph repair/cleanup utilities.

---

## 🔒 Security & Privacy

### 10. API Keys Stored in Plain Text
**Severity:** High
**Impact:** Security

**Description:**
- API keys stored in QSettings without encryption.
- Visible in registry (Windows) or config files (Linux/macOS).
- Security risk if system is compromised.

**Recommendation:**
- Use OS keychain/credential manager.
- Encrypt sensitive settings.
- Add warning about key security.

