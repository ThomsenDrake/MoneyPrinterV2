## 2025-12-14 - Robust CLI Menus
**Learning:** CLI menus that exit or crash on invalid input break the user's flow and context, especially in sub-menus. This is a common "micro-UX" failure in CLI tools.
**Action:** Always wrap CLI inputs in a retry loop that handles validation errors gracefully and keeps the user in the current menu context. Use consistent visual cues (like emojis/colors) for prompts and errors.

## 2025-12-14 - Patching Imported Constants
**Learning:** When a module does `from config import CONSTANT`, patching `config.CONSTANT` in tests will not update the value in the module, because the module has its own reference.
**Action:** Patch the constant in the target module's namespace (e.g., `patch("target_module.CONSTANT")`) instead of the source module.
