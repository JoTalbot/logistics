# Publication adapters V1

The publication layer is intentionally split from provider transport. A `PublicationAdapter` renders a canonical `Load` into a provider payload; a future transport adapter performs the actual API/browser operation.

## Safety gates

- Only canonical loads reach publication preparation.
- Provider payloads preserve source provenance and explicitly represent the logistics role as `forwarder`.
- Markup is bounded to 0–100% in this V1 policy layer.
- Cancelled loads are rejected.
- Critical-risk autonomous publication requires the `human_operator` role.
- No automatic external publication is performed by the renderer itself.

## Current adapter

`GenericFreightExchangeAdapter` is a provider-neutral reference adapter. It is a contract and rendering testbed, not a claim that any external marketplace supports automated publication.

Provider-specific integrations must be implemented only through permitted official APIs or other explicitly authorized mechanisms, with credentials kept outside the repository.
