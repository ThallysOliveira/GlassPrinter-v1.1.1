"""
Funções utilitárias e auxiliares para a aplicação GlassPrinter.

Este módulo contém funções reutilizáveis como manipulação de caminhos,
validação de dados, e operações de arquivo.
"""

import sys
import os
import logging
import re
import time
from typing import Any, Optional
from pathlib import Path

import pandas as pd
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from core.config import (
    FONT_DEFAULT,
    FONT_BOLD,
    FONT_THIN,
    FONT_SEMIBOLD,
    FONTS_DIR,
    ICON_FONT_NAME,
    ICON_FONT_FILE,
)


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# PATH UTILITIES
# ============================================================================

def get_resource_path(relative_path: str) -> str:
    """
    Retorna o caminho absoluto para um recurso, funcionando tanto em
    desenvolvimento quanto em executáveis criados com PyInstaller.

    Args:
        relative_path: Caminho relativo para o recurso desejado.

    Returns:
        Caminho absoluto para o recurso.

    Examples:
        >>> path = get_resource_path("assets/logo.ico")
        >>> os.path.exists(path)
        True
    """
    try:
        # PyInstaller cria uma variável temporária _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Em desenvolvimento, usa o diretório do script
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base_path, relative_path)

def register_custom_fonts() -> None:
    """
    Registra fontes no ReportLab para geração de PDF.
    """
    fonts = [
        (FONT_DEFAULT, "Onest-Regular.ttf"),
        (FONT_BOLD, "Onest-Bold.ttf"),
        (FONT_THIN, "Onest-Thin.ttf"),
        (FONT_SEMIBOLD, "Onest-SemiBold.ttf"),
        (ICON_FONT_NAME, ICON_FONT_FILE),
    ]
    
    for font_name, font_file in fonts:
        try:
            path = get_resource_path(os.path.join(FONTS_DIR, font_file))
            if os.path.exists(path):
                # TTFont espera .ttf/.otf; aqui mantemos o mesmo mecanismo do projeto
                # Caso a fonte não seja compatível com TTFont, o erro será logado e não quebra a UI.
                pdfmetrics.registerFont(TTFont(font_name, path))
                logger.info(f"Fonte {font_name} registrada com sucesso.")
            else:
                logger.warning(f"Arquivo de fonte não encontrado: {path}")
        except Exception as e:
            if "postscript outlines" in str(e).lower():
                logger.error(f"Erro: A fonte {font_name} (.otf) usa PostScript outlines, que não são suportados pelo ReportLab. Converta para .ttf.")
            else:
                logger.error(f"Erro ao registrar fonte {font_name}: {e}")


def get_default_output_path(subfolder: str = "Etiquetas_GlassPrinter") -> Path:
    """
    Obtém o caminho da pasta onde o executável/script está, criando uma subpasta se necessário.

    Args:
        subfolder: Nome da subpasta de saída.

    Returns:
        Path object para a pasta de saída.

    Raises:
        OSError: Se não for possível criar a pasta.
    """
    if getattr(sys, 'frozen', False):
        # Caminho onde o .exe está localizado
        base_dir = os.path.dirname(sys.executable)
    else:
        # Caminho da raiz do projeto em desenvolvimento
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    output_path = Path(base_dir) / subfolder
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


# ============================================================================
# DATA VALIDATION AND NORMALIZATION
# ============================================================================

def is_empty_value(value: Any) -> bool:
    """
    Verifica se um valor é vazio, lidando com listas, NaN e None de forma segura.
    """
    if value is None:
        return True
    
    # Se o pandas entregou uma lista, verifica se ela tem conteúdo
    if isinstance(value, (list, tuple)):
        return len(value) == 0

    # Se for um valor escalar (número, string, etc), converte para string
    # e remove espaços para validar se está vazio
    str_val = str(value).strip().lower()
    return str_val in ("", "nan", "n/a", "none")


def normalize_text(text: Any, patterns_to_remove: tuple = (), use_regex: bool = True) -> str:
    """
    Normaliza o texto garantindo que o input seja tratado como string.
    """
    # Se for lista (causa do erro anterior), achata para string
    if isinstance(text, list):
        text = " ".join(map(str, text))
    
    if is_empty_value(text):
        return ""

    # Converte para string e limpa os padrões
    normalized = str(text)
    for pattern in patterns_to_remove:
        if use_regex:
            normalized = re.sub(pattern, "", normalized, flags=re.IGNORECASE)
        else:
            normalized = normalized.replace(pattern, "")

    return normalized.strip()


