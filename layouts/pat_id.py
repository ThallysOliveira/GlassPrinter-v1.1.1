"""
Layout PAT ID para identificação de caixas (50x40mm).
"""

import logging
from typing import Dict, Any
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128

from core.utils import get_resource_path, safe_get_dict_value, normalize_text
from core.config import (
    FONT_BOLD,
    FONT_THIN,
    FONT_SEMIBOLD,
    LOGO_FILE,
    LABEL_SIZE_PAT_ID,
    TEXT_REPLACEMENT_PATTERNS,
)

logger = logging.getLogger(__name__)

def desenhar_pat_id(canvas_obj: Canvas, dados: Dict[str, Any]) -> None:
    """
    Desenha o layout PAT ID em uma etiqueta compacta de 50x40mm.
    """
    width, height = LABEL_SIZE_PAT_ID
    
    # --- LOGO SECTION ---
    logo_path = get_resource_path(LOGO_FILE)
    
    # Configuração para centralização (Icone + Texto)
    font_size = 9
    canvas_obj.setFont(FONT_SEMIBOLD, font_size)
    
    # Cálculo da largura total para centralizar o bloco no centro superior
    texto_principal = "AUTOGLASS"
    texto_secundario = "GRUPO"
    largura_texto = canvas_obj.stringWidth(texto_principal, FONT_SEMIBOLD, font_size)
    largura_icone = 10 * mm
    espacamento = 0 * mm
    largura_total_bloco = largura_icone + espacamento + largura_texto
    start_x = (width - largura_total_bloco) / 2

    try:
        canvas_obj.drawImage(logo_path, start_x, 31.5*mm, width=largura_icone, height=6.5*mm, mask="auto")
    except Exception:
        pass

    # Texto alinhado (G em cima do A) e centralizado como bloco
    text_x = start_x + largura_icone + espacamento
    
    canvas_obj.setFont(FONT_THIN, font_size)
    canvas_obj.drawString(text_x, 34.3*mm, texto_secundario)
    
    canvas_obj.setFont(FONT_SEMIBOLD, font_size)
    canvas_obj.drawString(text_x, 31.5*mm, texto_principal)

    # Linha separadora superior
    canvas_obj.setLineWidth(1)
    canvas_obj.line(3*mm, 30*mm, 47*mm, 30*mm)

    # --- PRODUTO ---
    produto_bruto = safe_get_dict_value(dados, "produto")
    produto_limpo = normalize_text(produto_bruto, TEXT_REPLACEMENT_PATTERNS)
    
    canvas_obj.setFont(FONT_BOLD, 11)
    # Limita o texto para não estourar a etiqueta pequena
    display_text = produto_limpo[:25] + "..." if len(produto_limpo) > 25 else produto_limpo
    canvas_obj.drawCentredString(width/2, 25*mm, display_text.upper())

    # --- CÓDIGO DE BARRAS (PATRIMÔNIO) ---
    patrimonio = safe_get_dict_value(dados, "patrimonio", "000000")
    try:
        # Usamos Code 128 (1D) conforme o print
        barcode = code128.Code128(patrimonio, barHeight=10*mm, barWidth=0.3*mm)
        bw = barcode.width
        # Centraliza o código de barras
        barcode.drawOn(canvas_obj, (width - bw)/2, 12*mm)
    except Exception as e:
        logger.error(f"Erro ao gerar código de barras PAT ID: {e}")

    # Texto do patrimônio logo abaixo das barras
    canvas_obj.setFont(FONT_BOLD, 12)
    canvas_obj.drawCentredString(width/2, 7.5*mm, patrimonio)

    # --- FOOTER ---
    # Linha separadora inferior
    canvas_obj.setLineWidth(0.8)
    canvas_obj.line(3*mm, 6*mm, 47*mm, 6*mm)

    canvas_obj.setFont(FONT_BOLD, 7)
    canvas_obj.drawCentredString(width/2, 2.5*mm, "TECNOLOGIA DA INFORMAÇÃO")

    # Moldura externa opcional (ajuda no corte se necessário)
    canvas_obj.setLineWidth(0.2)
    canvas_obj.rect(1*mm, 1*mm, 48*mm, 38*mm)

if __name__ == "__main__":
    # Bloco para teste rápido do layout sem abrir a interface principal
    import os
    import sys
    # Adiciona o diretório raiz ao path para permitir importação do 'core'
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    from reportlab.pdfgen import canvas
    
    test_pdf = "teste_pat_id.pdf"
    c = canvas.Canvas(test_pdf, pagesize=LABEL_SIZE_PAT_ID)
    
    dados_teste = {
        "produto": "Camera VHD 3130 B G6",
        "patrimonio": "175514"
    }
    
    desenhar_pat_id(c, dados_teste)
    c.save()
    print(f"PDF de teste gerado com sucesso: {test_pdf}")