# AntiGravity - Current Issues and Shortcomings

**Document Version:** 1.0  
**Date:** 2026-01-08  
**Project Version:** 0.1.0 (MVP)

This document provides a comprehensive analysis of current issues, technical debt, and areas for improvement in the AntiGravity project.

---

---

## 🟢 Resolved Issues

### 1. No Undo/Redo System
**Status:** ✅ Resolved  
**Date Resolved:** Jan 2026  
**Description:** Full command pattern implemented for all graph operations (add, delete, move, link, rename, paste) with Ctrl+Z/Ctrl+Y support and configurable stack size.

### 2. ID Collision on File Merge
**Status:** ✅ Resolved  
**Date Resolved:** Jan 2026  
**Description:** Implemented ID remapping on file load/merge. New UUIDs are generated for imported nodes, and connections are correctly remapped.

### 3. No Node Selection Feedback
**Status:** ✅ Resolved  
**Date Resolved:** Jan 2026  
**Description:** Implemented prominent visual feedback (blue border and glow) for selected nodes.

### 4. Synchronous HTTP Requests
**Status:** ✅ Resolved  
**Date Resolved:** Jan 2026  
**Description:** Refactored `LLMWorker` to use `httpx` and `asyncio`. Implemented non-blocking background fetching for model lists in settings dialogs. Added full cancellation support for LLM requests.

---

## 🟡 Functional Limitations

### 4. Missing @ID Autocomplete
**Severity:** Medium  
**Impact:** User experience, discoverability

**Description:**
- Specification mentions `@` autocomplete for connected nodes
- Not implemented in current `PromptEdit` widget
- Users must manually type node IDs

**Recommendation:**
- Implement QCompleter for `@` trigger
- Show popup with connected node IDs and labels
- Update as connections change

### 5. Limited Text Editor Capabilities
**Severity:** Medium  
**Impact:** User experience for code/structured prompts

**Description:**
- Basic `QTextEdit` without syntax highlighting
- No code folding, line numbers, or advanced features
- Focus/scrolling quirks inside QGraphicsScene

**Recommendation:**
- Consider QScintilla or custom syntax highlighter
- **Implemented:** Markdown rendering for output fields using `setMarkdown()`.
- Improve focus handling in embedded widgets

### 6. No Streaming Response Display
**Severity:** Low  
**Impact:** User experience during long generations

**Description:**
- `LLMWorker` has `chunk_received` signal but it's unused
- Users see no progress during generation
- Ollama/OpenAI streaming not implemented

**Recommendation:**
- Enable streaming in API calls
- Update node output incrementally
- Add progress indicator or typing animation

### 7. No Export Functionality
**Severity:** Low  
**Impact:** Workflow integration

**Description:**
- Can only save as proprietary JSON format
- No export to Markdown, PDF, or other formats
- Difficult to share results outside the app

**Recommendation:**
- Add "Export to Markdown" feature
- Generate conversation flow diagrams
- Support copy-as-text for individual nodes

---

## 🔧 Technical Debt


### 9. Inconsistent Error Handling
**Severity:** Medium  
**Impact:** User experience, debugging

**Description:**
- Some errors show QMessageBox, others only log
- No centralized error reporting strategy
- Stack traces not always captured

**Recommendation:**
- Implement centralized error handler
- Show user-friendly messages with details in logs
- Add error reporting/telemetry option

### 10. Hard-Coded UI Constants [RESOLVED]
**Severity:** Low | **Impact:** Maintainability, Customization
**Description:** UI components had hard-coded colors, sizes, and spacing.
**Recommendation:** Centralize constants in a dedicated module.
**Status:** Fixed by creating `ui/theme.py` and refactorings all UI components.

### 11. Limited Logging Context
**Severity:** Low  
**Impact:** Debugging, monitoring

**Description:**
- Logs don't include node IDs consistently
- No request/response logging for LLM calls
- Difficult to trace issues in complex graphs

**Recommendation:**
- Add structured logging with context
- Log full prompts and responses (with privacy option)
- Include timing information for performance analysis

### 12. No Validation on Settings
**Severity:** Medium  
**Impact:** User experience, error prevention

