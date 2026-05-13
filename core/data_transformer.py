"""
Transformador de dados para substituir Power Query.

Este módulo implementa as transformações de dados equivalentes ao Power Query,
carregando e processando arquivos Excel de kit de colaboradores e equipamentos.
"""

import logging
import re
from typing import Optional, Dict, List, Any
from datetime import datetime, date
from pathlib import Path

import pandas as pd
from core.config import TEXT_REPLACEMENT_PATTERNS

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}


# Colunas a remover em cada transformação
KIT_PROMOVIDO_REMOVE = [
    "Sistemas Autoglass", "Acesso ao MXM ou Dootax?", "MXM", "Dootax",
    "Office", "Informe o serviço", "Itens de Telefonia?",
    "O colaborador já tem ramal atribuído?", "Ramal Antigo", "Itens de telefonia",
    "Informe o ramal", "Informe o grupo de rodízio", "Informe o grupo de captura",
    "Diretório de Rede?", "Usar Login espelho?", "Informe o caminho",
    "Acesso a internet?", "Usa Login espelho?", "Descreva o acesso",
    "Grupo de e-mail?", "Usa Login espelho?_1", "Informe os grupos",
    "Outras informações importantes:", "Motivo", "Anexo"
]

KIT_NOVO_REMOVE = [
    "Login Espelho", "Setor", "Cargo", "Departamento", "Azular", "MG09",
    "Necessário chip?", "DDD + Telefone", "Itens de telefonia",
    "Informe o ramal", "Informe o grupo de rodízio", "Informe o grupo de captura",
    "Acesso ao MXM ou Dootax?", "Sistemas Autoglass?", "Diretório de rede?",
    "Usar login espelho para diretório de rede?", "Informe o caminho",
    "Acesso a internet?", "Usar login espelho para acesso a internet?",
    "Descreva o acesso", "Acesso a grupos de e-mail?",
    "Usar login espelho para grupo de e-mail?", "Informe os grupos",
    "Informe o serviço", "Informe o motivo do upgrade de licença", "Anexo"
]

LOCALIDADES_FILTRO = ["Azular", "Call Back - MG09"]


# ============================================================================
# TRANSFORMAÇÕES GENÉRICAS
# ============================================================================

def _format_equipment(eqp: str, qtd: Optional[Any] = None, data: Optional[Any] = None) -> str:
    """
    Formata equipamento com quantidade e data, se necessário.
    
    Regras:
    - Se equipamento JÁ começa com número (ex: "2 monitor") → não adiciona quantidade
    - Se equipamento NÃO começa com número (ex: "webcam") → adiciona quantidade
    - Sempre adiciona data no final se fornecida
    
    Args:
        eqp: Texto do equipamento.
        qtd: Quantidade (opcional).
        data: Data de início (opcional).
        
    Returns:
        Equipamento formatado.
    """
    if not eqp:
        return ""
    
    eqp_str = str(eqp).strip()
    
    # Verifica se já começa com número
    comeca_com_numero = re.match(r'^\d+\s*(-|–|—)?', eqp_str)
    
    # Se não começa com número E tem quantidade, adiciona
    if not comeca_com_numero and qtd and not pd.isna(qtd):
        qtd_str = str(int(float(qtd))).strip() if isinstance(qtd, (int, float)) else str(qtd).strip()
        if qtd_str and qtd_str != "0":
            eqp_str = f"{qtd_str} - {eqp_str}"
    
    # Adiciona data no final se fornecida
    if data and not pd.isna(data):
        if isinstance(data, (datetime, date)):
            data_str = f"{data.day} de {MESES_PT.get(data.month)}"
        else:
            data_str = str(data).strip()
            
        if data_str:
            eqp_str = f"{eqp_str} - {data_str}"
    
    return eqp_str.strip()


def _process_equipment_item_kit_promovido(item_str: str) -> str: # type: ignore
    """
    Processa um item de equipamento específico para Kit Promovido,
    aplicando as regras de filtragem e renomeação.
    
    Regras:
    - Se o item indica que o equipamento JÁ POSSUI ou NÃO É NECESSÁRIO, retorna vazio.
    - Se o item indica "Necessário fornecer Micro computador", renomeia para "Micro computador".
    - Se o item indica "Necessário fornecer notebook", renomeia para "notebook".
    - Remove o prefixo genérico "Necessário fornecer " se ainda presente.
    """
    item_str_lower = item_str.lower()

    if "já possui notebook e irá continuar utilizando na nova área" in item_str_lower or \
       "não será necessário fornecer micro computador/notebook" in item_str_lower:
        return ""
    if "necessário fornecer micro computador" in item_str_lower:
        return "Micro computador"
    if "necessário fornecer notebook" in item_str_lower:
        return "notebook"
    
    return re.sub(r"necessário fornecer\s*", "", item_str, flags=re.IGNORECASE).strip()


