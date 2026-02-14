"""Tests for lightrag.kg.postgres_impl backward compatibility."""

import warnings


def test_deprecation_warning_pgkvstorage():
    """Test that importing PGKVStorage from postgres_impl emits deprecation warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from lightrag.kg.postgres_impl import PGKVStorage

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "PGKVStorage" in str(w[0].message)
        assert "lightrag.kg.postgres_impl" in str(w[0].message)
        assert "deprecated" in str(w[0].message).lower()


def test_deprecation_warning_pgvectorstorage():
    """Test that importing PGVectorStorage from postgres_impl emits deprecation warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from lightrag.kg.postgres_impl import PGVectorStorage

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "PGVectorStorage" in str(w[0].message)


def test_deprecation_warning_pgdocstatusstorage():
    """Test that importing PGDocStatusStorage from postgres_impl emits deprecation warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from lightrag.kg.postgres_impl import PGDocStatusStorage

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "PGDocStatusStorage" in str(w[0].message)


def test_deprecation_warning_pggraphstorage():
    """Test that importing PGGraphStorage from postgres_impl emits deprecation warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        from lightrag.kg.postgres_impl import PGGraphStorage

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "PGGraphStorage" in str(w[0].message)


def test_backward_compat_imports_work():
    """Test that backward compatibility imports still work."""
    from lightrag.kg.postgres_impl import (
        PGKVStorage,
        PGVectorStorage,
        PGDocStatusStorage,
        PGGraphStorage,
        PostgreSQLDB,
    )

    # Just verify they can be imported (class objects)
    assert PGKVStorage is not None
    assert PGVectorStorage is not None
    assert PGDocStatusStorage is not None
    assert PGGraphStorage is not None
    assert PostgreSQLDB is not None
