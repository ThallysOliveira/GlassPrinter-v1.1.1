"""
Layout UNIDADE para geração de etiquetas GlassPrinter.

Este módulo implementa o design do layout para etiquetas de envio para unidades,
com suporte a QR codes, logotipos e formatação de múltiplas informações.
"""

import io
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import qrcode
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

from core.utils import get_resource_path, safe_get_dict_value, normalize_text
from core.config import (
    QR_CODE_VERSION,
    QR_CODE_BOX_SIZE,
    QR_CODE_BORDER,
    FONT_BOLD,
    FONT_DEFAULT,
    COLOR_BACKGROUND_CELL,
    LOGO_FILE,
    JIRA_BASE_URL,
    UNIDADE_ORIGIN_DEFAULT,
    TEXT_REPLACEMENT_PATTERNS,
)


# ============================================================================
# LOGGING
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# UNIDADE LAYOUT - CONSTANTES
# ============================================================================

# Logo
LOGO_X: int = 7 * mm
LOGO_Y: int = 68 * mm
LOGO_WIDTH: int = 22 * mm
LOGO_HEIGHT: int = 9 * mm

# QR Codes
QR_SIZE: int = 11 * mm
QR_CHAMADO_X: int = 21 * mm
QR_CHAMADO_Y: int = 5.5 * mm
QR_PATRIMONIO_X: int = 68 * mm
QR_PATRIMONIO_Y: int = 5.5 * mm

# Text positions
QR_CHAMADO_LABEL_X: int = 26.5 * mm
QR_CHAMADO_LABEL_Y: int = 3.8 * mm
QR_PATRIMONIO_LABEL_X: int = 73.5 * mm
QR_PATRIMONIO_LABEL_Y: int = 3.8 * mm


# ============================================================================
# QR CODE GENERATION
# ============================================================================

