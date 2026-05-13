# 🏗️ Guia de Arquitetura - GlassPrinter v1.1.1

## Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                       main.py (GUI)                              │
│              GlassPrinterApp (Tkinter Interface)                │
├─────────────────────────────────────────────────────────────────┤
│   - Screen Management (telas)                                   │
│   - UI Construction (formulários)                               │
│   - Data Entry & Validation (entrada de dados)                 │
│   - Batch Import (importação)                                   │
│   - PDF Generation & Printing (geração)                        │
└──────────────────┬──────────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┬─────────────┐
        │          │          │             │
        ▼          ▼          ▼             ▼
┌────────────┐ ┌─────────┐ ┌────────────┐ ┌──────────┐
│   Config   │ │ Engine  │ │   Utils    │ │Exceptions│
│            │ │         │ │            │ │          │
│ Constantes │ │PDF/Print│ │ Funções    │ │ Custom   │
│ Mensagens  │ │ Classes │ │ Utilitárias│ │Exceptions│
│ Cores/Fonts│ │         │ │            │ │          │
└────────────┘ └─────────┘ └────────────┘ └──────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────┐      ┌──────────────┐
│   layouts    │      │   assets     │
│              │      │              │
│ - adm.py     │      │ - logo.ico   │
│ - unidade.py │      │ - logo.png   │
└──────────────┘      └──────────────┘
```

## Fluxo de Dados

### 1. Inicialização
```
main.py
  ├─ __init__()
  │  ├─ _configure_window()
  │  ├─ _initialize_engines()
  │  │  ├─ PDFEngine()
  │  │  └─ PrintEngine()
  │  ├─ _initialize_data_structures()
  │  ├─ _load_icon()
  │  └─ tela_selecao_inicial()
```

### 2. Seleção de Layout
```
tela_selecao_inicial()
  ├─ Exibe botões: ADM ou UNIDADE
  └─ setup_ui(layout)
       ├─ _clear_main_container()
       ├─ _construir_formulario_manual()
       ├─ _construir_area_lote()
       └─ _construir_tabela_resumo()
```

### 3. Entrada Manual
```
add_manual()
  ├─ Coleta dados dos campos
  ├─ _validate_record()
  ├─ Adiciona à dados_fila
  ├─ _adicionar_na_tabela()
  └─ _reset_manual_form()
```

### 4. Importação em Lote
```
importar_lote()
  ├─ Abre dialog de seleção
  └─ pdf_engine.importar_e_consolidar(caminhos_arquivos)
       ├─ Detecta se é Power Query (3 arquivos específicos)
       │  ├─ core/data_transformer.transform_power_query()
       │  └─ Consolida dados (gera lista[dict])
       └─ Caso contrário: modo genérico
          └─ motor_de_mapeamento(df_bruto, SMART_MAPPING)
       └─ Retorna lista[dict] pronta
  └─ Adiciona cada registro em dados_fila e na TreeView
```

### 5. Geração de PDF
```
gerar_pdf()
  ├─ Validações
  │  ├─ Layout ativo?
  │  └─ Dados na fila?
  ├─ pdf_engine.save_backup()
  │  └─ Salva CSV com histórico
  ├─ pdf_engine.generate_pdf()
  │  ├─ set_layout()
  │  │  └─ Carrega módulo de layout
  │  └─ Chama desenhar_adm() ou desenhar_unidade()
  │     └─ Desenha etiquetas
  ├─ Pergunta ao usuário sobre impressão
  ├─ print_engine.print_file() ou print_engine.open_file()
  └─ _limpar_dados()
```

## Módulos e Responsabilidades

### 📄 main.py
**Responsabilidade:** Interface com usuário

```python
class GlassPrinterApp:
    # Inicialização
    __init__()
    _configure_window()
    _initialize_engines()
    _initialize_data_structures()
    _load_icon()
    
    # Screen Management
    tela_selecao_inicial()      # Tela de seleção de layout
    setup_ui()                  # Configura tela principal
    _clear_main_container()     # Limpa widgets
    
    # UI Construction
    _construir_formulario_manual()   # Formulário
    _construir_area_lote()           # Área de importação
    _construir_tabela_resumo()       # Tabela de visualização
    
    # Data Entry
    add_manual()                # Adiciona registro manual
    _validate_record()          # Valida dados
    _adicionar_na_tabela()      # Insere na Treeview
    _reset_manual_form()        # Limpa formulário
    
    # Batch Import
    importar_lote()             # Importa planilhas (automático via engine)
    
    # PDF Generation
    gerar_pdf()                 # Gera PDF
    _limpar_dados()             # Limpa dados