def _normalize_equipment_text(eqp: str, resumo: Optional[str] = None) -> str:
    """
    Normaliza texto de equipamento adicionando sufixo ADM/DEV se necessário.

    Args:
        eqp: Texto do equipamento.
        resumo: Resumo da solicitação.

    Returns:
        Texto normalizado com sufixo se aplicável.
    """
    if not eqp:
        return eqp

    eqp_lower = str(eqp).lower()
    resumo_str = str(resumo).lower() if resumo else ""

    # Só marca se "Equipamentos" contiver "notebook"
    has_notebook = "notebook" in eqp_lower

    if not has_notebook:
        return eqp

    # Adiciona sufixo baseado no resumo
    if "adm" in resumo_str:
        suffix = " - ADM"
    elif "dev" in resumo_str:
        suffix = " - DEV"
    else:
        return eqp

    # Evita duplicar sufixo
    if str(eqp).endswith(suffix):
        return eqp

    return str(eqp) + suffix



def _split_equipments(df: pd.DataFrame, col_name: str = "Equipamentos") -> pd.DataFrame:
    """
    Divide coluna de equipamentos por delimitador e expande linhas.

    Args:
        df: DataFrame.
        col_name: Nome da coluna a dividir.

    Returns:
        DataFrame com equipamentos expandidos.
    """
    if col_name not in df.columns or df[col_name].isna().all():
        return df

    # Divide por vírgula e expande
    df = df.copy()
    df[col_name] = df[col_name].fillna("").astype(str)
    df_expanded = df.assign(**{col_name: df[col_name].str.split(",")})
    df_expanded = df_expanded.explode(col_name, ignore_index=False)
    df_expanded[col_name] = df_expanded[col_name].str.strip()

    return df_expanded


# ============================================================================
# PROCESSADORES POR TIPO DE KIT
# ============================================================================

def _process_kit_promovido(file_path: str) -> pd.DataFrame:
    """
    Processa arquivo de Kit Promovido.

    Args:
        file_path: Caminho do arquivo Excel.

    Returns:
        DataFrame processado.
    """
    logger.info(f"Processando Kit Promovido: {file_path}")

    # Carrega arquivo
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(file_path, sheet_name="Forms")

    # Remove colunas vazias e promove headers
    df = df.dropna(axis=1, how="all")

    # Remove colunas indesejadas
    cols_to_drop = [c for c in KIT_PROMOVIDO_REMOVE if c in df.columns]
    df = df.drop(columns=cols_to_drop, errors="ignore")

    # Converte "Previsão de Início" para data se existir
    if "Previsão de Início" in df.columns:
        df["Previsão de Início"] = pd.to_datetime(
            df["Previsão de Início"], unit="ms", errors="coerce"
        ).dt.date

    # Combina equipamentos de várias colunas em uma só
    equipamento_cols = [
        c for c in [
            "Equipamentos", 
            "Informe o equipamento", 
            "Equipamentos Adicionais",
            "Colaborador já possui notebook ou micro computador?"
        ] if c in df.columns
    ]
    if equipamento_cols:
        df["Equipamentos"] = (
            df[equipamento_cols]
            .astype(str)
            .replace({"nan": ""})
            .agg(", ".join, axis=1)
            .str.replace(r"\s*,\s*$", "", regex=True)
            .str.strip(", ")
        )
        df = df.drop(columns=[c for c in equipamento_cols if c != "Equipamentos"], errors="ignore")

        # Expande equipamentos separados por vírgula
        df = _split_equipments(df, "Equipamentos")

        # Aplica a função de processamento de itens e filtra os vazios
        df["Equipamentos"] = df["Equipamentos"].apply(_process_equipment_item_kit_promovido)
        df = df[df["Equipamentos"] != ""].copy() # Remove linhas onde o equipamento foi esvaziado

    # Formata equipamentos com quantidade e data
    if "Equipamentos" in df.columns:
        qtd_col = next(
            (c for c in ["QTD", "Informe a quantidade", "Quantidade"] if c in df.columns),
            None,
        )
        data_col = next(
            (c for c in ["Previsão de Início", "Previsão de início"] if c in df.columns),
            None,
        )

        df["Equipamentos"] = df.apply(
            lambda row: _format_equipment(
                row["Equipamentos"],
                row.get(qtd_col),
                row.get(data_col),
            ),
            axis=1,
        )

    # Adiciona sufixo ADM/DEV
    df["Equipamentos"] = df.apply(
        lambda row: _normalize_equipment_text(
            row.get("Equipamentos", ""), row.get("Resumo")
        ),
        axis=1,
    )

    # Renomeia colunas-chave
    df = df.rename(
        columns={
            "Issue Key": "Chamado",
            "CC": "Centro de Custo",
            "Previsão de Início": "Previsão de início",
        },
        errors="ignore",
    )

    # Garante que Centro de Custo existe
    if "Centro de Custo" not in df.columns:
        df["Centro de Custo"] = ""

    # Garante que Nome Completo existe
    if "Nome Completo" not in df.columns:
        df["Nome Completo"] = ""

    df["Origem"] = Path(file_path).name
    logger.info(f"Kit Promovido processado: {len(df)} linhas")

    return df


