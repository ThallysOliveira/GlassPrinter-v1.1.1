"""
Exemplo de uso do transformador Power Query.

Demonstra como carregar arquivos Excel, aplicar as transformações
e exportar os dados processados.
"""

import logging
from pathlib import Path
from core.data_transformer import transform_power_query, export_to_excel

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """
    Exemplo de uso do transformador.
    
    IMPORTANTE: Atualize os caminhos dos arquivos Excel para os locais corretos.
    """
    
    # ========================================================================
    # CONFIGURAR CAMINHOS DOS ARQUIVOS
    # ========================================================================
    
    kit_promovido_path = r"C:\Users\thallys.fernandes\Documents\Teste etiqueta\kit.colaborador.promovido.xlsx"
    kit_novo_path = r"C:\Users\thallys.fernandes\Documents\Teste etiqueta\kit.novo.colaborador.xlsx"
    solicitar_equipamento_path = r"C:\Users\thallys.fernandes\Documents\Teste etiqueta\Solicitar.equipamento.xlsx"
    
    # Pasta de saída
    output_folder = Path(__file__).parent.parent / "output"
    output_folder.mkdir(exist_ok=True)
    output_path = output_folder / "dados_transformados.xlsx"
    
    # ========================================================================
    # EXECUTAR TRANSFORMAÇÃO
    # ========================================================================
    
    try:
        logger.info("Iniciando transformação dos dados...")
        
        # Transforma dados
        df = transform_power_query(
            kit_promovido_path,
            kit_novo_path,
            solicitar_equipamento_path,
        )
        
        # Exibe informações
        logger.info(f"Total de registros: {len(df)}")
        logger.info(f"Colunas: {list(df.columns)}")
        
        # Exibe primeiras linhas
        logger.info("\nPrimeiros registros:")
        logger.info(df.head(10).to_string())
        
        # Exporta para Excel
        export_to_excel(df, str(output_path))
        
        logger.info(f"\n✓ Transformação concluída com sucesso!")
        logger.info(f"Arquivo exportado: {output_path}")
        
        return df
        
    except Exception as e:
        logger.error(f"Erro na transformação: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    df = main()