```

### ⚙️ core/config.py
**Responsabilidade:** Configurações e constantes

```python
# Informações da aplicação
APP_VERSION
APP_TITLE
APP_WINDOW_WIDTH
APP_WINDOW_HEIGHT

# Diretórios
ASSETS_DIR
LAYOUTS_DIR
ICON_FILE
LOGO_FILE
HISTORY_FILE

# PDF e Etiquetas
LABEL_WIDTH_MM
LABEL_HEIGHT_MM
LABEL_SIZE
QR_CODE_VERSION
QR_CODE_BOX_SIZE
QR_CODE_BORDER

# Cores
COLOR_HEADER_ADM
COLOR_HEADER_UNIDADE
COLOR_BACKGROUND_CELL
COLOR_BLACK
COLOR_WHITE

# Fontes
FONT_DEFAULT
FONT_BOLD
FONT_SIZE_TITLE
FONT_SIZE_HEADER
FONT_SIZE_LABEL
FONT_SIZE_VALUE
FONT_SIZE_QR_LABEL

# Layouts
LAYOUT_ADM
LAYOUT_UNIDADE
AVAILABLE_LAYOUTS

# Campos
FIELD_MAPPING
FORM_FIELDS
REQUIRED_FIELDS

# Mensagens
MESSAGES (dicionário com todas as mensagens)

# Jira
JIRA_BASE_URL
```

### 🔧 core/engine.py
**Responsabilidade:** Lógica de negócio (PDF e impressão)

```python
class PDFEngine:
    __init__(output_dir=None)
    set_layout(layout_name)     # Define layout
    generate_pdf(records, layout_name)  # Gera PDF
    save_backup(records)        # Salva CSV de backup

class PrintEngine:
    @staticmethod
    print_file(filepath, silent=False)  # Imprime arquivo
    
    @staticmethod
    open_file(filepath)         # Abre arquivo
```

### 🛠️ core/utils.py
**Responsabilidade:** Funções reutilizáveis

```python
# Path utilities
get_resource_path(relative_path)
get_desktop_path(subfolder)

# Data validation
is_empty_value(value)
normalize_text(text, patterns_to_remove)
safe_get_dict_value(data, key, default)

# File operations
ensure_file_not_locked(filepath, max_retries)
create_backup_filename(base_name, timestamp_format)

# Data formatting
format_quantity_product(quantity, product)
format_jira_link(issue_key, base_url)
```

### ⚠️ core/exceptions.py
**Responsabilidade:** Exceções customizadas

```python
class GlassPrinterException(Exception)    # Base
class ValidationError(GlassPrinterException)
class PDFGenerationError(GlassPrinterException)
class PrintError(GlassPrinterException)
class FileOperationError(GlassPrinterException)
```

### 🎨 layouts/adm.py
**Responsabilidade:** Design do layout ADM

```python
# Constantes de posição
Y_TOP, LOGO_X, LOGO_Y, LOGO_WIDTH, LOGO_HEIGHT
CELL_HEADER_DATE_X, CELL_HEADER_DATE_Y, ...
QR_SIZE, QR_X, QR_Y
FILIAL_ID_X, FILIAL_ID_Y, FILIAL_ID_FONT_SIZE

# Funções
gerar_qr_adm(texto)             # Gera QR code
desenhar_celula_adm(...)        # Desenha célula
desenhar_adm(canvas_obj, dados) # Desenha layout completo
```

### 🎨 layouts/unidade.py
**Responsabilidade:** Design do layout UNIDADE

```python
# Constantes de posição
LOGO_X, LOGO_Y, LOGO_WIDTH, LOGO_HEIGHT
QR_SIZE, QR_CHAMADO_X, QR_CHAMADO_Y
QR_PATRIMONIO_X, QR_PATRIMONIO_Y

# Funções
gerar_qr_unidade(texto)             # Gera QR code
desenhar_celula(...)                # Desenha célula
desenhar_unidade(canvas_obj, dados) # Desenha layout completo
```

## Fluxo de Dados - Detalhado

### Entrada Manual
```
Usuário preenche formulário
         │
         ▼
add_manual()
         │
         ├─ Cria dicionário de registro
         │
         ├─ _validate_record()
         │  └─ Valida campos obrigatórios
         │
         ├─ self.dados_fila.append(registro)
         │  └─ Adiciona à fila
         │
         ├─ _adicionar_na_tabela(registro)
         │  └─ Exibe na TreeView
         │
         └─ _reset_manual_form()
            └─ Limpa campos
```

### Importação em Lote
```
Usuário seleciona arquivos
         │
         ▼