def _process_kit_novo(file_path: str) -> pd.DataFrame:
    """
    Processa arquivo de Kit Novo Colaborador.

    Args:
        file_path: Caminho do arquivo Excel.

    Returns:
        DataFrame processado.
    """
    logger.info(f"Processando Kit Novo: {file_path}")

    df = pd.read_excel(file_path, sheet_name="Forms")
    df = df.dropna(axis=1, how="all")

    # Remove colunas indesejadas
    cols_to_drop = [c for c in KIT_NOVO_REMOVE if c in df.columns]
    df = df.drop(columns=cols_to_drop, errors="ignore")

    # Converte data
    if "Previsão de início" in df.columns:
        df["Previsão de início"] = pd.to_datetime(
            df["Previsão de início"], unit="ms", errors="coerce"
        ).dt.date

    # Divide equipamentos
    if "Equipamentos" in df.columns:
        df = _split_equipments(df, "Equipamentos")

    # Formata equipamentos usando a função _format_equipment
    if "Equipamentos" in df.columns:
        qtd_col = "Informe a quantidade" if "Informe a quantidade" in df.columns else None
        data_col = "Previsão de início"
        
        df["Equipamentos"] = df.apply(
            lambda row: _format_equipment(
                row['Equipamentos'],
                row.get(qtd_col) if qtd_col else None,
                row.get(data_col)
            ),
            axis=1,
        )

    # Adiciona sufixo ADM/DEV
    df["Equipamentos"] = df.apply(
        lambda row: _normalize_equipment_text(
            row.get("Equipamentos", ""), row.get("Resumo")
        ),
        axis=1,
    )

    # Renomeia colunas
    df = df.rename(columns={"Issue Key": "Chamado"}, errors="ignore")

    # Garante que Centro de Custo existe
    if "Centro de Custo" not in df.columns:
        df["Centro de Custo"] = ""

    # Garante que Nome Completo existe
    if "Nome Completo" not in df.columns:
        df["Nome Completo"] = ""

    df["Origem"] = Path(file_path).name
    logger.info(f"Kit Novo processado: {len(df)} linhas")

    return df


def _process_solicitar_equipamento(file_path: str) -> pd.DataFrame:
    """
    Processa arquivo de Solicitar Equipamento.

    Args:
        file_path: Caminho do arquivo Excel.

    Returns:
        DataFrame processado.
    """
    logger.info(f"Processando Solicitar Equipamento: {file_path}")

    df = pd.read_excel(file_path, sheet_name="Forms")
    df = df.dropna(axis=1, how="all")

    # Cria coluna Equipamentos com formatação consistente
    if "Informe o equipamento" in df.columns:
        qtd_col = "Informe a quantidade" if "Informe a quantidade" in df.columns else None
        motivo_col = "Motivo" if "Motivo" in df.columns else None
        
        df["Equipamentos"] = df.apply(
            lambda row: (
                # Se é bateria, outros ou tonner, adiciona o motivo
                _format_equipment(
                    row['Informe o equipamento'],
                    row.get(qtd_col) if qtd_col else None,
                    row.get(motivo_col) if motivo_col and any(
                        keyword in str(row.get('Informe o equipamento', '')).lower()
                        for keyword in ["bateria", "outros", "tonner"]
                    ) else None
                )
                if any(
                    keyword in str(row.get("Informe o equipamento", "")).lower()
                    for keyword in ["bateria", "outros", "tonner"]
                )
                # Caso contrário, sem motivo
                else _format_equipment(
                    row.get('Informe o equipamento', ''),
                    row.get(qtd_col) if qtd_col else None,
                    None
                )
            ),
            axis=1,
        )

    # Adiciona sufixo ADM/DEV
    df["Equipamentos"] = df.apply(
        lambda row: _normalize_equipment_text(
            row.get("Equipamentos", ""), row.get("Resumo")
        ),
        axis=1,
    )

    # Renomeia colunas
    df = df.rename(
        columns={
            "Issue Key": "Chamado",
            "Beneficiário": "Nome Completo",
        },
        errors="ignore",
    )

    # Garante que Centro de Custo existe
    if "Centro de Custo" not in df.columns:
        df["Centro de Custo"] = ""

    # Garante que Nome Completo existe
    if "Nome Completo" not in df.columns:
        df["Nome Completo"] = ""

    df["Origem"] = Path(file_path).name
    logger.info(f"Solicitar Equipamento processado: {len(df)} linhas")

    return df


