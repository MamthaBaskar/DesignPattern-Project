"""
Factory Pattern: DocumentProcessorFactory.
Instantiates and returns the appropriate DocumentAdapterInterface based on file extension.
"""

from pathlib import Path
from typing import Dict, Type

from .adapters import DOCXAdapter, PDFAdapter, TXTAdapter
from .interfaces import DocumentAdapterInterface
from .validators import DocumentValidationError


class DocumentProcessorFactory:
    """
    Factory class that decouples document processing clients
    from concrete adapter classes.
    """

    _registry: Dict[str, Type[DocumentAdapterInterface]] = {
        ".pdf": PDFAdapter,
        ".docx": DOCXAdapter,
        ".txt": TXTAdapter,
    }

    @classmethod
    def create_adapter(cls, filename: str) -> DocumentAdapterInterface:
        """
        Creates and returns a concrete DocumentAdapter for the specified file.

        Args:
            filename: The name or path of the target document.

        Returns:
            DocumentAdapterInterface: An instance of PDFAdapter, DOCXAdapter, or TXTAdapter.

        Raises:
            DocumentValidationError: If file extension is unsupported.
        """
        ext = Path(filename).suffix.lower()
        adapter_cls = cls._registry.get(ext)

        if not adapter_cls:
            supported = ", ".join(cls._registry.keys())
            raise DocumentValidationError(
                f"Unsupported document type '{ext}'. Factory only supports: {supported}",
                "UNSUPPORTED_ADAPTER",
            )

        return adapter_cls()

    @classmethod
    def register_adapter(cls, extension: str, adapter_cls: Type[DocumentAdapterInterface]) -> None:
        """Allows runtime extensibility for new document formats."""
        cls._registry[extension.lower()] = adapter_cls

