"""
Configurações e constantes globais da aplicação GlassPrinter.

Este módulo centraliza todas as configurações, constantes e valores padrão
utilizados em toda a aplicação, facilitando manutenção e alterações futuras.
"""

import os
from typing import Dict, Tuple, Any
from reportlab.lib.units import mm


# ============================================================================
# CONFIGURAÇÕES DA APLICAÇÃO
# ============================================================================

APP_VERSION: str = "1.1.1"
APP_TITLE: str = "GlassPrinter v1.1.1 - Autoglass"
APP_WINDOW_WIDTH: int = 1024
APP_WINDOW_HEIGHT: int = 720

# ============================================================================
# DIRETÓRIOS E CAMINHOS
# ============================================================================

ASSETS_DIR: str = "assets"
LAYOUTS_DIR: str = "layouts"
ICON_FILE: str = os.path.join(ASSETS_DIR, "logo.ico")
LOGO_FILE: str = os.path.join(ASSETS_DIR, "logo.png")
ICONS_DIR: str = os.path.join(ASSETS_DIR, "icons")
BACKGROUND_FILE: str = os.path.join(ASSETS_DIR, "fundo.png")
LOGO_TYPE_FILE: str = os.path.join(ASSETS_DIR, "logo_tipo.png")
FONTS_DIR: str = os.path.join(ASSETS_DIR, "fonts")

# Históricos separados por layout para evitar colunas bagunçadas
HISTORY_FILES: Dict[str, str] = {
    "adm": "historico_adm.csv",
    "unidade": "historico_unidade.csv",
    "pat_id": "historico_patrimonio.csv",
    "gati": "historico_gati.csv"
}

SETTINGS_FILE: str = "settings.json"

# ============================================================================
# CONFIGURAÇÕES DE PDF E ETIQUETAS
# ============================================================================

LABEL_WIDTH_MM: int = 100
LABEL_HEIGHT_MM: int = 80
LABEL_SIZE: Tuple[int, int] = (100 * mm, 80 * mm)
LABEL_SIZE_PAT_ID: Tuple[float, float] = (50 * mm, 40 * mm)

# QR Code
QR_CODE_VERSION: int = 1
QR_CODE_BOX_SIZE: int = 10
QR_CODE_BORDER: int = 1

# ============================================================================
# CORES (HexColor)
# ============================================================================

COLOR_HEADER_ADM: str = "#2021D4"  # Azul Royal Institucional
COLOR_PRIMARY_BLUE: str = "#0A64FF" # Azul Primário Autoglass
COLOR_SUPPORT_BLUE: str = "#73C6FF"  # Azul de Apoio 2
COLOR_HEADER_UNIDADE: str = "#73C6FF"  # Azul de Apoio 2 (Substituindo Amarelo)
COLOR_BACKGROUND_CELL: str = "#EEEDED"  # Cinza Apoio 3 para células de fundo
COLOR_BLACK: str = "#000000"
COLOR_WHITE: str = "#FFFFFF"
COLOR_SUCCESS: str = "#008444"  # Verde Institucional para botões de ação

# ============================================================================
# FONTES
# ============================================================================

FONT_DEFAULT: str = "Onest"
FONT_BOLD: str = "Onest-Bold"
FONT_THIN: str = "Onest-Thin"
FONT_SEMIBOLD: str = "Onest-SemiBold"

# Material Icons (font de ícones) — usada no PDF via ReportLab
# Observação: ReportLab/TTFont não aceita WOFF2.
ICON_FONT_NAME: str = "MaterialIconsOutlined"
ICON_FONT_FILE: str = "MaterialIconsOutlined-Regular.otf"

FONT_SIZE_TITLE: int = 14
FONT_SIZE_HEADER: int = 8
FONT_SIZE_LABEL: int = 7
FONT_SIZE_VALUE: int = 7
FONT_SIZE_QR_LABEL: int = 6

# ============================================================================
# LAYOUTS
# ============================================================================

LAYOUT_ADM: str = "adm"
LAYOUT_UNIDADE: str = "unidade"
LAYOUT_PAT_ID: str = "pat_id"
LAYOUT_GATI: str = "gati"
AVAILABLE_LAYOUTS: tuple = (LAYOUT_ADM, LAYOUT_UNIDADE, LAYOUT_PAT_ID, LAYOUT_GATI)

# Configuração de Grade por Layout (Sistema de Colunas no Rolo)
LAYOUT_GRID_CONFIG: Dict[str, Dict[str, Any]] = {
    LAYOUT_ADM: {"cols": 1, "gap": 0},
    LAYOUT_UNIDADE: {"cols": 1, "gap": 0},
    LAYOUT_PAT_ID: {"cols": 2, "gap": 0.5},
    LAYOUT_GATI: {"cols": 2, "gap": 0.5}
}

# Opções de equipamentos para o módulo PAT ID
PAT_ID_EQUIPMENT_TYPES: Tuple[str, ...] = (
    "Camera VHD", "DVR", "NVR", "Switch", "Roteador", "Notebook", "Monitor", "Impressora"
)

# ============================================================================
# CAMPOS DO FORMULÁRIO
# ============================================================================

SMART_MAPPING = {
    "chamado": ["Issue key", "Issue Key", "Chamado", "ID"],
    "solicitante": ["Nome Completo", "Beneficiário", "Solicitante", "Usuário"],
    "setor": ["Centro de Custo", "CC", "Setor", "Departamento"],
    "produto": ["Resumo", "Equipamentos", "Item", "Descrição", "nome"],
    "quantidade": ["Quantidade", "Qtd", "QTD", "Informe a quantidade"],
    "destino": ["Local Patrimonial", "Destino", "Unidade", "Localidade"],
    "tecnico": ["Relator", "Técnico", "Responsável", "Técnico Responsável"],
    "patrimonio": ["Patrimônio", "Tag", "Ativo", "Service Tag", "patrimonio"]
}