**Description:**
- Settings dialog accepts invalid inputs (e.g., negative ports)
- No validation before saving
- Can lead to runtime errors

**Recommendation:**
- Add input validators (QIntValidator, QRegExpValidator)
- Validate on save and show clear error messages
- Test connections before accepting settings

---

## 🎨 UI/UX Issues


### 14. Wire Routing Could Be Improved
**Severity:** Low  
**Impact:** Visual clarity

**Description:**
- Bezier curves can overlap or cross awkwardly
- No automatic routing to avoid nodes
- Can be visually cluttered in dense graphs

**Recommendation:**
- Implement smarter routing algorithms
- Add wire color coding by type/status
- Consider orthogonal routing option

### 15. No Minimap or Overview
**Severity:** Low  
**Impact:** Navigation in large graphs

**Description:**
- No overview map for large graphs
- Difficult to navigate complex workflows
- No "fit to view" or "zoom to selection"

**Recommendation:**
- Add minimap widget
- Implement "Zoom to Fit" and "Zoom to Selection"
- Add breadcrumb navigation for deep graphs

### 16. Limited Node Customization
**Severity:** Low  
**Impact:** User experience, organization

**Description:**
- All nodes look similar except for status color
- No custom colors, icons, or labels
- Difficult to organize visually

**Recommendation:**
- Add node color picker
- Support custom labels/titles
- Add icon/emoji support for visual categorization

### 17. No Search/Filter Functionality
**Severity:** Medium  
**Impact:** Usability in large projects

**Description:**
- No way to search nodes by content or ID
- No filtering by status (dirty, clean, error)
- Difficult to find specific nodes in large graphs

**Recommendation:**
- Add search bar with fuzzy matching
- Implement filters (by status, model, etc.)
- Highlight matching nodes on canvas

---

## 📊 Performance Issues

### 18. No Graph Size Limits
**Severity:** Medium  
**Impact:** Performance, memory usage

**Description:**
- No limits on number of nodes or connections
- Could lead to performance degradation
- No warnings for large graphs

**Recommendation:**
- Profile performance with large graphs (100+ nodes)
- Add optional limits or warnings
- Optimize rendering for large scenes

### 19. Full Graph Refresh on Updates
**Severity:** Low  
**Impact:** Performance with many nodes

**Description:**
- `refresh_visuals()` clears and rebuilds entire scene
- Inefficient for single node updates
- Could cause flicker or lag

**Recommendation:**
- Implement incremental updates
- Only refresh affected nodes/wires
- Use dirty flags for rendering optimization

### 20. No Lazy Loading for Large Outputs
**Severity:** Low  
**Impact:** Memory usage, rendering performance

**Description:**
- Full output text stored and rendered in nodes
- Large outputs (10k+ chars) could impact performance
- No truncation or pagination

**Recommendation:**
- Truncate display with "Show More" option
- Implement virtual scrolling for large texts
- Add output size warnings

---

## 🔒 Security & Privacy

### 21. API Keys Stored in Plain Text
**Severity:** High  
**Impact:** Security

**Description:**
- API keys stored in QSettings without encryption
- Visible in registry (Windows) or config files (Linux/macOS)
- Security risk if system is compromised

**Recommendation:**
- Use OS keychain/credential manager
- Encrypt sensitive settings
- Add warning about key security

### 22. No Prompt/Response Privacy Controls
**Severity:** Medium  
**Impact:** Privacy, compliance

**Description:**
- All prompts and responses logged without filtering
- No option to disable logging of sensitive data
- Could violate privacy policies

**Recommendation:**
- Add privacy mode to disable detailed logging
- Implement prompt/response redaction
- Add clear privacy policy in settings

---

## 📦 Deployment & Distribution

### 23. No Packaging/Distribution
**Severity:** Medium  
**Impact:** User adoption, ease of installation

**Description:**
- No executable builds for Windows/macOS/Linux
- Requires Python environment setup
- Not accessible to non-technical users

**Recommendation:**
- Use PyInstaller or cx_Freeze for executables
- Create installers (NSIS for Windows, DMG for macOS)
- Publish to package repositories

