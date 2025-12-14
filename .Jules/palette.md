## 2025-12-14 - Robust CLI Menus
**Learning:** CLI menus that exit or crash on invalid input break the user's flow and context, especially in sub-menus. This is a common "micro-UX" failure in CLI tools.
**Action:** Always wrap CLI inputs in a retry loop that handles validation errors gracefully and keeps the user in the current menu context. Use consistent visual cues (like emojis/colors) for prompts and errors.
