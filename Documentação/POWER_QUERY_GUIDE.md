# Power Query em Python - Documentação

## Visão Geral

Este projeto implementa a lógica do Power Query em Python, substituindo as transformações do Power Query por código Python usando pandas. Isso permite que o GlassPrinter processe dados de equipamentos diretamente, sem dependência do Power Query ou Excel.

## 📁 Estrutura de Arquivos

```
GlassPrinter/
├── core/
│   ├── data_transformer.py       # Módulo principal de transformação
│   ├── utils.py
│   ├── engine.py
│   └── config.py
├── power_query_transformation.ipynb  # Notebook interativo
├── example_power_query.py            # Exemplo de uso
└── README.md
```

## 🚀 Uso Rápido

### Opção 1: Usando o Módulo Python Diretamente

```python
from core.data_transformer import transform_power_query, export_to_excel

# Caminhos dos arquivos
kit_promovido_path = r"C:\caminho\kit.colaborador.promovido.xlsx"
kit_novo_path = r"C:\caminho\kit.novo.colaborador.xlsx"
solicitar_equipamento_path = r"C:\caminho\Solicitar.equipamento.xlsx"

# Transforma os dados
df = transform_power_query(
    kit_promovido_path,
    kit_novo_path,
    solicitar_equipamento_path,
)

# Exporta resultado
export_to_excel(df, "saida.xlsx")

# Usa os dados no GlassPrinter
print(f"Total de registros: {len(df)}")
print(df.head())
```

### Opção 2: Usando o Script Exemplo

```bash
python example_power_query.py
```

### Opção 3: Usando o Notebook Jupyter

```bash
jupyter notebook power_query_transformation.ipynb
```

## 📊 O que o módulo faz

### 1. Carrega 3 arquivos Excel

- **Kit Promovido**: `kit.colaborador.promovido.xlsx`
- **Kit Novo**: `kit.novo.colaborador.xlsx`
- **Solicitar Equipamento**: `Solicitar.equipamento.xlsx`

### 2. Processa cada arquivo

Para cada arquivo, o módulo:
- Carrega a sheet "Forms"
- Promove headers
- Adiciona/renomeia colunas
- Converte tipos de dados
- Remove colunas desnecessárias
- Divide equipamentos por delimitador
- Formata equipamentos com quantidade e data
- Adiciona sufixos ADM/DEV quando necessário

### 3. Combina os dados

Concatena os 3 DataFrames em um único Dataset.

### 4. Filtra por localidade

Mantém apenas registros onde `Informe sua localidade` é:
- "Azular"
- "Call Back - MG09"

### 5. Adiciona informações finais

- **Destino**: Baseado em "Local patrimonial" ou "Local Patrimonial"
- **Data de retirada**: Data atual
- **Origem**: Indica qual arquivo cada registro veio

## 🔧 API do Módulo

### `transform_power_query(kit_promovido_path, kit_novo_path, solicitar_equipamento_path)`

**Descrição**: Carrega e transforma os 3 arquivos, combinando-os.

**Argumentos**:
- `kit_promovido_path` (str): Caminho do arquivo kit promovido
- `kit_novo_path` (str): Caminho do arquivo kit novo
- `solicitar_equipamento_path` (str): Caminho do arquivo solicitar equipamento

**Retorno**: `pd.DataFrame` com dados combinados e filtrados

**Exceções**:
- `FileNotFoundError`: Se algum arquivo não existir
- `Exception`: Para erros de processamento

**Exemplo**:
```python
df = transform_power_query(
    "kit.promovido.xlsx",
    "kit.novo.xlsx",
    "solicitar.xlsx"
)
```

### `export_to_excel(df, output_path)`

**Descrição**: Exporta DataFrame para arquivo Excel.

**Argumentos**:
- `df` (pd.DataFrame): DataFrame a exportar
- `output_path` (str): Caminho do arquivo de saída

**Retorno**: Caminho do arquivo exportado (str)

**Exemplo**:
```python
export_to_excel(df, "dados_transformados.xlsx")
```

## 📈 Estrutura de Dados de Saída

### Colunas Principais

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| Chamado | str | ID/Key da solicitação |
| Nome Completo | str | Nome do colaborador/beneficiário |
| Centro de Custo | str | CC/Departamento |
| Destino | str | Local de entrega |
| Equipamentos | str | Descrição formatada do equipamento |
| Data de retirada | date | Data atual |
| Origem | str | Kit Promovido, Kit Novo ou Solicitar Equipamento |
| Informe sua localidade | str | Localidade do solicitante |
| Previsão de início | date | Data prevista de início |
| Motivo | str | Motivo da solicitação |

