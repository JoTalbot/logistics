# Remote Agent: Android GUI + Ubuntu Server

## Goal

Provide a mobile-friendly Vercel web GUI for operating an AI coding/operations agent against a remote Ubuntu server, while keeping server credentials on the server and avoiding a public web-to-root SSH bridge.

## Recommended architecture

```text
Android browser / PWA
        |
        | HTTPS + authenticated session
        v
Vercel Web GUI
        |
        | HTTPS/WebSocket control channel
        v
Ubuntu Remote Agent
        |
        +--> local shell / Docker / Git
        +--> SSH to other hosts when explicitly configured
        +--> GitHub
        +--> project workspaces
```

### Why the agent should live on Ubuntu

An interactive shell, long-running commands, Docker access, PTY sessions and background processes are a poor fit for a Vercel request/function. The durable control plane should therefore be on the Ubuntu host. Vercel provides the UI, authentication, API gateway and static/realtime presentation.

The Ubuntu agent should initiate the outbound connection to the Vercel control plane. This avoids exposing an unrestricted inbound command endpoint and also avoids storing an Ubuntu private SSH key in Vercel.

## Security requirements

1. Never expose a root shell directly to the public internet.
2. Run the remote agent as a dedicated non-root Unix user.
3. Give that user access only to approved project directories and required Docker resources.
4. Use short-lived, rotated authentication credentials for the control channel.
5. Require explicit confirmation for destructive operations (`rm`, disk changes, firewall changes, credential changes, production database operations, etc.).
6. Record every command, actor, timestamp, working directory, exit code and output digest in an audit log.
7. Keep SSH private keys and provider secrets on Ubuntu or in an appropriate secret manager, never in Git.
8. Support a read-only mode and a kill/disconnect control.
9. Apply command timeouts, output limits and concurrency limits.
10. Never accept arbitrary shell text from unauthenticated HTTP requests.

## Remote SSH option

For direct developer workflows, use Codex Remote SSH from a trusted client. The Vercel GUI should not impersonate an SSH terminal when a native Remote SSH workflow is available.

For the Vercel GUI, use the Ubuntu agent as the execution boundary. If the agent needs to reach another machine, it can use SSH from Ubuntu with a dedicated key and restricted account.

## Android UX

The initial GUI should provide:

- Server connection status
- Project/workspace selector
- Agent task input
- Live task/progress state
- Terminal output stream
- Changed files summary
- Git status and recent commits
- Test/build status
- Approve / reject controls for privileged actions
- Stop agent button
- Audit history

The UI must be responsive and usable from a phone without requiring a desktop terminal.

## Logistics integration

The first workspace should support `JoTalbot/logistics` and expose its existing operational workflow without bypassing its API-first and audit-first principles.

The agent must be able to:

- inspect the repository;
- run tests and diagnostics;
- inspect Docker services;
- edit code/configuration;
- create commits and branches;
- report deployment state;
- interact with approved external APIs through existing application integrations.

Production actions remain gated by explicit policy/approval.

## Implementation phases

### Phase 1

- Vercel mobile web shell
- authenticated sessions
- Ubuntu agent registration
- heartbeat/online status
- task queue
- streamed logs
- cancel task

### Phase 2

- PTY terminal sessions
- workspace/project management
- Git operations
- Docker status/logs
- artifact and diff viewer

### Phase 3

- agent execution loop
- approval gates
- audit trail
- role-based permissions
- reconnect/resume after network interruption

### Phase 4

- Android PWA installability
- notifications
- multiple Ubuntu hosts
- health dashboard
- deployment controls
- controlled production operations

## Non-goals

- No public unauthenticated shell.
- No committed credentials.
- No unrestricted root execution from the browser.
- No dependency on a single Vercel request remaining open for an entire long-running job.
