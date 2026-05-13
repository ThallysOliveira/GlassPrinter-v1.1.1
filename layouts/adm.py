"""
Layout ADM para geração de etiquetas GlassPrinter.

Este módulo implementa o design do layout para etiquetas de estoque ADM,
com suporte a QR codes e logotipos.
"""

import io
import logging
from typing import Dict, Any
from datetime import datetime

import qrcode
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

from core.utils import get_resource_path, safe_get_dict_value, normalize_text
from core.config import (
    QR_CODE_VERSION,
    QR_CODE_BOX_SIZE,
    QR_CODE_BORDER,
    FONT_BOLD,
    FONT_DEFAULT,
    LOGO_FILE,
    JIRA_BASE_URL,
    TEXT_REPLACEMENT_PATTERNS,
)


# ============================================================================
# LOGGING
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# ADM LAYOUT - CONSTANTES
# ============================================================================

# Posições e dimensões
Y_TOP: int = 60
LOGO_X: int = 5 * mm
LOGO_Y: int = 60 * mm
LOGO_WIDTH: int = 22 * mm
LOGO_HEIGHT: int = 15 * mm

# Cells
CELL_HEADER_DATE_X: int = 27 * mm
CELL_HEADER_DATE_Y: int = 60 * mm
CELL_HEADER_DATE_WIDTH: int = 33 * mm
CELL_HEADER_DATE_HEIGHT: int = 5 * mm

CELL_HEADER_CHAMADO_X: int = 60 * mm
CELL_HEADER_CHAMADO_Y: int = 60 * mm
CELL_HEADER_CHAMADO_WIDTH: int = 35 * mm
CELL_HEADER_CHAMADO_HEIGHT: int = 5 * mm

# QR Code
QR_SIZE: int = 18 * mm
QR_X: int = 12 * mm
QR_Y: int = 8 * mm

# Filial ID
FILIAL_ID_X: int = 55 * mm
FILIAL_ID_Y: int = 15 * mm
FILIAL_ID_FONT_SIZE: int = 16

# Moldura
MOLDURA_X: int = 5 * mm
MOLDURA_WIDTH: int = 90 * mm
MOLDURA_Y: int = 5 * mm


# ============================================================================
# QR CODE GENERATION
# ============================================================================

def gerar_qr_adm(texto: str) -> ImageReader:
    """
    Gera um QR Code em PNG e retorna um ImageReader para o ReportLab.

    Args:
        texto: Texto a ser codificado no QR code.

    Returns:
        ImageReader do ReportLab contendo a imagem PNG do QR code.
    """
    if not texto or str(texto).lower() == "nan":
        texto = "N/A"

    qr = qrcode.QRCode(
        version=QR_CODE_VERSION,
        box_size=QR_CODE_BOX_SIZE,
        border=QR_CODE_BORDER,
    )
    qr.add_data(str(texto))
    qr.make(fit=True)

    imagem_qr = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    imagem_qr.save(buffer, format="PNG")
    buffer.seek(0)

    return ImageReader(buffer)


# ============================================================================
# CELL DRAWING
# ============================================================================

def desenhar_celula_adm(
    canvas_obj: Canvas,
    x: float,
    y: float,
    largura: float,
    altura: float,
    texto: str,
    negrito: bool = True,
    tam_fonte: int = 8,
    alinhar_esquerda: bool = True,
    com_borda: bool = True,
) -> None:
    """
    Desenha um campo retangular com texto alinhado à esquerda ou centralizado.

    Args:
        canvas_obj: Objeto Canvas do ReportLab.
        x: Posição X em unidades do ReportLab.
        y: Posição Y em unidades do ReportLab.
        largura: Largura da célula.
        altura: Altura da célula.
        texto: Texto a ser exibido.
        negrito: Se True, usa fonte bold.
        tam_fonte: Tamanho da fonte em pontos.
        alinhar_esquerda: Se True, alinha à esquerda; caso contrário, centraliza.
        com_borda: Se True, desenha o retângulo de borda.
    """
    if com_borda:
        canvas_obj.setLineWidth(0.5)
        canvas_obj.rect(x, y, largura, altura)

    fonte = FONT_BOLD if negrito else FONT_DEFAULT
    canvas_obj.setFont(fonte, tam_fonte)

    texto_str = str(texto) if texto and str(texto).lower() != "nan" else ""
    pos_y = y + altura / 2 - 1 * mm

    if alinhar_esquerda:
        canvas_obj.drawString(x + 2 * mm, pos_y, texto_str)
    else:
        canvas_obj.drawCentredString(x + largura / 2, pos_y, texto_str)


