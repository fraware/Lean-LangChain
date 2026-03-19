# Plugin and extension contract

Versioned contract for external policy packs and extensions. Safe to depend on for tool builders and platform integrators.

## Policy pack plugin contract (v1)

**Stability:** v1 is stable. New optional fields may be added to the pack schema with defaults; existing fields are not removed. A future v2 may introduce breaking changes under a new contract version.

**What you implement:** A YAML file that validates as `PolicyPack` (see `packages/policy/lean_langchain_policy/models.py`). Required keys: `version`, `name`, `description`. Optional keys (with defaults): `allow_trust_compiler`, `block_sorry_ax`, `block_unexpected_custom_axioms`, `require_human_if_imports_change`, `protected_paths`, `require_human_on_trust_delta`, `allow_interactive_warnings`, and the protocol flags (`single_owner_handoff`, `reviewer_gated_execution`, etc.).

**How the runtime loads it:**

- **By name:** `load_pack("strict_patch_gate_v1")` loads from the built-in `packs/` directory.
- **By path:** `load_pack("/path/to/my_pack.yaml")` or `load_pack_from_path(Path("/path/to/my_pack.yaml"))` loads an external file. Use an absolute path or a path containing a directory separator.
- **Via env:** Set `OBR_POLICY_PACK` to a pack name (e.g. `strict_patch_gate_v1`) or to an absolute path to a `.yaml` file. The orchestrator and graph use this when loading the pack for review and protocol evaluation.

**Versioning:** The `version` field inside the YAML is the pack’s own version (e.g. `"0.1.0"`). The *plugin contract* version (v1) is the loader API and schema stability guarantee above. When the runtime adds new optional fields to `PolicyPack`, existing packs remain valid without change.

**Example:** See `examples/integrations/policy_pack_extension/custom_strict_v1.yaml` and that directory’s README.

## Policy pack plugin contract (v1.1, additive)

**Stability:** Backward compatible with v1. Same required keys. New optional keys:

- **`extends`:** Single string, name or path of another pack. Base fields are merged first; this file’s keys override.
- **`import`:** List of pack names or paths. Each pack is merged in list order; later entries override earlier ones. Then this file’s keys override (except `extends` / `import`, which are consumed at load time).
- **`path_rules`:** List of `{ glob, require_human?, reason_code? }`. After batch verification succeeds, if any `changed_files` entry (from patch metadata) matches `glob` (Unix-style `fnmatch`), policy returns `needs_review` with `reason_code` (default `path_rule_review`).

Composition depth is capped (see `pack_loader.py`). Cycles in `extends` / `import` raise at load time.

### Composition merge semantics (v1.1)

Load order and precedence (see `pack_loader._merge_pack_layers`):

1. If `extends` is set, that base pack is merged first (recursively).
2. Each entry in `import` is merged in **list order**; **later imports overwrite** earlier keys on conflict (shallow dict merge: `merged.update(sub)` per layer).
3. The current file’s body (all keys except `extends` and `import`) is merged last and **wins** over all bases and imports.

**Field behavior:**

- **Scalars and booleans:** Last writer wins (child / later import / own body).
- **Lists** (`protected_paths`, `path_rules`, `trust_gates`, `import` list itself): the merged layer from a child pack **replaces** the list from the previous merge for that key when the child YAML specifies the key; there is **no** deep merge of list elements. To combine path rules from multiple packs, use `import` and repeat rules in the final pack if needed.
- **Depth:** Maximum composition depth is 12; exceeding it raises `ValueError`.
- **Cycles:** Visiting the same pack path twice while resolving `extends`/`import` raises `ValueError` with a circular reference message.

**Import conflict policy:** Optional `composition_conflict_policy`:

- `last_wins` (default): each `import` entry overwrites overlapping scalar flags from earlier imports, as before.
- `error_on_import_scalar_override`: while merging the **current file’s** `import` list only, if a later import would change any of the tracked scalar/protocol flags (`require_human_if_imports_change`, `block_sorry_ax`, protocol booleans, etc.) relative to the merge-so-far, load fails with `ValueError`. Does not apply to `extends` merges or to the final pack body (body still wins). Use when parallel imports must not silently disagree.

**Trust gates (`trust_gates`):** List of rules `{ rule_id?, when_trust_level[], path_globs[], require_human?, reason_code? }`. After batch verification succeeds, if the batch `trust_level` is in `when_trust_level` and any `changed_files` entry matches a `path_globs` entry (empty `path_globs` means “any change”), policy returns `needs_review` with the given `reason_code`. Evaluated together with `path_rules` and import/protected-path gates.

**Example:** [composed_v1_1.yaml](../../examples/integrations/policy_pack_extension/composed_v1_1.yaml), built-in [loose_imports_v1.yaml](../../packages/policy/lean_langchain_policy/packs/loose_imports_v1.yaml).

## Extension stability notes

- Built-in packs in `packages/policy/lean_langchain_policy/packs/` are part of the repo and may change between releases.
- External packs loaded by path are not validated for signature or provenance; use your own supply-chain controls if required.
- For protocol evaluation, the runtime uses additional pack attributes (e.g. `single_owner_handoff`). Omitted keys default to `false`; see `PolicyPack` for the full list.

**See also:** [CONTRIBUTING.md](../../CONTRIBUTING.md) (Plugins and extensions), [pack_loader.py](../../packages/policy/lean_langchain_policy/pack_loader.py), [examples/integrations/](../../examples/integrations/README.md).