FORM_FIELDS: Tuple[Tuple[str, str], ...] = (
    ("Chamado", "chamado"),
    ("Beneficiário", "solicitante"),
    ("Setor/CC", "setor"),
    ("Produto", "produto"),
    ("Quantidade", "quantidade"),
    ("Destino", "destino"),
    ("Forma Envio", "forma_envio"),
    ("Técnico", "tecnico"),
    ("Patrimônio", "patrimonio"),
    ("Arquivo", "origem"),
)

# Definição de campos específicos por Layout para a Interface
FORM_FIELDS_ADM: Tuple[Tuple[str, str], ...] = (
    ("Chamado", "chamado"),
    ("Beneficiário", "solicitante"),
    ("Setor/CC", "setor"),
    ("Produto", "produto"),
    ("Quantidade", "quantidade"),
    ("Destino", "destino"),
    ("Técnico", "tecnico"),
    ("Arquivo", "origem"),
)

FORM_FIELDS_UNIDADE: Tuple[Tuple[str, str], ...] = (
    ("Chamado", "chamado"),
    ("Beneficiário", "solicitante"),
    ("Setor/CC", "setor"),
    ("Produto", "produto"),
    ("Quantidade", "quantidade"),
    ("Destino", "destino"),
    ("Forma Envio", "forma_envio"),
    ("Técnico", "tecnico"),
    ("Patrimônio", "patrimonio"),
    ("Arquivo", "origem"),
)

FORM_FIELDS_PAT_ID: Tuple[Tuple[str, str], ...] = (
    ("Produto", "produto"),
    ("Patrimônio", "patrimonio"),
    ("Arquivo", "origem"),
)

FORM_FIELDS_GATI: Tuple[Tuple[str, str], ...] = (
    ("Tipo", "produto"),
    ("Patrimônio", "patrimonio"),
    ("Arquivo", "origem"),
)

# Campos obrigatórios
REQUIRED_FIELDS: Tuple[str, ...] = ("chamado", "solicitante")

# ============================================================================
# LAYOUT ADM - POSIÇÕES E DIMENSÕES
# ============================================================================

ADM_Y_TOP: int = 60
ADM_LOGO_X: int = 5
ADM_LOGO_Y: int = 60
ADM_LOGO_WIDTH: int = 30
ADM_LOGO_HEIGHT: int = 15

ADM_HEADER_FIELDS: Tuple[Tuple[str, int, int, int, int, str], ...] = (
    ("RETIRADA EST:", 35, 65, 25, 10, "label"),
    ("", 35, 60, 25, 5, "value_date"),
    ("CHAMADO ESTOQUE:", 60, 65, 35, 10, "label"),
    ("", 60, 60, 35, 5, "value_chamado"),
)

# ============================================================================
# LAYOUT UNIDADE - POSIÇÕES E DIMENSÕES
# ============================================================================

UNIDADE_LOGO_X: int = 7
UNIDADE_LOGO_Y: int = 68
UNIDADE_LOGO_WIDTH: int = 22
UNIDADE_LOGO_HEIGHT: int = 9

UNIDADE_ORIGIN_DEFAULT: str = "MG80"

# ============================================================================
# CARACTERES E SEPARADORES
# ============================================================================

CSV_SEPARATOR: str = ";"
CSV_ENCODING: str = "utf-8-sig"

# Padrões (Regex) para remover do texto do produto
TEXT_REPLACEMENT_PATTERNS: Tuple[str, ...] = (
    r'^[A-Z]{2,}\d+[A-Z0-9]*\s*-\s*', # Remove códigos de localidade no início (Ex: "MG801S - ", "MG09 - ")
    r'^.*?Solicitar\s+equipamento\s*-\s*.*?\s*-\s*', # Remove prefixo com localidade (Ex: "Solicitar equipamento - MG09 - ")
    r'Solicitar\s+equipamento\s*-\s*',
    r'Solicitar\s+equipamento',
    "Já possui notebook e irá continuar utilizando na nova área",
    "Necessário fornecer ",
    "Não será necessário fornecer Micro computador/notebook.",
)

# ============================================================================
# MENSAGENS
# ============================================================================

MESSAGES: Dict[str, str] = {
    "incomplete_data": "Dados Incompletos",
    "incomplete_data_msg": "Chamado e Beneficiário são obrigatórios.",
    "empty_queue": "Fila Vazia",
    "empty_queue_msg": "Não há dados para gerar etiquetas.",
    "no_layout": "Aviso",
    "no_layout_msg": "Nenhum layout foi selecionado.",
    "file_open_warning": "Arquivo Aberto",
    "file_open_msg": (
        "Não foi possível salvar o histórico porque 'historico_etiquetas.csv' "
        "está aberto no Excel.\n\nFeche a planilha e tente gerar o PDF novamente."
    ),
    "print_success": "Impressão enviada",
    "print_manual": "Impressão Manual",
    "print_manual_msg": (
        "Não foi possível imprimir automaticamente.\n\n"
        "O PDF será aberto para impressão manual.\n\nErro: {error}"
    ),
    "pdf_generated": "PDF Gerado",
    "pdf_generated_msg": "Arquivo salvo no Desktop!\nDeseja imprimir?",
    "success": "Sucesso",
    "success_msg": "Etiquetas geradas e histórico salvo!",
    "critical_error": "Erro Crítico",
    "critical_error_msg": "Falha ao processar PDF:\n\n{error}",
}

# ============================================================================
# JIRA INTEGRATION
# ============================================================================

JIRA_BASE_URL: str = "https://servicedesk-autoglass.atlassian.net/browse"
