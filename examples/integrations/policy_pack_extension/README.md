# Policy pack extension

Ship your own policy pack (YAML) and load it by path. The pack must conform to the PolicyPack schema (version, name, description, and optional flags such as reviewer_gated_execution, protected_paths).

**Option 1 — Path:** Set `OBR_POLICY_PACK` to an absolute path to a `.yaml` file (or a path containing a directory separator). The orchestrator and graph will load it via `load_pack`.

**Option 2 — Copy:** Copy your pack into the built-in packs dir of an installed `lean-langchain-policy` and reference it by name.

**Example:** Use the sample pack in this directory:

```bash
export OBR_POLICY_PACK="$(pwd)/examples/integrations/policy_pack_extension/custom_strict_v1.yaml"
obr run-patch-obligation --thread-id demo --target-files Main.lean
```

See [pack_loader](../../packages/policy/lean_langchain_policy/pack_loader.py) for the plugin contract (load_pack_from_path, load_pack with path).