### 24. No Auto-Update Mechanism
**Severity:** Low  
**Impact:** User experience, maintenance

**Description:**
- Users must manually check for updates
- No version checking or notification
- Difficult to ensure users have latest fixes

**Recommendation:**
- Implement version check on startup
- Add "Check for Updates" menu item
- Consider auto-update framework

### 25. Missing Requirements.txt
**Severity:** Low  
**Impact:** Compatibility with pip users

**Description:**
- Only `pyproject.toml` and `uv.lock` provided
- Users without `uv` need to manually extract dependencies
- Reduces accessibility

**Recommendation:**
- Generate `requirements.txt` from pyproject.toml
- Include in repository
- Document both installation methods

---

## 🧩 Architecture & Design

### 26. Tight Coupling in MainWindow
**Severity:** Medium  
**Impact:** Maintainability, testability

**Description:**
- `AntiGravityWindow` has 500+ lines with many responsibilities
- Handles graph logic, UI updates, and worker management
- Difficult to test and modify

**Recommendation:**
- Extract controller/presenter layer
- Separate graph operations from UI logic
- Implement proper MVC/MVP pattern

### 27. No Plugin/Extension System
**Severity:** Low  
**Impact:** Extensibility

**Description:**
- No way to add custom node types or providers
- Hard-coded functionality
- Limits community contributions

**Recommendation:**
- Design plugin API
- Support custom node types
- Allow third-party LLM provider plugins

### 28. Limited Graph Validation
**Severity:** Medium  
**Impact:** Data integrity

**Description:**
- No cycle detection (relies on DAG assumption)
- No validation of link consistency
- Could allow invalid graph states

**Recommendation:**
- Add cycle detection on link creation
- Validate graph integrity on load
- Implement graph repair/cleanup utilities

---

## 📝 Documentation

### 29. No API Documentation
**Severity:** Medium  
**Impact:** Developer experience

**Description:**
- No docstrings for many methods
- No generated API documentation
- Difficult for contributors to understand code

**Recommendation:**
- Add comprehensive docstrings (Google/NumPy style)
- Generate docs with Sphinx
- Include architecture diagrams

### 30. No User Manual
**Severity:** Medium  
**Impact:** User onboarding

**Description:**
- README is developer-focused
- No step-by-step tutorials
- No video demonstrations

**Recommendation:**
- Create user manual with screenshots
- Add in-app help/tutorial
- Record demo videos

### 31. No Changelog
**Severity:** Low  
**Impact:** Communication, transparency

**Description:**
- No CHANGELOG.md file
- Users don't know what changed between versions
- Difficult to track feature additions

**Recommendation:**
- Create CHANGELOG.md following Keep a Changelog format
- Update with each release
- Include migration notes for breaking changes

---

## 🎯 Feature Gaps vs. Specification

### 32. Incomplete Dirty State Visualization
**Severity:** Low  
**Impact:** User awareness

**Description:**
- Specification mentions "Parent Dirty" warning in child nodes
- Currently only shows yellow border on dirty nodes
- Could be more informative

**Recommendation:**
- Add "Parent Dirty" badge/text as per spec
- Show which parent is dirty
- Add tooltip with dirty state explanation

### 33. Token Meter Not Fully Implemented
**Severity:** Low  
**Impact:** User awareness of context usage

**Description:**
- Token meter exists but may not accurately reflect all context
- Doesn't turn red when exceeding limits (per spec)
- No visual warning for truncation

**Recommendation:**
- Implement color-coded meter (green/yellow/red)
- Show truncation warnings
- Display detailed breakdown on hover

### 34. No Input Stack Labels
**Severity:** Low  
**Impact:** User experience

**Description:**
- Specification shows labeled inputs like `[A1]`, `[B2]`
- Current implementation shows ports but not labels
- Harder to identify connections

**Recommendation:**
- Display source node ID next to input ports
- Update labels when connections change
- Add tooltips with full node info

---

## 🔄 Workflow Issues

### 35. No Batch Operations
**Severity:** Low  
**Impact:** Efficiency for large workflows

