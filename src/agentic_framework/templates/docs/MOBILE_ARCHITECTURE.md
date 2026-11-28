# Mobile Application Architecture

- **Framework**: <React Native (Expo + TypeScript) | Flutter | Kotlin | Swift>
- **Target Platforms**: Android & iOS
- **Shared Backend API**: <URL / adapter boundary>

## Navigation & Platform Conventions
- Tab / stack / drawer structure and deep-linking routes.
- Android hardware back & iOS swipe-back behavior.

## Device Capabilities & Permissions
- Camera / Gallery / Location / Push Notifications (with rationale and denied-state fallback).

## Offline, Storage & Security
- Encrypted token storage (SecureStore / Keychain / Keystore).
- Offline cache and retry strategy.

## Android & iOS Verification Checklist
- [ ] Safe areas and status bar on notched/edge-to-edge devices
- [ ] Keyboard avoidance on all forms
- [ ] Network interruption & background/foreground lifecycle
