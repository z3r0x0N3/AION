# AION Security Model

## Credential Handling

Credentials are managed through the `CredentialManager` abstraction layer:

- **EnvCredentialProvider**: Reads from `AION_CRED_*` environment variables
- **FileCredentialProvider**: Encrypted JSON file at `~/.aion/credentials.json`
- **KeyringCredentialProvider**: Uses system keyring (SecretService, macOS Keychain, Windows Credential Manager)

Always prefer the keyring provider in production. File provider is for development only.

## Plugin Sandbox

- Plugins are Python files loaded via `importlib`
- Restricted builtins: no `exec`, `eval`, `compile`, `__import__`, `open` (only with capability)
- Capability gating: each plugin declares required capabilities; denied at runtime if not declared
- No filesystem access by default
- No network access by default
- No subprocess access by default

## Thread Safety

- All shared state guarded by `threading.RLock`
- UI mutations go through `UIMutationScheduler` (bounded deque, drained on main thread)
- EventBus operations are atomic under RLock
- StateStore uses per-connection SQLite with WAL mode and RLock

## Subprocess Timeouts

All subprocess calls must use `safe_subprocess_run()` with a timeout parameter.
Default timeout is 30s for local operations, 60s for network.
Long-running operations should use `run_in_background()`.

## Network Policy

- Webhook triggers listen for incoming events only (no outbound by default)
- Plugin network capability must be explicitly granted
- No built-in telemetry sends data externally
