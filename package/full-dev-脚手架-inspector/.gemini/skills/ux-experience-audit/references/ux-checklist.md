# UX Checklist

## 1. Core User Path

- Can a first-time user finish setup without reading source code?
- Does every critical action have immediate feedback (loading/success/error)?
- Can users recover from errors without refreshing the page?

## 2. Configuration Reliability

- Provider switch updates base URL and default model consistently.
- Saved config is actually used by runtime requests.
- Error messages include provider/baseURL context when auth fails.

## 3. Interaction Safety

- Copy/export actions handle clipboard/file permission failures.
- Disabled/non-selectable UI options cannot trigger invalid state.
- Buttons that mutate state prevent duplicate clicks when loading.

## 4. Observability

- Console/network logs can map to user-visible failures.
- Error toast text is actionable (what failed, what to check next).
- Debug record (.debug) includes reproduction steps and validation commands.

## 5. Checkfix Minimum

- Run at least one automated check type (build/lint/test).
- Re-run checks after fixes until pass or explicit debt note.
- Sync docs for user-facing behavior changes.