**Description:**
- Can't run multiple nodes in sequence
- No "Run All Dirty" or "Run Downstream" options
- Manual execution only

**Recommendation:**
- Add "Run All Dirty Nodes" action
- Implement "Run Downstream from Selection"
- Add execution queue with progress tracking

### 36. No Node Templates
**Severity:** Low  
**Impact:** Productivity

**Description:**
- Every node starts with default config
- No way to save/load node templates
- Repetitive setup for similar nodes

**Recommendation:**
- Add node template system
- Allow saving custom templates
- Include common templates (summarize, translate, etc.)

### 37. Limited Copy/Paste Functionality
**Severity:** Low  
**Impact:** Workflow efficiency

**Description:**
- Copy/paste works but doesn't preserve connections
- Can't paste between different graph files
- No "paste as reference" option

**Recommendation:**
- Preserve internal connections on paste
- Support cross-file paste
- Add "paste as reference" to link to original

---

## 📈 Monitoring & Observability

### 38. No Usage Analytics
**Severity:** Low  
**Impact:** Product improvement

**Description:**
- No telemetry or usage data
- Don't know which features are used
- Can't prioritize improvements based on data

**Recommendation:**
- Add optional anonymous analytics
- Track feature usage, errors, performance
- Respect user privacy with opt-in

### 39. No Performance Metrics
**Severity:** Low  
**Impact:** Optimization efforts

**Description:**
- No timing data for LLM calls
- No metrics on context assembly time
- Can't identify bottlenecks

**Recommendation:**
- Add performance logging
- Track LLM response times
- Monitor memory usage

---

## 🎓 Learning Curve

### 40. No Onboarding Flow
**Severity:** Medium  
**Impact:** User adoption

**Description:**
- New users dropped into empty canvas
- No tutorial or sample project
- Steep learning curve for DAG concept

**Recommendation:**
- Add first-run tutorial
- Include sample projects
- Add interactive tooltips for first-time users

### 41. No Contextual Help
**Severity:** Low  
**Impact:** User experience

**Description:**
- No tooltips on many UI elements
- No "What's This?" help mode
- Users must refer to external docs

**Recommendation:**
- Add comprehensive tooltips
- Implement Qt "What's This?" help
- Add help links in context menus

---

## Summary Statistics

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| Critical Issues | 0 | 1 | 0 | 0 | 1 |
| Functional Limitations | 0 | 0 | 3 | 4 | 7 |
| Technical Debt | 0 | 0 | 2 | 3 | 5 |
| UI/UX Issues | 0 | 0 | 2 | 3 | 5 |
| Performance | 0 | 0 | 1 | 2 | 3 |
| Security & Privacy | 0 | 1 | 1 | 0 | 2 |
| Deployment | 0 | 0 | 1 | 2 | 3 |
| Architecture | 0 | 0 | 2 | 1 | 3 |
| Documentation | 0 | 0 | 2 | 1 | 3 |
| Feature Gaps | 0 | 0 | 0 | 3 | 3 |
| Workflow | 0 | 0 | 0 | 3 | 3 |
| Monitoring | 0 | 0 | 0 | 2 | 2 |
| Learning Curve | 0 | 0 | 1 | 1 | 2 |
| **TOTAL** | **0** | **2** | **15** | **25** | **42** |

## Prioritization Recommendations

### Immediate (Next Sprint)
1. API Keys Encryption (#21)
2. Automated Testing Framework (#1)
3. Settings Validation (#12)

### Short-term (Next Month)
4. @ID Autocomplete (#4)
5. Search/Filter Functionality (#17)
6. Error Handling Improvements (#9)
7. User Manual (#30)

### Medium-term (Next Quarter)
10. Streaming Response Display (#6)
11. Export Functionality (#7)
12. Packaging/Distribution (#23)
13. Plugin System (#27)
14. Batch Operations (#35)

### Long-term (Future Releases)
15. Advanced Text Editor (#5)
16. Performance Optimizations (#18, #19, #20)
18. UI Enhancements (#13-16)
19. Analytics & Monitoring (#38, #39)

---

**Note:** This document should be reviewed and updated regularly as issues are resolved and new ones are discovered.
