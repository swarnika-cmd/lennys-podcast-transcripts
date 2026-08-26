# User Interface & Design Specification: Obsidian Console

This document outlines the UI/UX principles, design decisions, information architecture, and key interaction states for **The Lenny Growth Assistant Console**.

---

## 1. Core UX/UI Principles

Instead of generic glassmorphic or boilerplate material templates, the Lenny Growth Assistant is designed using a **Cyber-Minimalist Obsidian Console** aesthetic. This design mimics professional high-performance developer tools (like Linear, Cursor, or Vercel CLI) which prioritize text readability, utility density, and functional styling.

*   **Low Cognitive Overhead:** Eliminates unnecessary decorations, gradients, and shadows. Panels are separated by clean, single-pixel borders.
*   **Aesthetic Tone:** Dark obsidian backgrounds combined with high-contrast cyber-cyan highlights and code-friendly monospaced metadata labels.
*   **Utility Density:** Information is packed cleanly. Clear status lights indicate database connectivity, and citations are rendered as compact developer pills.

---

## 2. Information Architecture & Layout

The app is built as a responsive three-panel viewport layout:

```
+-------------------------------------------------------------------------+
|  SIDEBAR           |  ACTIVE CHAT PANEL              |  SLIDING         |
|  [Brand Icon]      |  [Active Session Title]  [Mode] |  ARTIFACT        |
|  [Status Indicator]|  +----------------------------+ |  PANEL           |
|  [New Terminal Btn]|  | Assistant bubble           | |  [Title & Label|
|                    |  | "Grounded transcript text" | |  [Tab Switcher]|
|  [Sessions List]   |  +----------------------------+ |  +-------------+|
|  - Session A       |  | User bubble                | |  |             ||
|  - Session B       |  | "How does PLG work?"       | |  |   Iframe    ||
|                    |  +----------------------------+ |  |  Sandboxed  ||
|                    |  | Input panel                | |  |   Preview   ||
|  [Provider Select] |  | [Type query...           ] | |  +-------------+|
+-------------------------------------------------------------------------+
```

1.  **Left Sidebar (280px):** Handles configuration, active database connection checks, starting new conversational instances ("terminals"), and swapping between conversational history.
2.  **Central Chat Panel (Flexible):** Holds the main dialogue thread, bubble structures, citations list, and RAG/Essay mode switches.
3.  **Right Sliding Panel (600px - Collapse/Expand):** Renders the code/previews of dynamically generated HTML or Markdown artifacts.

---

## 3. Design Tokens & Color Palette

The interface uses standard custom HSL design tokens to maintain visual cohesion:

| Variable | HEX Code | Purpose |
| :--- | :--- | :--- |
| `--bg-obsidian` | `#090b0e` | Master background, deepest black |
| `--bg-slate` | `#11141b` | Main container and panel backgrounds |
| `--bg-input` | `#181d28` | Lighter slate highlight for textareas and active items |
| `--border-color` | `#222a36` | Subtle gray-blue borders separating panels |
| `--accent-cyan` | `#00e5ff` | Primary interaction accent, highlights, focus indicators |
| `--accent-emerald`| `#00e676` | Blinking status indicator for active DB connectivity |
| `--accent-rose` | `#ff1744` | Status indicator for database error or offline state |
| `--text-primary` | `#e3e6eb` | Main body text |
| `--text-secondary`| `#8b949e` | Sub-labels, dates, metadata, and system prompts |

---

## 4. Key Interaction States

*   **Status Connection Indicator:** The status panel in the sidebar queries `/health` every 10 seconds.
    *   *ONLINE:* Green blinking dot (`#00e676`) with a subtle pulse animation.
    *   *OFFLINE / ERROR:* Solid red dot (`#ff1744`).
*   **Loading State (Grounded Router):** When a query is sent, the input is locked and a monospaced cyan notification shows `SEARCHING VECTOR EMBEDDINGS & RUNNING COGNITIVE ROUTER...`. This provides immediate system response feedback while local models generate embeddings.
*   **Artifact Injection & Slide-Out:**
    *   If the assistant generates an HTML/Markdown code block, the JS extraction regex catches it and appends a `Render HTML Page` or `Preview Document` pill below the bubble.
    *   Clicking it slides open the Artifact Viewer panel from the right. The panel contains two tabs: **Preview** (live rendering) and **Code** (raw source view).
*   **Form Focus Indicators:** Textareas and dropdown inputs glow slightly on focus (`box-shadow: 0 0 10px rgba(0, 229, 255, 0.15)`) to guide keyboard input.

---

## 5. Security & Responsive Isolation

*   **HTML Sanitization & Sandboxing:** Untrusted AI-generated HTML is rendered inside an `iframe` with the `sandbox="allow-scripts"` parameter. This allows javascript contained in the artifact to run, but blocks access to parent cookies, host local storage, or same-origin cross-site scripting (XSS) risks.
*   **Responsive Collapsing:** The layout wraps flex-containers. If the window width is below `768px`, the sidebar collapses to a sliding menu, and the Artifact Panel occupies the full width to keep text readable on smaller screens.