def gerar_qr_unidade(texto: str) -> ImageReader:
    """
    Retorna um ImageReader com QR Code PNG para uso no ReportLab.

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

    imagem = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG")
    buffer.seek(0)

    return ImageReader(buffer)



# ============================================================================
# CELL DRAWING
# ============================================================================

def desenhar_celula(
    canvas_obj: Canvas,
    x: float,
    y: float,
    largura: float,
    altura: float,
    texto: str = "",
    preencher: bool = False,
    negrito: bool = True,
    tam_fonte: int = 8,
    alinhar_esquerda: bool = False,
) -> None:
    """
    Desenha uma célula com borda, fundo opcional e texto alinhado.

    Args:
        canvas_obj: Objeto Canvas do ReportLab.
        x: Posição X em unidades do ReportLab.
        y: Posição Y em unidades do ReportLab.
        largura: Largura da célula.
        altura: Altura da célula.
        texto: Texto a ser exibido.
        preencher: Se True, preenche a célula com cor de fundo.
        negrito: Se True, usa fonte bold.
        tam_fonte: Tamanho da fonte em pontos.
        alinhar_esquerda: Se True, alinha à esquerda; caso contrário, centraliza.
    """
    if preencher:
        canvas_obj.setFillColor(HexColor(COLOR_BACKGROUND_CELL))
        canvas_obj.rect(x, y, largura, altura, fill=1)

    canvas_obj.setFillColor(HexColor("#000000"))
    canvas_obj.setLineWidth(0.5)
    canvas_obj.rect(x, y, largura, altura, fill=0)

    fonte = FONT_BOLD if negrito else FONT_DEFAULT
    texto_str = str(texto) if texto and str(texto).lower() != "nan" else ""

    # Suporte para textos longos
    if not negrito and len(texto_str) > 35:
        estilo = ParagraphStyle("texto_long", fontName=fonte, fontSize=tam_fonte - 1, leading=tam_fonte)
        paragrafo = Paragraph(texto_str, estilo)
        paragrafo.wrapOn(canvas_obj, largura - 2 * mm, altura)
        paragrafo.drawOn(canvas_obj, x + 1.5 * mm, y + 1.2 * mm)
        return

    canvas_obj.setFont(fonte, tam_fonte)
    pos_y = y + altura / 2 - 1.2 * mm

    if alinhar_esquerda:
        canvas_obj.drawString(x + 2 * mm, pos_y, texto_str)
    else:
        canvas_obj.drawCentredString(x + largura / 2, pos_y, texto_str)


def desenhar_unidade(canvas_obj: Canvas, dados: Dict[str, Any]) -> None:
    """
    Desenha o layout de unidade para etiquetas de 100x80mm.

    O layout inclui:
    - Logotipos da empresa
    - Cabeçalho com título do formulário
    - Informações gerais (chamado, data de envio)
    - Blocos de dados (solicitante, patrimônio, produto)
    - Informações de logística (origem, forma de envio, técnico, destino)
    - QR codes de validação (chamado e patrimônio)

    Args:
        canvas_obj: Objeto Canvas do ReportLab para desenho.
        dados: Dicionário contendo os dados da etiqueta.
    """
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    # --- LOGO SECTION ---
    logo_path = get_resource_path(LOGO_FILE)
    try:
        canvas_obj.drawImage(
            logo_path,
            LOGO_X,
            LOGO_Y,
            width=LOGO_WIDTH,
            height=LOGO_HEIGHT,
            mask="auto",
        )
    except Exception as e:
        logger.warning(f"Erro ao carregar logotipo: {e}")
        canvas_obj.setFont(FONT_BOLD, 8)
        canvas_obj.drawString(LOGO_X, LOGO_Y + 4 * mm, "AUTOGLASS")

    # --- HEADER SECTION ---
    desenhar_celula(
        canvas_obj, 33 * mm, 71 * mm, 64 * mm, 6 * mm,
        "FORMULÁRIO DE ENVIO - UNIDADE",
        preencher=True,
        tam_fonte=8,
    )

    desenhar_celula(
        canvas_obj, 33 * mm, 68 * mm, 32 * mm, 3 * mm,
        "CHAMADO",
        preencher=True,
        tam_fonte=6,
    )
    desenhar_celula(
        canvas_obj, 65 * mm, 68 * mm, 32 * mm, 3 * mm,
        texto=safe_get_dict_value(dados, "chamado"),
        negrito=False,
        tam_fonte=7,
    )

    desenhar_celula(
        canvas_obj, 33 * mm, 65 * mm, 32 * mm, 3 * mm,
        "DATA DE ENVIO",
        preencher=True,
        tam_fonte=6,
    )
    desenhar_celula(
        canvas_obj, 65 * mm, 65 * mm, 32 * mm, 3 * mm,
        texto=data_hoje,
        negrito=False,
        tam_fonte=7,
    )

    # --- DATA BLOCKS SECTION ---
    blocos = [
        ("SOLICITANTE", "solicitante"),
        ("PATRIMÔNIO", "patrimonio"),
        ("PRODUTO", "produto"),
    ]
    y_blocos = [59, 53, 47]

    for (titulo, chave), y in zip(blocos, y_blocos):
        desenhar_celula(
            canvas_obj, 3 * mm, y * mm, 30 * mm, 6 * mm,
            titulo,
            preencher=True,
            tam_fonte=7.5,
        )

        if chave == "solicitante":
            valor = safe_get_dict_value(dados, "solicitante") or safe_get_dict_value(dados, "beneficiario")
        else:
            valor = safe_get_dict_value(dados, chave)

        valor_str = str(valor) if valor and str(valor).lower() != "nan" else ""

        if chave == "produto":
            valor_limpo = normalize_text(valor_str, TEXT_REPLACEMENT_PATTERNS)
            quantidade = safe_get_dict_value(dados, "quantidade", "")
            valor_str = f"{quantidade} - {valor_limpo}".strip(" -")

        desenhar_celula(
            canvas_obj, 33 * mm, y * mm, 64 * mm, 6 * mm,
            texto=valor_str,
            negrito=False,
            alinhar_esquerda=True,
            tam_fonte=7.5,
        )

    # --- LOGISTICS SECTION ---
    desenhar_celula(
        canvas_obj, 3 * mm, 41 * mm, 20 * mm, 6 * mm,
        "ORIGEM",
        preencher=True,
        tam_fonte=7.5,
    )
    desenhar_celula(
        canvas_obj, 23 * mm, 41 * mm, 74 * mm, 6 * mm,
        texto=UNIDADE_ORIGIN_DEFAULT,
        negrito=False,
        alinhar_esquerda=True,
        tam_fonte=7.5,
    )

    desenhar_celula(
        canvas_obj, 3 * mm, 35 * mm, 47 * mm, 6 * mm,
        "FORMA DE ENVIO",
        preencher=True,
        tam_fonte=7.5,
    )
    desenhar_celula(
        canvas_obj, 50 * mm, 35 * mm, 47 * mm, 6 * mm,
        "TÉCNICO",
        preencher=True,
        tam_fonte=7.5,
    )

    desenhar_celula(
        canvas_obj, 3 * mm, 27 * mm, 47 * mm, 8 * mm,
        texto=safe_get_dict_value(dados, "forma_envio", "LOGÍSTICA / CARRETA"),
        negrito=False,
        tam_fonte=7.5,
    )
    desenhar_celula(
        canvas_obj, 50 * mm, 27 * mm, 47 * mm, 8 * mm,
        texto=safe_get_dict_value(dados, "tecnico"),
        negrito=False,
        alinhar_esquerda=True,
        tam_fonte=7.5,
    )

    desenhar_celula(
        canvas_obj, 3 * mm, 21 * mm, 25 * mm, 6 * mm,
        "DESTINO",
        preencher=True,
        tam_fonte=7.5,
    )
    desenhar_celula(
        canvas_obj, 28 * mm, 21 * mm, 69 * mm, 6 * mm,
        texto=safe_get_dict_value(dados, "destino"),
        negrito=False,
        alinhar_esquerda=True,
        tam_fonte=7.5,
    )

    # --- QR CODES VALIDATION SECTION ---
    desenhar_celula(
        canvas_obj, 3 * mm, 17 * mm, 94 * mm, 4 * mm,
        "VALIDAÇÃO QRCODE",
        preencher=True,
        tam_fonte=6,
    )

    # QR Code boxes
    canvas_obj.rect(3 * mm, 3 * mm, 47 * mm, 14 * mm)
    canvas_obj.rect(50 * mm, 3 * mm, 47 * mm, 14 * mm)

    # Issue QR Code
    chamado_cod = safe_get_dict_value(dados, "chamado", "N/A")
    link_jira = f"{JIRA_BASE_URL}/{chamado_cod}"
    canvas_obj.drawImage(
        gerar_qr_unidade(link_jira),
        QR_CHAMADO_X,
        QR_CHAMADO_Y,
        width=QR_SIZE,
        height=QR_SIZE,
    )
    canvas_obj.setFont(FONT_BOLD, 6)
    canvas_obj.drawCentredString(QR_CHAMADO_LABEL_X, QR_CHAMADO_LABEL_Y, "CHAMADO (JIRA)")

    # Patrimonio QR Code
    patrimonio = safe_get_dict_value(dados, "patrimonio", "N/A")
    canvas_obj.drawImage(
        gerar_qr_unidade(patrimonio),
        QR_PATRIMONIO_X,
        QR_PATRIMONIO_Y,
        width=QR_SIZE,
        height=QR_SIZE,
    )
    canvas_obj.drawCentredString(QR_PATRIMONIO_LABEL_X, QR_PATRIMONIO_LABEL_Y, "PATRIMÔNIO")