## 🎯 Lógica de Normalização de Equipamentos

O módulo normaliza equipamentos adicionando sufixos ADM/DEV:

```
Entrada:
  Equipamentos: "notebook dell"
  Resumo: "Setup ADM para novo colaborador"

Saída:
  "notebook dell - ADM"
```

**Regras**:
1. Se "Equipamentos" **não** contém "notebook" → sem sufixo
2. Se "Equipamentos" contém "notebook" **E** "Resumo" contém "adm" → adiciona " - ADM"
3. Se "Equipamentos" contém "notebook" **E** "Resumo" contém "dev" → adiciona " - DEV"
4. Caso contrário → sem sufixo

## 🔍 Transformações por Tipo de Kit

### Kit Promovido

**Transformações específicas**:
- Substitui valores específicos por vazios
- Remove 24 colunas desnecessárias
- Divide equipamentos por vírgula
- Formata: `QTD - Equipamento - Data`

**Colunas removidas**:
```
Sistemas Autoglass, Acesso ao MXM ou Dootax?, MXM, Dootax,
Office, Informe o serviço, Itens de Telefonia?, ...
```

### Kit Novo Colaborador

**Transformações específicas**:
- Remove 23 colunas desnecessárias
- Divide equipamentos por vírgula
- Formata: `Qtd - Equipamento - Data`
- Calcula dados automaticamente

### Solicitar Equipamento

**Transformações específicas**:
- Lógica condicional para equipamentos:
  - Se contém "bateria" → inclui motivo
  - Se contém "outros" → inclui motivo
  - Se contém "tonner" → inclui motivo
  - Caso contrário → apenas quantidade e equipamento

## 🐛 Tratamento de Erros

O módulo registra todos os eventos via logging:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Arquivos carregados com sucesso")
logger.error("Erro ao processar dados")
```

Para habilitar logging detalhado:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 📝 Exemplos Avançados

### Filtrar por Centro de Custo

```python
df_filtered = df[df["Centro de Custo"] == "CC123"]
```

### Agrupar por Destino

```python
group_by_dest = df.groupby("Destino").size()
print(group_by_dest)
```

### Contar Equipamentos por Tipo

```python
equipment_count = df["Equipamentos"].value_counts()
print(equipment_count)
```

### Adicionar Coluna Customizada

```python
df["Status"] = "Processado"
df["Data Processamento"] = pd.Timestamp.now()
```

### Exportar para CSV

```python
df.to_csv("dados.csv", index=False, encoding="utf-8-sig")
```

## 🔄 Integração com GlassPrinter

### Usar dados para gerar PDFs

No app atual, a geração de PDFs é feita pelo `PDFEngine` (em `core/engine.py`).

Exemplo (conceitual) usando o motor diretamente:

```python
from core.engine import PDFEngine

engine = PDFEngine()

# `records` deve ser uma lista de dicts no formato esperado pelos layouts:
# ex: [{"chamado": "...", "solicitante": "...", "patrimonio": "...", "produto": "...", ...}, ...]

records = df.to_dict("records")

layout = "adm"  # ou "unidade"
pdf_path = engine.generate_pdf(records, layout)
print(pdf_path)
```

## 📋 Checklist de Configuração

- [ ] Instalar pandas: `pip install pandas openpyxl`
- [ ] Atualizar caminhos dos arquivos no script
- [ ] Verificar se os arquivos Excel existem
- [ ] Verificar se as sheets são nomeadas "Forms"
- [ ] Executar e validar os dados de saída
- [ ] Integrar com GlassPrinter se necessário

## ⚠️ Limitações Conhecidas

1. **Dependência de estrutura de dados**: Espera coluna "Forms" em cada arquivo
2. **Encoding**: Presume UTF-8 encoding nos arquivos
3. **Data conversão**: Timestamps do Jira são convertidos de millisegundos
4. **Colunas nulas**: Remove completamente colunas vazias

## 🚀 Próximos Passos

- [ ] Adicionar validação de dados de entrada
- [ ] Implementar tratamento de duplicatas
- [ ] Criar interface gráfica para configuração
- [ ] Adicionar caching de dados
- [ ] Implementar versionamento de transformações

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs (enable debug mode)
2. Valide os arquivos Excel
3. Verifique os caminhos dos arquivos
4. Consulte a documentação do pandas

## 📄 Licença

Parte do projeto GlassPrinter.
