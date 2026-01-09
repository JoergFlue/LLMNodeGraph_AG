# **Project Specification: Branching LLM Logic Engine (Desktop MVP)**
**Version:** 2.0 (Revised)  
**Stack:** Python 3.10+, PySide6 (Qt), JSON (Persistence)  
**Type:** Standalone Desktop Application

## **1. Executive Summary**
A local-first desktop application for non-linear LLM interactions. It allows users to structure conversations as a **Directed Acyclic Graph (DAG)**.
**Key Constraints for MVP:**
1.  **Direct Linking:** Context references are strictly limited to physically connected nodes.
2.  **Token Safety:** Strict limits prevent context explosion.
3.  **Passive State:** "Dirty" flags are informational only and do not block execution.

---

## **2. Architecture: Modular MVC**

### **Module A: UX / View**
*   **Canvas:** `QGraphicsScene` with Pan/Zoom.
*   **Node Items:**
    *   **Input Stack (Left):** Dynamic list of connected inputs (Labeled `[ID]`).
    *   **Output Port (Right):** Single source for downstream nodes.
    *   **Controls:** Trace Depth Slider, **Max Token Override Input** (New).
    *   **Prompt Editor:** `QTextEdit` overlay.
        *   *Autocomplete:* Typing `@` triggers a popup listing **only** the IDs of nodes currently connected to the Input Stack.
*   **Status Indicators:**
    *   **Dirty:** Yellow border (Informational).
    *   **Token Warning:** Token meter turns Red if calculated context > Max Limit.

### **Module B: Data / Model**
*   **Graph State:** List of Nodes and Links.
*   **Node Model:**
    *   `id`: UUID (Internal) / ShortString (Display, e.g., "A1").
    *   `config`: { `model`: "gpt-4o", `max_tokens`: 16000, `trace_depth`: 2 }.
    *   `cached_output`: The last generated string from this node.
    *   `is_dirty`: Boolean.

### **Module C: Core Logic (The Brain)**
*   **Context Assembler (Strict Mode):**
    1.  **Gather:** Fetch text from the Primary Parent up to `Trace Depth`.
    2.  **Resolve References:** Parse `@ID`. **Constraint:** If `@A1` is in the prompt, Node A1 *must* be in the `inputs` list. If not, ignore or warn.
    3.  **Merge:** Concatenate (History + Referenced Inputs + Current Prompt).
    4.  **Guard (Token Limiter):**
        *   Check `len(text) / 4`.
        *   If Total > `Node.max_tokens` (or Global Default):
            *   **Truncate:** Keep the Current Prompt + References. Truncate the *oldest* history from the Primary Parent path until it fits.
            *   *Log:* Add a warning to the output metadata "Context truncated by X tokens."
*   **Dirty Propagation:**
    *   When Node A changes: Mark A and all children as `is_dirty = True`.
    *   **Execution Rule:** When "Run" is clicked on a Dirty node, execute immediately using the **Cached Output** of parents. Do not force re-runs of parents.

### **Module D: Services**
*   **Worker Thread:**
    *   Handles synchronous calls to LLM APIs (Ollama/OpenAI) on a background thread to prevent GUI freezing.
    *   Emits signals: `started`, `chunk_received`, `finished`, `error`.

---

## **3. Functional Workflows**

### **3.1 Connection & Referencing (The "Physical" Constraint)**
*   **Global references are banned.** You cannot reference `@A1` unless you have drawn a wire from A1 to the current node.
*   **Workflow:**
    1.  User creates Node B.
    2.  User wants to use context from Node A.
    3.  User drags wire: `Node A (Output)` -> `Node B (Placeholder Input)`.
    4.  Node B creates input port `[A1]`.
    5.  User types: "Summarize the text from @A1".
    6.  **Logic:** The system looks at Node B's connections, finds the link to A1, and injects `A1.cached_output`.

### **3.2 Context Safety Strategy**
*   **Global Setting:** "Default Max Input Tokens" (Default: 16,384).
*   **Per-Node Override:** User can set Node C to 4,096 or 128,000.
*   **The Guard Rail:**
    *   Before sending the request, the `Assembler` calculates the budget.
    *   **Priority Queue for Context:**
        1.  System Prompt (Always Keep)
        2.  Current User Prompt (Always Keep)
        3.  Explicit `@ID` References (Always Keep)
        4.  Inherited History (Trace Depth) -> **Drop these first** (Oldest to Newest) if budget is exceeded.

### **3.3 The "Passive Dirty" State**
*   **Scenario:** Node A (Parent) -> Node B (Child).
*   User edits Node A's prompt. Node A and Node B turn Yellow (Dirty).
*   User clicks "Run" on **Node B** (skipping Node A).
*   **System Action:**
    *   The system uses the **existing/stale** `cached_output` of Node A.
    *   It generates a new response for Node B.
    *   Node B turns Green (Clean). Node A remains Yellow (Dirty).
*   *Rationale:* This allows for rapid iteration on downstream nodes without paying (time/money) to re-generate the whole chain every time.

---

## **4. Data Persistence (JSON)**

Schema updated with token limits.

```json
{
  "version": "2.0",
  "app_settings": {
    "global_token_limit": 16384
  },
  "nodes": [
    {
      "id": "B2",
      "type": "LLM_Node",
      "pos": [400, 300],
      "inputs": [
        {"name": "Input_0", "link": 1, "label": "A1"}
      ],
      "properties": {
        "model": "gpt-4o",
        "max_tokens": 32000,  // Override
        "trace_depth": 3
      },
      "widgets_values": [
        "Refine the logic in @A1",  // Prompt
        "Resulting text..."         // Cached Output
      ]
    }
  ]
}
```

---

## **5. Acknowledged Limitations (MVP Scope)**

The following issues are known and accepted for the initial release:
1.  **Text Editor:** Standard `QTextEdit` will be used. No code syntax highlighting. Focus/Scrolling quirks inside the Canvas are expected.
2.  **Concurrency:** `requests` (Sync) inside `QThread` will be used instead of complex `asyncio` bridging.
3.  **Data Safety:** No Undo/Redo system.
4.  **ID Collisions:** Merging two JSON files with identical Short IDs (e.g., both have "A1") will not be supported in MVP.

---

## **6. Implementation Steps**

1.  **Scaffold:** PySide6 Window + GraphicsScene.
2.  **Node UI:** Implement the Input Stack and Placeholder Port logic.
3.  **Graph Logic:** Implement `Assembler` with the **Direct-Link check** and **Token truncation**.
4.  **Service:** Connect `worker.py` to Ollama (via `requests`).
5.  **Settings:** Add "Global Token Limit" field.
6.  **Persistence:** JSON Save/Load.