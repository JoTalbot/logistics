# V29 — Recommendation Replay Evaluation

V29 adds a deterministic, read-only evaluation layer for shadow commercial recommendations.

## Measures

- number of recommendation cases;
- cases with a later score observation;
- terminal wins and losses;
- unknown outcomes;
- mean change between suggested and later score;
- mean absolute prediction error when later realized and predicted margins are available.

## Safety

Evaluation is pure and side-effect free. It does not alter pricing, opportunity scores, autonomy policy, publication state, negotiations, contracts, or financial records.

A recommendation can be evaluated after later operational evidence exists, but the result is evidence for an operator or release process, not an authorization to mutate production policy.
