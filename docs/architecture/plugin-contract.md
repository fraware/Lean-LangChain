# Plugin and extension contract

Versioned contract for external policy packs and extensions. Safe to depend on for tool builders and platform integrators.

## Policy pack plugin contract (v1)

**Stability:** v1 is stable. New optional fields may be added to the pack schema with defaults; existing fields are not removed. A future v2 may introduce breaking changes under a new contract version.

**What you implement:** A YAML file that validates as `PolicyPack` (see `packages/policy/obligation_runtime_policy/models.py`). Required keys: `version`, `name`, `description`. Optional keys (with defaults): `allow_trust_compiler`, `block_sorry_ax`, `block_unexpected_custom_axioms`, `require_human_if_imports_change`, `protected_paths`, `require_human_on_trust_delta`, `allow_interactive_warnings`, and the protocol flags (`single_owner_handoff`, `reviewer_gated_execution`, etc.).

**How the runtime loads it:**

- **By name:** `load_pack("strict_patch_gate_v1")` loads from the built-in `packs/` directory.
- **By path:** `load_pack("/path/to/my_pack.yaml")` or `load_pack_from_path(Path("/path/to/my_pack.yaml"))` loads an external file. Use an absolute path or a path containing a directory separator.
- **Via env:** Set `OBR_POLICY_PACK` to a pack name (e.g. `strict_patch_gate_v1`) or to an absolute path to a `.yaml` file. The orchestrator and graph use this when loading the pack for review and protocol evaluation.

**Versioning:** The `version` field inside the YAML is the pack’s own version (e.g. `"0.1.0"`). The *plugin contract* version (v1) is the loader API and schema stability guarantee above. When the runtime adds new optional fields to `PolicyPack`, existing packs remain valid without change.

**Example:** See `examples/integrations/policy_pack_extension/custom_strict_v1.yaml` and that directory’s README.

## Extension stability notes

- Built-in packs in `packages/policy/obligation_runtime_policy/packs/` are part of the repo and may change between releases.
- External packs loaded by path are not validated for signature or provenance; use your own supply-chain controls if required.
- For protocol evaluation, the runtime uses additional pack attributes (e.g. `single_owner_handoff`). Omitted keys default to `false`; see `PolicyPack` for the full list.

**See also:** [CONTRIBUTING.md](../../CONTRIBUTING.md) (Plugins and extensions), [pack_loader.py](../../packages/policy/obligation_runtime_policy/pack_loader.py), [examples/integrations/](../../examples/integrations/README.md).