importar_lote()
         │
         └─ pdf_engine.importar_e_consolidar(caminhos_arquivos)
            │
            ├─ Detecta Power Query (3 arquivos específicos)
            │  └─ core/data_transformer.transform_power_query()
            │
            └─ Caso contrário: modo genérico
               └─ motor_de_mapeamento(df_bruto, SMART_MAPPING)
            │
            └─ Retorna lista[dict] pronta
         │
         └─ Adiciona cada registro em dados_fila e na TreeView
```

### Geração de PDF
```
Usuário clica "Exportar"
         │
         ▼
gerar_pdf()
         │
         ├─ Valida layout_ativo
         ├─ Valida dados_fila
         │
         ├─ pdf_engine.save_backup(dados_fila)
         │  └─ Salva CSV de histórico
         │
         ├─ pdf_engine.generate_pdf(dados_fila, layout)
         │  │
         │  ├─ set_layout()
         │  │  └─ Carrega adm.py ou unidade.py
         │  │
         │  ├─ canvas.Canvas()
         │  │
         │  └─ Para cada registro:
         │     ├─ Se layout == "adm":
         │     │  └─ desenhar_adm(canvas, registro)
         │     └─ Se layout == "unidade":
         │        └─ desenhar_unidade(canvas, registro)
         │
         ├─ canvas.save()
         │
         ├─ Pergunta ao usuário sobre impressão
         │  ├─ Sim: print_engine.print_file()
         │  └─ Não: nada
         │
         ├─ _limpar_dados()
         │  └─ dados_fila = []
         │
         └─ Exibe mensagem de sucesso
```

## Tratamento de Erros

### Camadas de Tratamento

1. **Validation Layer**
   - `_validate_record()` valida dados
   - Levanta `ValidationError`

2. **Business Logic Layer**
   - `PDFEngine` trata erros de PDF
   - `PrintEngine` trata erros de impressão

3. **UI Layer**
   - `try/except` captura exceções
   - Exibe `messagebox` ao usuário
   - Log com `logger`

## Dependências e Imports

```
main.py
├── tkinter (GUI)
├── pandas (Excel/CSV)
├── logging (Logging)
├── typing (Type hints)
├── pathlib (Path handling)
│
├── core.config (Configurações)
├── core.engine (PDF/Print engines)
├── core.utils (Utilitários)
└── core.exceptions (Exceções)

core/engine.py
├── pandas (DataFrame)
├── reportlab (PDF)
├── ctypes (Print API Windows)
└── logging (Logging)

layouts/adm.py
├── qrcode (QR codes)
├── reportlab (Desenho)
├── core.utils (Funções auxiliares)
└── core.config (Constantes)

layouts/unidade.py
├── qrcode (QR codes)
├── reportlab (Desenho)
├── core.utils (Funções auxiliares)
└── core.config (Constantes)
```

## Padrões de Design Usados

### 1. **Singleton Pattern (Implícito)**
- `PDFEngine` e `PrintEngine` usadas como singletons
- Uma instância por aplicação

### 2. **Factory Pattern**
- `set_layout()` carrega o módulo de layout correto

### 3. **Strategy Pattern**
- Diferentes estratégias de desenho (ADM vs UNIDADE)
- Encapsuladas em módulos separados

### 4. **Separation of Concerns**
- GUI (main.py) separada da lógica (engine.py)
- Layout separado do engine

### 5. **Template Method Pattern**
- Fluxo geral em `gerar_pdf()`
- Detalhes específicos em layouts

## Extensibilidade

### Adicionar Novo Layout

1. Criar `layouts/novo.py`:
```python
def desenhar_novo(canvas_obj: Canvas, dados: Dict[str, Any]) -> None:
    """Implementação do novo layout."""
    ...
```

2. Atualizar `core/config.py`:
```python
LAYOUT_NOVO: str = "novo"
AVAILABLE_LAYOUTS: tuple = (LAYOUT_ADM, LAYOUT_UNIDADE, LAYOUT_NOVO)
```

3. Pronto! Sistema suporta novo layout automaticamente

### Adicionar Novo Engine

1. Criar classe em `core/engine.py`:
```python
class NovoEngine:
    def processar(self, dados):
        """Nova funcionalidade."""
        ...
```

2. Usar em `main.py`:
```python
self.novo_engine = NovoEngine()
```

## Performance Considerations

1. **Pandas concat()** - Junta múltiplos arquivos eficientemente
2. **Logging** - Apenas em níveis apropriados
3. **Canvas generation** - Uma página por iteração
4. **Validation** - Validado uma vez antes de processar

## Security Considerations

1. **Path validation** - Usar `pathlib.Path`
2. **File permissions** - Verificar permissões antes
3. **Data validation** - Validar todos os inputs
4. **Exception handling** - Não expor internals

---

Este documento serve como referência para desenvolvedores que trabalham com o projeto GlassPrinter.
