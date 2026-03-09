from obligation_runtime_schemas.hashing import canonical_sha256


def test_hash_stability_for_dict_order() -> None:
    a = {"b": 2, "a": 1}
    b = {"a": 1, "b": 2}
    assert canonical_sha256(a) == canonical_sha256(b)