def safe_get_dict_value(data: dict, key: str, default: str = "") -> str:
    """
    Obtém um valor de um dicionário com segurança, retornando um padrão se vazio.

    Args:
        data: Dicionário de dados.
        key: Chave a procurar.
        default: Valor padrão se a chave não existir ou estiver vazia.

    Returns:
        Valor do dicionário ou o padrão.
    """
    value = data.get(key, default)

    if is_empty_value(value):
        return default

    return str(value).strip()


# ============================================================================
# FILE OPERATIONS
# ============================================================================

def ensure_file_not_locked(filepath: str, max_retries: int = 3) -> bool:
    """
    Verifica se um arquivo está bloqueado/aberto por outro processo.

    Args:
        filepath: Caminho do arquivo a verificar.
        max_retries: Número máximo de tentativas.

    Returns:
        True se o arquivo está disponível, False caso contrário.
    """
    if not os.path.exists(filepath):
        return True

    for attempt in range(max_retries):
        try:
            with open(filepath, "a"):
                return True
        except PermissionError:
            time.sleep(0.3)  # Aguarda um curto período antes de tentar novamente
            if attempt == max_retries - 1:
                return False
            continue

    return False


def create_backup_filename(base_name: str, timestamp_format: str = "%Y%m%d_%H%M%S") -> str:
    """
    Gera um nome de arquivo com timestamp.

    Args:
        base_name: Nome base do arquivo.
        timestamp_format: Formato do timestamp.

    Returns:
        Nome do arquivo com timestamp.

    Examples:
        >>> filename = create_backup_filename("etiquetas")
        >>> filename.startswith("Lote_etiquetas_")
        True
    """
    from datetime import datetime

    timestamp = datetime.now().strftime(timestamp_format)
    return f"Lote_{base_name}_{timestamp}"

def processar_sufixo_notebook(equipamento: str, resumo: str) -> str:
    """
    Adiciona o sufixo - ADM ou - DEV para notebooks baseando-se no resumo.
    """
    eqp = str(equipamento)
    resumo_txt = str(resumo).lower() if resumo else ""
    
    if "notebook" in eqp.lower():
        if "adm" in resumo_txt:
            return f"{eqp} - ADM"
        if "dev" in resumo_txt:
            return f"{eqp} - DEV"
    return eqp

def motor_de_mapeamento(df_bruto: pd.DataFrame, mapping_dict: dict) -> pd.DataFrame:
    """
    Lê o arquivo bruto e padroniza as colunas e textos com busca insensível a maiúsculas/minúsculas.
    """
    df_processado = pd.DataFrame()
    
    # Criar um dicionário de busca: {nome_da_coluna_em_minusculo: nome_original_da_coluna}
    colunas_reais = {str(col).lower().strip(): col for col in df_bruto.columns}
    
    for campo_app, colunas_possiveis in mapping_dict.items():
        coluna_encontrada = None
        for col_possivel in colunas_possiveis:
            busca = str(col_possivel).lower().strip()
            if busca in colunas_reais:
                coluna_encontrada = colunas_reais[busca]
                break
        
        if coluna_encontrada:
            df_processado[campo_app] = df_bruto[coluna_encontrada]
        else:
            df_processado[campo_app] = ""

    return df_processado

# ============================================================================
# DATA FORMATTING
# ============================================================================

def format_quantity_product(quantity: str, product: str) -> str:
    """
    Formata a quantidade e o produto em um texto combinado.

    Args:
        quantity: Quantidade do item.
        product: Nome do produto.

    Returns:
        Texto formatado como "quantidade - produto".

    Examples:
        >>> format_quantity_product("5", "Monitor LED")
        '5 - Monitor LED'
    """
    qty = safe_get_dict_value({"qty": quantity}, "qty", "1")
    prod = product.strip() if product else ""

    if not prod:
        return qty

    return f"{qty} - {prod}".strip(" -")


def format_jira_link(issue_key: str, base_url: str) -> str:
    """
    Formata um link para o Jira.

    Args:
        issue_key: Chave da issue (ex: "PROJ-123").
        base_url: URL base do Jira.

    Returns:
        URL completa para a issue.

    Examples:
        >>> url = format_jira_link("ABC-123", "https://jira.example.com/browse")
        >>> url == "https://jira.example.com/browse/ABC-123"
        True
    """
    if is_empty_value(issue_key):
        return "N/A"

    return f"{base_url}/{issue_key.strip().upper()}"
