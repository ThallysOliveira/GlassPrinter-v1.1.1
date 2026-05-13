"""
Engine de geração de PDF e gerenciamento de dados para a aplicação GlassPrinter.

Este módulo é responsável por:
- Geração de arquivos PDF com as etiquetas
- Gestão de backup de dados
- Integração com os layouts específicos
- Comunicação com o sistema de impressão
"""

import os
import logging
import re
import ctypes
import io
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from core.config import (
    LABEL_SIZE,
    LABEL_SIZE_PAT_ID,
    LAYOUT_PAT_ID,
    LAYOUT_GATI,
    LAYOUT_GRID_CONFIG,
    CSV_SEPARATOR,
    CSV_ENCODING,
    HISTORY_FILES,
    JIRA_BASE_URL,
    FORM_FIELDS,
    SMART_MAPPING,
    TEXT_REPLACEMENT_PATTERNS,
)
from core.utils import (
    get_default_output_path,
    create_backup_filename,
    ensure_file_not_locked,
    format_jira_link,
    motor_de_mapeamento,
    normalize_text,
    processar_sufixo_notebook,
)
from core.data_transformer import transform_power_query, export_to_excel

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# PDF ENGINE
# ============================================================================

class PDFEngine:
    """
    Engine responsável pela geração de arquivos PDF com etiquetas.

    Attributes:
        output_dir (Path): Diretório de saída para arquivos PDF e backups.
        layout_module (module): Módulo com funções de desenho específicas do layout.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Inicializa o PDFEngine.

        Args:
            output_dir: Diretório de saída. Se None, usa o diretório padrão (ao lado do executável).
        """
        self.output_dir = output_dir or get_default_output_path()
        self.layout_module = None

    def set_layout(self, layout_name: str) -> None:
        """
        Define o módulo de layout a ser utilizado.

        Args:
            layout_name: Nome do layout ('adm' ou 'unidade').

        Raises:
            ImportError: Se o módulo de layout não puder ser importado.
        """
        try:
            if layout_name == "adm":
                from layouts.adm import desenhar_adm
                self.draw_function = desenhar_adm
            elif layout_name == "unidade":
                from layouts.unidade import desenhar_unidade
                self.draw_function = desenhar_unidade
            elif layout_name == "pat_id":
                from layouts.pat_id import desenhar_pat_id
                self.draw_function = desenhar_pat_id
            elif layout_name == "gati":
                from layouts.pat_id import desenhar_pat_id
                self.draw_function = desenhar_pat_id
            else:
                raise ValueError(f"Layout desconhecido: {layout_name}")

            logger.info(f"Layout '{layout_name}' carregado com sucesso")

        except ImportError as e:
            logger.error(f"Erro ao importar layout '{layout_name}': {e}")
            raise

    def generate_pdf(
        self,
        records: List[Dict[str, str]],
        layout_name: str,
        overwrite: bool = False,
    ) -> str:
        """
        Gera um arquivo PDF com as etiquetas baseado nos registros fornecidos.

        Args:
            records: Lista de dicionários com dados dos registros.
            layout_name: Tipo de layout a usar ('adm' ou 'unidade').
            overwrite: Se True, usa um nome de arquivo fixo para evitar acúmulo.

        Returns:
            Caminho completo do arquivo PDF gerado.

        Raises:
            ValueError: Se a lista de registros estiver vazia.
            Exception: Em caso de erro durante a geração do PDF.
        """
        if not records:
            raise ValueError("Nenhum registro fornecido para geração de PDF")

        self.set_layout(layout_name)

        if overwrite:
            filename = f"Ultima_Etiqueta_{layout_name.upper()}"
        else:
            filename = create_backup_filename(layout_name, "%Y%m%d_%H%M%S")
            
        filepath = self.output_dir / f"{filename}.pdf"
        
        # Configurações de grade e dimensões base
        base_size = LABEL_SIZE_PAT_ID if layout_name in [LAYOUT_PAT_ID, LAYOUT_GATI] else LABEL_SIZE
        grid_cfg = LAYOUT_GRID_CONFIG.get(layout_name, {"cols": 1, "gap": 0})
        num_cols = grid_cfg["cols"]
        h_gap = grid_cfg["gap"] * mm
        
        # Calcula a largura total da página (uma "linha" do rolo)
        page_width = (base_size[0] * num_cols) + (h_gap * (num_cols - 1))
        page_height = base_size[1]

        try:
            c = canvas.Canvas(str(filepath), pagesize=(page_width, page_height))

            for i, record in enumerate(records):
                col = i % num_cols
                
                c.saveState()
                # Translada o sistema de coordenadas para a posição da etiqueta atual na linha
                x_offset = col * (base_size[0] + h_gap)
                c.translate(x_offset, 0)
                
                self.draw_function(c, record)
                c.restoreState()
                
                # Muda de página (linha do rolo) se preencheu as colunas ou se for o último registro
                if col == num_cols - 1 or i == len(records) - 1:
                    c.showPage()

            c.save()
            logger.info(f"PDF gerado com sucesso: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {e}")
            raise

    def get_preview_image(self, record: Dict[str, str], layout_name: str) -> Optional[Any]:
        """
        Gera uma imagem PIL de pré-visualização para um único registro.
        """
        try:
            import fitz  # PyMuPDF
            from PIL import Image
            
            self.set_layout(layout_name)
            buffer = io.BytesIO()
            
            # Determina o tamanho da etiqueta para o canvas
            base_size = LABEL_SIZE_PAT_ID if layout_name in [LAYOUT_PAT_ID, LAYOUT_GATI] else LABEL_SIZE
            
            # Desenha a etiqueta em um PDF temporário na memória
            c = canvas.Canvas(buffer, pagesize=base_size)
            self.draw_function(c, record)
            c.save()
            
            # Converte o PDF em imagem usando PyMuPDF
            buffer.seek(0)
            doc = fitz.open(stream=buffer.read(), filetype="pdf")
            page = doc.load_page(0)
            # Zoom de 2x para garantir nitidez na tela
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return img
            
        except Exception as e:
            logger.error(f"Erro ao gerar preview: {e}")
            return None

    def save_backup(self, records: List[Dict[str, str]], layout_name: Optional[str] = None) -> bool:
        """
        Salva um backup dos registros em arquivo CSV.

        Args:
            records: Lista de dicionários com os dados a salvar.
            layout_name: Nome do layout utilizado ('adm' ou 'unidade').

        Returns:
            True se o backup foi salvo com sucesso, False caso contrário.

        Raises:
            PermissionError: Se o arquivo de histórico estiver aberto.
        """
        if not records:
            logger.debug("Nenhum registro para backup")
            return True

        # Garante que o diretório de saída existe
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Define o arquivo de destino baseado no layout
        nome_arquivo = HISTORY_FILES.get(layout_name, "historico_geral.csv") # type: ignore
        backup_file = self.output_dir / nome_arquivo

        try:
            df = pd.DataFrame(records)
            df["data_processamento"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            df["layout"] = layout_name or "desconhecido"

            # Padroniza o nome para o Histórico (solicitante -> beneficiario)
            if "solicitante" in df.columns:
                df = df.rename(columns={"solicitante": "beneficiario"})

            # Seleciona colunas pertinentes ao layout específico para manter o CSV limpo
            if layout_name in ["pat_id", "gati"]:
                cols_historico = ["layout", "patrimonio", "produto", "origem", "data_processamento"]
            elif layout_name == "adm":
                cols_historico = ["layout", "chamado", "data_retirada", "tecnico", "beneficiario", "destino", "setor", "produto", "quantidade", "data_processamento"]
            else:
                cols_historico = [
                    "layout", "chamado", "data_retirada", "patrimonio", "tecnico",
                    "beneficiario", "destino", "setor", "produto",
                    "quantidade", "forma_envio", "origem", "data_processamento"
                ]

            # Garante que todas as colunas existam para evitar erro de seleção
            for col in cols_historico:
                if col not in df.columns:
                    df[col] = ""

            # Se for layout ADM, limpa o campo forma_envio no backup pois não é pertinente
            if layout_name == "adm" and "forma_envio" in df.columns:
                df["forma_envio"] = ""

            # Filtra e reordena as colunas
            df = df[cols_historico]

            mode = "a" if backup_file.exists() else "w"
            header = not backup_file.exists()

            # Tenta verificar o bloqueio com retentativa interna
            if not ensure_file_not_locked(str(backup_file), max_retries=5):
                raise PermissionError(
                    f"Arquivo de histórico '{nome_arquivo}' está aberto em outro programa"
                )

            df.to_csv(
                str(backup_file),
                mode=mode,
                header=header,
                index=False,
                sep=CSV_SEPARATOR,
                encoding=CSV_ENCODING,
            )

            logger.info(f"Backup salvo em: {backup_file}")
            return True

        except PermissionError as e:
            logger.error(f"Permissão negada ao salvar backup: {e}")
            raise

        except Exception as e:
            logger.error(f"Erro ao salvar backup: {e}")
            return False

    def importar_e_consolidar(self, caminhos_arquivos: list) -> List[Dict[str, str]]:
        """
        Importa e consolida dados usando o novo módulo data_transformer (Power Query).
        
        Suporta dois modos:
        1. Modo Power Query: Se contiver os 3 arquivos específicos
        2. Modo Genérico: Outros arquivos Excel/CSV
        
        Args:
            caminhos_arquivos: Lista de caminhos dos arquivos.
            
        Returns:
            Lista de dicionários com dados consolidados.
        """
        # 1. Verifica se são os 3 arquivos do Power Query
        nomes_arquivos = [Path(c).name.lower() for c in caminhos_arquivos]
        
        # Identificação flexível por palavras-chave
        e_power_query = any(kw in n for n in nomes_arquivos for kw in ["promovido", "kit.novo", "solicitar", "equipamento"])
        
        if e_power_query:
            return self._importar_com_power_query(caminhos_arquivos)
        return self._importar_modo_generico(caminhos_arquivos)

    def _importar_com_power_query(self, caminhos_arquivos: list) -> List[Dict[str, str]]:
        """
        Importa dados usando o módulo data_transformer (Power Query).
        
        Procura pelos 3 arquivos específicos:
        - kit.colaborador.promovido.xlsx
        - kit.novo.colaborador.xlsx
        - Solicitar.equipamento.xlsx
        """
        try:
            # Encontra cada arquivo
            kit_promovido = next((c for c in caminhos_arquivos if "promovido" in Path(c).name.lower()), None)
            kit_novo = next((c for c in caminhos_arquivos if "novo" in Path(c).name.lower()), None)
            solicitar_eq = next((c for c in caminhos_arquivos if ("solicitar" in Path(c).name.lower() or "equipamento" in Path(c).name.lower())), None)
            
            logger.info("Iniciando importação com Power Query...")

            registros: List[Dict[str, str]] = []
            outros_arquivos = [
                c for c in caminhos_arquivos if c not in {kit_promovido, kit_novo, solicitar_eq}
            ]

            if kit_promovido or kit_novo or solicitar_eq:
                if kit_promovido:
                    logger.info(f"  Kit Promovido: {Path(kit_promovido).name}")
                if kit_novo:
                    logger.info(f"  Kit Novo: {Path(kit_novo).name}")
                if solicitar_eq:
                    logger.info(f"  Solicitar Equipamento: {Path(solicitar_eq).name}")

                df = transform_power_query(kit_promovido, kit_novo, solicitar_eq)

                if not df.empty:
                    logger.info(f"Power Query processou {len(df)} registros")

                    # Converte DataFrame para lista de dicionários
                    # Padroniza os nomes das colunas para o formato esperado por FORM_FIELDS
                    df_padrao = df.copy()

                    # Mapeamento: Nome Power Query → Nome usado no app
                    rename_map = {
                        'Chamado': 'chamado',
                        'Nome Completo': 'solicitante',  # Usado como "Beneficiário" na UI
                        'Centro de Custo': 'setor',      # Usado como "Setor/CC" na UI
                        'Equipamentos': 'produto',
                        'Destino': 'destino',
                        'Relator': 'tecnico',
                        'Origem': 'origem',
                        'Data de retirada': 'data_retirada',
                    }

                    # Aplica mapeamento
                    for old_name, new_name in rename_map.items():
                        if old_name in df_padrao.columns:
                            df_padrao[new_name] = df_padrao[old_name]

                    # Função para extrair quantidade do equipamento
                    def extrair_quantidade(produto_str):
                        """
                        Extrai quantidade do início do equipamento.
                        Se começar com número (ex: "2 - Monitor"), retorna vazio.
                        Se não começar com número, retorna "1".
                        """
                        if not produto_str or pd.isna(produto_str):
                            return "1"

                        produto_str = str(produto_str).strip()
                        match = re.match(r'^(\d+)\s*-', produto_str)

                        if match:
                            return ""
                        return "1"

                    required_fields = {
                        'chamado': '',
                        'solicitante': '',
                        'setor': '',
                        'produto': '',
                        'destino': '',
                        'quantidade': '1',
                        'forma_envio': 'LOGÍSTICA / CARRETA',
                        'tecnico': '',
                        'patrimonio': '',
                    }

                    for field, default in required_fields.items():
                        if field not in df_padrao.columns:
                            df_padrao[field] = default
                        else:
                            df_padrao[field] = df_padrao[field].astype(str).fillna(default)

                    if 'produto' in df_padrao.columns:
                        df_padrao['quantidade'] = df_padrao['produto'].apply(extrair_quantidade)

                    for col in ['Chamado', 'Nome Completo', 'Relator', 'Centro de Custo', 'Equipamentos', 'Destino', 'Origem']:
                        if col not in df_padrao.columns:
                            df_padrao[col] = ''

                    registros.extend(df_padrao.to_dict('records'))
                else:
                    logger.warning("Power Query retornou DataFrame vazio")

            if outros_arquivos:
                logger.info(f"Processando {len(outros_arquivos)} arquivo(s) adicionais em modo genérico")
                registros.extend(self._importar_modo_generico(outros_arquivos))

            if not registros:
                logger.warning("Nenhum registro foi carregado no modo Power Query")

            logger.info(f"Importação final com Power Query: {len(registros)} registros")
            return registros
            
        except Exception as e:
            logger.error(f"Erro ao importar com Power Query: {e}", exc_info=True)
            raise

    def _importar_modo_generico(self, caminhos_arquivos: list) -> List[Dict[str, str]]:
        """
        Importa dados em modo genérico (compatibilidade com arquivos antigos).
        """
        todos_os_dados = []

        for caminho in caminhos_arquivos:
            try:
                logger.info(f"Processando arquivo genérico: {Path(caminho).name}")
                
                # 1. Leitura bruta
                df_bruto = pd.read_excel(caminho) 
                
                # 2. Mapeamento automático (Sem tela de configuração)
                df_limpo = motor_de_mapeamento(df_bruto, SMART_MAPPING)
                
                # Garante que todos os campos do formulário existam no dataframe
                campos_necessarios = [campo for _, campo in FORM_FIELDS]
                for campo in campos_necessarios:
                    if campo not in df_limpo.columns:
                        if campo == "quantidade":
                            df_limpo[campo] = "1"
                        elif campo == "forma_envio":
                            df_limpo[campo] = "LOGÍSTICA / CARRETA"
                        else:
                            df_limpo[campo] = ""
                    else:
                        # Limpa valores nulos se a coluna existir mas estiver vazia
                        df_limpo[campo] = df_limpo[campo].fillna("")

                # Adiciona o nome do arquivo como origem
                df_limpo['origem'] = Path(caminho).name
                
                # 3. Expansão de itens (Separados por vírgula no Jira)
                if 'produto' in df_limpo.columns:
                    df_limpo = df_limpo.assign(produto=df_limpo['produto'].str.split(',')).explode('produto')
                
                # 4. Aplicação de Sufixos (ADM/DEV) e Normalização de Texto
                # Pegamos o resumo original para decidir se é ADM ou DEV
                resumo_orig = next((df_bruto[c] for c in df_bruto.columns if str(c).lower().strip() == "resumo"), None)

                if 'produto' in df_limpo.columns:
                    df_limpo['produto'] = df_limpo.apply(
                        lambda row: processar_sufixo_notebook(
                            normalize_text(row.get('produto', ''), TEXT_REPLACEMENT_PATTERNS),
                            str(resumo_orig.iloc[row.name]) if resumo_orig is not None else row.get('produto', '')
                        ),
                        axis=1
                    )
                
                todos_os_dados.append(df_limpo)
                logger.info(f"  Arquivo processado: {len(df_limpo)} linhas")
                
            except Exception as e:
                logger.warning(f"Erro ao processar arquivo {caminho}: {e}")
                continue

        if not todos_os_dados:
            logger.warning("Nenhum arquivo foi processado com sucesso")
            return []

        # 5. Consolidação final
        df_final = pd.concat(todos_os_dados, ignore_index=True)
        
        # 6. Remove linhas onde os principais campos de identificação estão vazios
        # Mantém a linha se houver ou um chamado ou um patrimônio
        df_final = df_final[
            (df_final['chamado'].astype(str).str.strip() != "") | 
            (df_final['patrimonio'].astype(str).str.strip() != "")
        ].copy()

        logger.info(f"Modo genérico: {len(df_final)} registros após consolidação")
        return df_final.to_dict('records')

# ============================================================================
# PRINT ENGINE
# ============================================================================

class PrintEngine:
    """
    Engine responsável pela impressão de arquivos PDF.

    Implementa comunicação com o sistema de impressão do Windows via ShellExecute.
    """

    @staticmethod
    def print_file(filepath: str, silent: bool = False) -> bool:
        """
        Envia um arquivo PDF para impressão automática.

        Args:
            filepath: Caminho completo do arquivo a imprimir.
            silent: Se True, não exibe mensagens de sucesso.

        Returns:
            True se a impressão foi enviada com sucesso, False caso contrário.
        """
        try:
            if not os.path.exists(filepath):
                logger.error(f"Arquivo não encontrado: {filepath}")
                return False

            # Shell execute codes: <= 32 indica erro
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "print",
                filepath,
                None,
                None,
                0,
            )

            if result <= 32:
                logger.warning(f"Shell execute error code: {result}")
                return False

            if not silent:
                logger.info(f"Impressão enviada: {os.path.basename(filepath)}")

            return True

        except Exception as e:
            logger.error(f"Erro ao enviar impressão: {e}")
            return False

    @staticmethod
    def open_file(filepath: str) -> bool:
        """
        Abre um arquivo com o programa padrão do sistema.

        Útil como fallback quando a impressão automática falha.

        Args:
            filepath: Caminho completo do arquivo.

        Returns:
            True se o arquivo foi aberto com sucesso, False caso contrário.
        """
        try:
            if not os.path.exists(filepath):
                logger.error(f"Arquivo não encontrado: {filepath}")
                return False

            os.startfile(filepath)
            logger.info(f"Arquivo aberto: {os.path.basename(filepath)}")
            return True

        except Exception as e:
            logger.error(f"Erro ao abrir arquivo: {e}")
            return False
