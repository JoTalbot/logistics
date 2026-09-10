# Authorized Contact Channels

The logistics platform treats contact as a separate, explicitly authorized stage after discovery and qualification.

## Supported contract types

- Email
- Telegram
- Phone
- Web form

These are **contracts only**. They do not connect to providers, fetch contact lists, send messages, bypass platform controls, or perform autonomous outreach.

## Required gates

A contact intent must have:

1. a concrete target;
2. a channel;
3. a non-empty human-reviewed message draft;
4. explicit authorization for that channel/source;
5. no suppression or opt-out state;
6. human approval before sending.

The code deliberately keeps `human_approval_required=True` until an explicit operator approval transition occurs.

## Activation policy

Before any real adapter is implemented, verify the provider's current terms, API permissions, commercial conditions, privacy/retention requirements and applicable law. Technical accessibility is not authorization.

No bulk outreach, unsolicited messaging, contact harvesting, anti-bot bypass or opaque enrichment is part of the core platform.
