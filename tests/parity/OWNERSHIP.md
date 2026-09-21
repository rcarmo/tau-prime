# Tau-owned canonical parity artifacts

Tau independently owns this version-controlled parity suite. It contains contracts, canonical Gherkin, semantic state, interaction cases, Piclaw/Tau/Vibes adapters, deterministic capture/comparison primitives, and tests.

Running the owned unit/contract suite must not depend on a Vibes checkout, `/workspace/projects/ui-parity-fixtures`, or another mutable workspace directory. Piclaw and Vibes static roots used for headed comparisons are explicit external test inputs; generated captures remain outside this repository.

The product-facing copy `tests/ux/features/canonical-ux.feature` must remain byte-identical to `tests/parity/features/canonical-ux.feature` at SHA-256:

```text
a08a623880c6f327bc051edc51bb2bbff2959aed86421b5227e61d5a92fc2441
```

## Public validation

From the Tau repository root:

```bash
make test-parity
```

Equivalent direct command:

```bash
bun test tests/parity
```

Comparison runners require explicit external roots where documented. The Tau adapter defaults only to Tau-owned static assets; the Vibes adapter deliberately requires `staticRoot` from its caller.

## Provenance and adaptations

Initial content was copied from the independently owned Vibes suite at commit `0ecf550aa328dc33d6d657a2c53322eee5c7b7f3` on 2026-09-21. That suite had itself imported the former unversioned shared fixture after its alignment gate passed.

Tau-specific adaptations:

- ownership and public validation instructions name Tau;
- the Vibes adapter has no repository-relative Vibes default and requires an explicit external static root;
- the canonical product copy remains Tau's `tests/ux/features/canonical-ux.feature`;
- generated screenshots/reports and external product assets are never vendored.

Initial key hashes retained from provenance:

- `canonical-state.mjs`: `9c0f0c5bcb66f46b376abeda7f5c7da0e32a88d5fb8083e14fc6577d41bde235`
- `cases.mjs`: `e86785cc361ad5696920b3c8b5e4dc1ccbadc228e8b38b227552bc985038b3fb`
- `INTERACTION-CONTRACT.md`: `7e198bb1f6c8f04b77e9ab00c924c506011dcd982f92bb5bc7f7ff927534dfa9`
- `QUEUE-MODEL-FLOWS.md`: `cae2e184fc29a4b54af664eef2cdbfebab0a949c2c4582029d46759a6dbf2b03`
- `run-plan-comparison.mjs`: `690c616e9ded7fbcc004ca382de7a3f31ff43480769b1b467f88bfde593d9f15`
- `adapters/tau.mjs`: `d5be996ab5af23b7742c5604931c3178ee47391d0aac32c783f1109c6bcfeb4f`
- imported `adapters/vibes.mjs`: `03f1cb2000c2cfb1718ce40128204a3a67552ca20147049fa46d88e4155c140d` before Tau's explicit-root adaptation
