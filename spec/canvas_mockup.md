I have generated a scalable Vector Graphic (SVG) mockup that represents the UX described in your specification.

### **Visual Walkthrough**

1.  **Node A1 (The Parent):**
    *   **Status:** "Clean" (Green Dot).
    *   **State:** Execution complete. Shows the Model used (`Ollama: Llama3`).
    *   **Ports:** Shows the Single Output port on the right.

2.  **Node B2 (The Child):**
    *   **Status:** "Dirty" (Yellow Border & Dot). This indicates that A1 was edited, but B2 hasn't been re-run yet.
    *   **Input Stack:**
        *   **Active Input:** Shows `[A1]` connected.
        *   **Placeholder:** The `+` port at the bottom, waiting for a new drag-and-drop connection.
    *   **Token Meter:** Shows the estimated usage (History + Current Prompt).
    *   **Prompt:** Demonstrates the explicit referencing syntax: *"Based on the summary in @A1..."*

3.  **The Canvas:**
    *   Dark mode aesthetic (standard for node editors).
    *   Bezier curve connection (Wire).
    *   Grid background for spatial reference.

### **The Mockup**

You can view the design below.

```svg
<svg width="1000" height="600" viewBox="0 0 1000 600" xmlns="http://www.w3.org/2000/svg">
  <!-- CSS Styles for UI Elements -->
  <style>
    .font-ui { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    .node-bg { fill: #2b2b2b; }
    .header-clean { fill: #383838; }
    .header-dirty { fill: #4d4418; }
    .border-clean { stroke: #555; stroke-width: 1px; }
    .border-dirty { stroke: #e6c60d; stroke-width: 2px; stroke-dasharray: 5, 5; }
    .text-white { fill: #e0e0e0; font-size: 14px; }
    .text-dim { fill: #aaaaaa; font-size: 12px; }
    .text-code { font-family: Consolas, monospace; fill: #ce9178; font-size: 13px; }
    .port { fill: #777; stroke: #333; stroke-width: 1px; }
    .port-hover { fill: #fff; }
    .wire { fill: none; stroke: #888; stroke-width: 2px; }
    .grid { stroke: #333; stroke-width: 1px; }
    .btn-run { fill: #2d5a37; rx: 4; }
    .btn-text { fill: #fff; font-size: 12px; font-weight: bold; text-anchor: middle; }
    .input-box { fill: #1e1e1e; stroke: #444; }
    .token-bar-bg { fill: #111; }
    .token-bar-fill { fill: #2d8a4e; }
  </style>

  <!-- Background Grid -->
  <defs>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" class="grid" opacity="0.2"/>
    </pattern>
  </defs>
  <rect width="100%" height="100%" fill="#161616"/>
  <rect width="100%" height="100%" fill="url(#grid)" />

  <!-- Wire Connection (A1 Output -> B2 Input) -->
  <!-- Bezier Curve calculation: Start(350, 160) Control1(475, 160) Control2(425, 230) End(550, 230) -->
  <path d="M 350 160 C 475 160, 425 230, 550 230" class="wire" />

  <!-- NODE A1 (Parent - Clean State) -->
  <g transform="translate(50, 80)">
    <!-- Main Body -->
    <rect x="0" y="0" width="300" height="280" rx="6" class="node-bg border-clean" />
    
    <!-- Header -->
    <path d="M 0 6 Q 0 0 6 0 L 294 0 Q 300 0 300 6 L 300 30 L 0 30 Z" class="header-clean" />
    <circle cx="15" cy="15" r="5" fill="#4caf50" /> <!-- Green Status Dot -->
    <text x="30" y="20" class="font-ui text-white" font-weight="bold">A1</text>
    <text x="290" y="20" class="font-ui text-dim" text-anchor="end">Ollama: Llama3</text>

    <!-- Inputs Column (Left) -->
    <!-- Placeholder Input -->
    <rect x="-6" y="50" width="12" height="12" class="port" />
    <text x="-15" y="60" class="font-ui text-dim" text-anchor="end" font-size="16">+</text>

    <!-- Output Port (Right) -->
    <rect x="294" y="80" width="12" height="12" class="port" />
    <text x="315" y="90" class="font-ui text-dim">Out</text>

    <!-- Content Area -->
    <text x="15" y="60" class="font-ui text-dim">Trace Depth: 0 (None)</text>
    
    <!-- Prompt Box -->
    <rect x="10" y="70" width="280" height="60" rx="2" class="input-box" />
    <text x="20" y="95" class="font-ui text-white">System: Summarize the</text>
    <text x="20" y="115" class="font-ui text-white">attached logs.</text>

    <!-- Output Box -->
    <rect x="10" y="140" width="280" height="90" rx="2" fill="#111" />
    <text x="20" y="165" class="font-ui text-dim">Output (Cached):</text>
    <text x="20" y="185" class="font-ui text-white">The logs indicate a failure</text>
    <text x="20" y="205" class="font-ui text-white">in the database shard...</text>
    <text x="20" y="225" class="font-ui text-dim">[...400 words...]</text>

    <!-- Footer -->
    <rect x="10" y="240" width="80" height="25" class="btn-run" opacity="0.5" />
    <text x="50" y="257" class="font-ui btn-text">RUN</text>
    
    <text x="290" y="257" class="font-ui text-dim" text-anchor="end">Tokens: 450</text>
  </g>

  <!-- NODE B2 (Child - Dirty State) -->
  <g transform="translate(550, 150)">
    <!-- Dirty Border Glow -->
    <rect x="-2" y="-2" width="304" height="324" rx="8" fill="none" class="border-dirty" />
    
    <!-- Main Body -->
    <rect x="0" y="0" width="300" height="320" rx="6" class="node-bg" />
    
    <!-- Header -->
    <path d="M 0 6 Q 0 0 6 0 L 294 0 Q 300 0 300 6 L 300 30 L 0 30 Z" class="header-dirty" />
    <circle cx="15" cy="15" r="5" fill="#e6c60d" /> <!-- Yellow Status Dot -->
    <text x="30" y="20" class="font-ui text-white" font-weight="bold">B2</text>
    <text x="290" y="20" class="font-ui text-dim" text-anchor="end">OpenAI: GPT-4o</text>

    <!-- Inputs Column (Left) -->
    <!-- Input 1 (Connected to A1) -->
    <rect x="-6" y="80" width="12" height="12" fill="#fff" stroke="#888" /> <!-- Connected -->
    <text x="10" y="90" class="font-ui text-code" font-weight="bold">[A1]</text>
    
    <!-- Placeholder Input (Shifted Down) -->
    <rect x="-6" y="110" width="12" height="12" class="port" />
    <text x="-15" y="120" class="font-ui text-dim" text-anchor="end" font-size="16">+</text>

    <!-- Output Port (Right) -->
    <rect x="294" y="80" width="12" height="12" class="port" />

    <!-- Content Area -->
    <text x="15" y="60" class="font-ui text-dim">Trace Depth: 1 (Inherit A1)</text>
    
    <!-- Prompt Box -->
    <rect x="10" y="130" width="280" height="80" rx="2" class="input-box" />
    <text x="20" y="155" class="font-ui text-white">Based on the summary</text>
    <text x="20" y="175" class="font-ui text-white">in <tspan class="text-code">@A1</tspan>, identify the</text>
    <text x="20" y="195" class="font-ui text-white">root cause.</text>

    <!-- Token Meter (Visual) -->
    <text x="15" y="230" class="font-ui text-dim">Context Payload:</text>
    <rect x="110" y="220" width="100" height="10" rx="2" class="token-bar-bg" />
    <rect x="110" y="220" width="60" height="10" rx="2" class="token-bar-fill" /> <!-- 60% full -->
    <text x="220" y="230" class="font-ui text-dim">8.5k / 16k</text>

    <!-- Output Box (Empty/Stale) -->
    <rect x="10" y="245" width="280" height="30" rx="2" fill="#111" />
    <text x="150" y="265" class="font-ui text-dim" text-anchor="middle" font-style="italic">Waiting to Run...</text>

    <!-- Footer -->
    <rect x="10" y="285" width="80" height="25" class="btn-run" />
    <text x="50" y="302" class="font-ui btn-text">RUN</text>
    
    <!-- Warning Text -->
    <text x="290" y="302" class="font-ui" fill="#e6c60d" font-size="11px" text-anchor="end">Parent Dirty</text>
  </g>

</svg>
```