# ============================================================================
# API PRINCIPAL
# ============================================================================

def transform_power_query(
    kit_promovido_path: Optional[str] = None,
    kit_novo_path: Optional[str] = None,
    solicitar_equipamento_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Carrega e transforma dados dos arquivos Excel Power Query.

    Args:
        kit_promovido_path: Caminho do arquivo kit promovido.
        kit_novo_path: Caminho do arquivo kit novo.
        solicitar_equipamento_path: Caminho do arquivo solicitar equipamento.

    Returns:
        DataFrame combinado e filtrado.
    """
    logger.info("Iniciando transformação Power Query")

    try:
        dataframes: List[pd.DataFrame] = []

        if kit_promovido_path:
            dataframes.append(_process_kit_promovido(kit_promovido_path))
        if kit_novo_path:
            dataframes.append(_process_kit_novo(kit_novo_path))
        if solicitar_equipamento_path:
            dataframes.append(_process_solicitar_equipamento(solicitar_equipamento_path))

        if not dataframes:
            raise ValueError("Nenhum arquivo Power Query fornecido para transformar.")

        # Combina DataFrames
        df_combinado = pd.concat(dataframes, ignore_index=True)
        logger.info(f"DataFrames combinados: {len(df_combinado)} linhas")

        # Filtra por localidade, sem confundir com o campo de destino
        localidade_candidates = [
            "Informe sua localidade",
            "Localidade",
            "Unidade",
            "Informar localidade",
        ]
        localidade_col = next(
            (c for c in localidade_candidates if c in df_combinado.columns),
            None,
        )

        if localidade_col:
            df_filtrado = df_combinado[
                df_combinado[localidade_col].isin(LOCALIDADES_FILTRO)
            ]
            logger.info(f"Após filtro de localidade: {len(df_filtrado)} linhas")
        else:
            df_filtrado = df_combinado
            logger.warning("Coluna de localidade não encontrada, retornando todos os dados")

        # Adiciona coluna "Destino" a partir do local patrimonial
        destino_candidates = ["Local patrimonial", "Local Patrimonial"]
        destino_col = next(
            (c for c in destino_candidates if c in df_filtrado.columns),
            None,
        )
        if destino_col:
            df_filtrado["Destino"] = df_filtrado[destino_col].fillna("")

        # Adiciona data de retirada
        df_filtrado["Data de retirada"] = datetime.now().date()

        # Reordena colunas (prioriza as principais)
        main_cols = [
            "Chamado",
            "Nome Completo",
            "Relator",
            "Centro de Custo",
            "Destino",
            "Equipamentos",
            "Data de retirada",
            "Origem",
        ]
        available_main_cols = [c for c in main_cols if c in df_filtrado.columns]
        other_cols = [c for c in df_filtrado.columns if c not in available_main_cols]
        df_filtrado = df_filtrado[available_main_cols + other_cols]

        logger.info(f"Transformação concluída: {len(df_filtrado)} registros finais")

        return df_filtrado

    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro ao transformar Power Query: {e}")
        raise


def export_to_excel(
    df: pd.DataFrame,
    output_path: str,
) -> str:
    """
    Exporta DataFrame para Excel.

    Args:
        df: DataFrame a exportar.
        output_path: Caminho do arquivo de saída.

    Returns:
        Caminho do arquivo exportado.
    """
    try:
        df.to_excel(output_path, sheet_name="Dados", index=False)
        logger.info(f"Arquivo exportado: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Erro ao exportar Excel: {e}")
        raise
