"""
Test suite for lightrag.kw_lazy module

This module provides lazy import helpers for KeyBERT-based keyword extraction.
Tests cover successful imports, missing dependencies, and error handling.
"""

import pytest
from unittest.mock import patch, MagicMock

from lightrag.kw_lazy import get_keybert_model


class TestKeyBERTModel:
    """Test cases for KeyBERT model lazy loading"""

    def test_get_keybert_model_success(self):
        """Test successful KeyBERT model instantiation when dependencies are available"""
        # Mock the dependencies
        mock_keybert = MagicMock()
        mock_sentence_transformer = MagicMock()
        mock_model = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "keybert": mock_keybert,
                "sentence_transformers": mock_sentence_transformer,
            },
        ):
            # Configure mocks
            mock_keybert.KeyBERT = MagicMock(return_value=mock_model)
            mock_sentence_transformer.SentenceTransformer = MagicMock(
                return_value=MagicMock()
            )

            result = get_keybert_model()

            # Verify KeyBERT was instantiated with correct model
            mock_keybert.KeyBERT.assert_called_once()
            mock_sentence_transformer.SentenceTransformer.assert_called_once_with(
                "all-mpnet-base-v2"
            )
            assert result is mock_model

    def test_get_keybert_model_missing_keybert(self):
        """Test returns None when KeyBERT is not installed"""
        with patch.dict(
            "sys.modules", {"keybert": None, "sentence_transformers": MagicMock()}
        ):
            result = get_keybert_model()
            assert result is None

    def test_get_keybert_model_missing_sentence_transformers(self):
        """Test returns None when sentence_transformers is not installed"""
        with patch.dict(
            "sys.modules", {"keybert": MagicMock(), "sentence_transformers": None}
        ):
            result = get_keybert_model()
            assert result is None

    def test_get_keybert_model_import_error(self):
        """Test returns None when import fails with any exception"""
        with patch("builtins.__import__", side_effect=ImportError("No module")):
            result = get_keybert_model()
            assert result is None

    def test_get_keybert_model_runtime_error(self):
        """Test returns None when instantiation fails with runtime error"""
        mock_keybert = MagicMock()
        mock_sentence_transformer = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "keybert": mock_keybert,
                "sentence_transformers": mock_sentence_transformer,
            },
        ):
            # Make KeyBERT constructor raise an exception
            mock_keybert.KeyBERT = MagicMock(
                side_effect=RuntimeError("Model loading failed")
            )
            mock_sentence_transformer.SentenceTransformer = MagicMock(
                return_value=MagicMock()
            )

            result = get_keybert_model()
            assert result is None

    def test_get_keybert_model_correct_model_name(self):
        """Test that the correct sentence transformer model name is used"""
        mock_keybert = MagicMock()
        mock_sentence_transformer = MagicMock()
        mock_sentence_model = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "keybert": mock_keybert,
                "sentence_transformers": mock_sentence_transformer,
            },
        ):
            mock_keybert.KeyBERT = MagicMock(return_value=MagicMock())
            mock_sentence_transformer.SentenceTransformer = MagicMock(
                return_value=mock_sentence_model
            )

            get_keybert_model()

            # Verify the correct model name is used
            mock_sentence_transformer.SentenceTransformer.assert_called_once_with(
                "all-mpnet-base-v2"
            )

    @pytest.mark.parametrize(
        "exception",
        [
            ImportError("No module named 'keybert'"),
            ModuleNotFoundError("No module named 'sentence_transformers'"),
            RuntimeError("CUDA out of memory"),
            ValueError("Invalid model name"),
            Exception("Unexpected error"),
        ],
    )
    def test_get_keybert_model_handles_all_exceptions(self, exception):
        """Test that all exceptions are caught and return None"""
        with patch.dict(
            "sys.modules",
            {"keybert": MagicMock(), "sentence_transformers": MagicMock()},
        ):
            # Make the import fail with specific exception
            with patch("builtins.__import__", side_effect=exception):
                result = get_keybert_model()
                assert result is None