def desenhar_adm(canvas_obj: Canvas, dados: Dict[str, Any]) -> None:
    """
    Desenha o layout ADM completo em uma etiqueta de 100x80mm.

    O layout inclui:
    - Logotipos da empresa
    - Informações de cabeçalho (data e chamado)
    - Campos de dados (setor, destino, beneficiário, técnico)
    - Informações de produto
    - QR code com link para Jira
    - ID da filial

    Args:
        canvas_obj: Objeto Canvas do ReportLab para desenho.
        dados: Dicionário contendo os dados da etiqueta.
    """
    # --- LOGO SECTION ---
    canvas_obj.rect(LOGO_X, LOGO_Y, LOGO_WIDTH, LOGO_HEIGHT)
    logo_path = get_resource_path(LOGO_FILE)

    try:
        canvas_obj.drawImage(
            logo_path,
            LOGO_X + 1 * mm,
            LOGO_Y + 2.5 * mm,
            width=LOGO_WIDTH - 2 * mm,
            height=LOGO_HEIGHT - 5 * mm,
            mask="auto",
        )
    except Exception as e:
        logger.warning(f"Erro ao carregar logotipo: {e}")
        canvas_obj.setFont(FONT_BOLD, 10)
        canvas_obj.drawCentredString(LOGO_X + LOGO_WIDTH / 2, LOGO_Y + 6 * mm, "AUTOGLASS")

    # --- HEADER SECTION ---
    desenhar_celula_adm(canvas_obj, 27 * mm, 65 * mm, 33 * mm, 10 * mm, "RETIRADA EST:", tam_fonte=7)
    desenhar_celula_adm(
        canvas_obj,
        27 * mm,
        Y_TOP * mm,
        33 * mm,
        5 * mm,
        datetime.now().strftime("%d/%m/%Y"),
        negrito=False,
    )
    desenhar_celula_adm(canvas_obj, 60 * mm, 65 * mm, 35 * mm, 10 * mm, "CHAMADO ESTOQUE:", tam_fonte=7)
    desenhar_celula_adm(
        canvas_obj,
        CELL_HEADER_CHAMADO_X,
        CELL_HEADER_CHAMADO_Y,
        CELL_HEADER_CHAMADO_WIDTH,
        CELL_HEADER_CHAMADO_HEIGHT,
        safe_get_dict_value(dados, "chamado"),
        negrito=False,
    )

    # --- DATA FIELDS SECTION ---
    y_pos = Y_TOP - 5
    campos = [
        ("CCeSETOR:", safe_get_dict_value(dados, "setor")),
        ("DESTINO:", safe_get_dict_value(dados, "destino")),
        (
            "BENEFICIÁRIO:",
            safe_get_dict_value(dados, "solicitante") or safe_get_dict_value(dados, "beneficiario"),
        ),
        ("TÉCNICO:", safe_get_dict_value(dados, "tecnico")),
    ]

    for label, valor in campos:
        desenhar_celula_adm(canvas_obj, 5 * mm, y_pos * mm, 22 * mm, 5 * mm, label, tam_fonte=7.5)
        desenhar_celula_adm(
            canvas_obj,
            27 * mm,
            y_pos * mm,
            68 * mm,
            5 * mm,
            valor,
            negrito=False,
            tam_fonte=7.5,
        )
        y_pos -= 5

    # --- PRODUCT/EQUIPMENT SECTION ---
    produto_bruto = safe_get_dict_value(dados, "produto")
    produto_limpo = normalize_text(produto_bruto, TEXT_REPLACEMENT_PATTERNS)
    qtd = safe_get_dict_value(dados, "quantidade", "")
    texto_item = f"{qtd} - {produto_limpo}".strip(" -")

    # Moldura única para a seção de equipamentos (sem linha divisória no meio)
    canvas_obj.rect(5 * mm, (y_pos - 5) * mm, 90 * mm, 10 * mm)

    # Título da seção centralizado ocupando a largura total (90mm)
    desenhar_celula_adm(
        canvas_obj, 5 * mm, y_pos * mm, 90 * mm, 5 * mm, "EQUIPAMENTOS:", 
        tam_fonte=7.5, alinhar_esquerda=False, com_borda=False
    )
    
    # Joga o campo onde vai o nome do produto para a linha de baixo
    y_pos -= 5

    desenhar_celula_adm(
        canvas_obj, 5 * mm, y_pos * mm, 90 * mm, 5 * mm, texto_item, 
        negrito=True, tam_fonte=8, alinhar_esquerda=False, com_borda=False
    )

    # --- QR CODE AND FILIAL ID SECTION ---
    altura_moldura = (y_pos - 5) * mm
    canvas_obj.rect(MOLDURA_X, MOLDURA_Y, MOLDURA_WIDTH, altura_moldura)

    chamado_str = safe_get_dict_value(dados, "chamado")
    link_jira = f"{JIRA_BASE_URL}/{chamado_str}"

    # QR Code
    canvas_obj.drawImage(gerar_qr_adm(link_jira), QR_X, QR_Y, width=QR_SIZE, height=QR_SIZE)

    # Filial ID
    if dados.get("destino"):
        filial_id = str(dados.get("destino")).strip().upper()[:4]
    else:
        filial_id = chamado_str or "N/A"

    canvas_obj.setFont(FONT_BOLD, FILIAL_ID_FONT_SIZE)
    canvas_obj.drawString(FILIAL_ID_X, FILIAL_ID_Y, filial_id)
