"""
Exceções customizadas para a aplicação GlassPrinter.

Este módulo define as exceções específicas da aplicação para melhor
tratamento de erros e diferenciação de casos de uso.
"""


class GlassPrinterException(Exception):
    """Exceção base para todas as exceções da aplicação GlassPrinter."""

    pass


class ValidationError(GlassPrinterException):
    """Exceção levantada quando há erro de validação de dados."""

    pass


class PDFGenerationError(GlassPrinterException):
    """Exceção levantada quando há erro na geração do PDF."""

    pass


class PrintError(GlassPrinterException):
    """Exceção levantada quando há erro na impressão."""

    pass


class FileOperationError(GlassPrinterException):
    """Exceção levantada quando há erro em operações com arquivos."""

    pass
