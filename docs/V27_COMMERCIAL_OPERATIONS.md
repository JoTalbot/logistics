# V27 — Commercial Calibration Operations

V27 turns V26 calibration signals into a controlled operational gate.

## Rules

1. Drift must be detected by V26.
2. A minimum terminal sample is required before a signal is actionable.
3. Explicit operator approval is required before a shadow adjustment is considered eligible.
4. Suggested score changes are bounded to a small delta.
5. No function in V27 mutates production pricing, scoring, autonomy policy, publication, negotiation, contracts, or financial state.

## Purpose

The system can now say: **this calibration signal is strong enough to review**. It still cannot say: **I changed production because I felt statistically adventurous**.

The output is suitable for an operator review queue and future replay experiments. Production policy changes remain a separately authorized release decision.
