---
name: "cheersai-desktop-ui-spec"
description: "Applies the CheersAI Desktop UI/UE spec to pages, cards, badges, dialogs, and chat surfaces. Invoke when adjusting Desktop visual style or interaction details."
---

# CheersAI Desktop UI Spec

This skill standardizes UI work in the CheersAI Desktop repository according to the workspace design authority:

- `/Users/FYP/Documents/WorkSpace/CheersAI/CheersAI - docs/02-解决方案/0202-设计/CheersAI产品UI规范.md`

Use this skill whenever a task changes:

- page layout
- cards, badges, headers, or grouped sections
- dialogs, drawers, or confirmation flows
- chat surfaces and input areas
- button, spacing, color, radius, or state feedback details

Do not invoke this skill for pure backend, data, auth, or deployment tasks that do not change UI.

## Source Of Truth

If implementation and memory conflict, the design document wins. Re-read the document before editing UI and align the code to it.

## Core Rules

1. Use the CheersAI color system only.
2. Prefer `#3b82f6` / `#2563eb` for primary actions and key highlights.
3. Use functional colors consistently:
   - success: `#10b981`
   - warning: `#f59e0b`
   - error: `#ef4444`
   - info: `#8b5cf6`
4. Use neutral text and borders from the gray scale:
   - primary text: `#111827`
   - secondary text: `#4b5563`
   - border: `#e5e7eb`
   - soft background: `#f9fafb`
5. Keep spacing on the 4px system.
6. Keep radii aligned to the spec:
   - buttons/inputs: 8px
   - cards: 8px to 12px
   - chat bubbles/dialog blocks: 16px
   - badges: full pill only when semantically needed
7. Keep transitions restrained:
   - fast 150ms
   - standard 200ms
   - avoid decorative motion that does not help feedback

## Component Guidance

### Buttons

- Primary button:
  - background `#3b82f6`
  - hover `#2563eb`
  - white text
  - 8px radius
- Secondary button:
  - white or transparent background
  - border `#d1d5db`
  - text `#4b5563`
  - hover background `#f3f4f6`

### Dialogs

- Use white panels with neutral borders and spec shadows.
- Title uses strong contrast.
- Description uses secondary gray.
- Critical warnings should use icon + text + container emphasis, not color alone.
- Confirmation dialogs should avoid off-brand orange/red gradients unless the product doc explicitly requires them.

### Badges

- Published or healthy state: green family
- Pending or warning state: yellow family
- Neutral informational count badge: blue info background or gray neutral background
- Avoid mixing multiple unrelated accent colors in the same area

### Chat Input And Confirmation

- Input containers should use light neutral backgrounds, clear borders, and visible focus rings.
- Sensitive confirmation UI should look trustworthy and product-native:
  - white dialog
  - blue info block
  - clear primary and secondary actions
  - checkbox row with visible state and keyboard-friendly hit area

## Accessibility Checks

Before finishing, verify:

1. Clickable elements are keyboard reachable when applicable.
2. Focus state is visible.
3. State is not expressed by color alone.
4. Text contrast remains clear on white and light backgrounds.

## Validation Checklist

- Re-read the UI spec doc before editing
- Compare touched UI against the color and spacing rules
- Check hover, active, disabled, and focus states
- Run diagnostics on edited files
- Perform a browser check for the changed surface when feasible

## Output Expectations

When finishing UI work with this skill, summarize:

1. Which surfaces were aligned to the spec
2. Which tokens or style rules were applied
3. How states and accessibility were handled
4. What was verified in browser or tests
