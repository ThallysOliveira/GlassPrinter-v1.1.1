# 👨‍💻 Guia de Contribuição - GlassPrinter

## Bem-vindo ao GlassPrinter!

Este guia orienta desenvolvedores que desejam contribuir com melhorias, correções e novas funcionalidades.

## 📋 Padrões de Código

### Type Hints (Obrigatório)

Sempre use type hints em funções:

```python
# ❌ Errado
def processar_dados(registros):
    return registros

# ✅ Correto
def processar_dados(registros: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Processa os registros."""
    return registros
```

### Docstrings (Obrigatório)

Use docstrings em formato Google Style:

```python
def minha_funcao(param1: str, param2: int) -> bool:
    """
    Descrição breve de uma linha.

    Descrição mais longa se necessário. Pode incluir detalhes
    sobre comportamento, casos especiais, etc.

    Args:
        param1: Descrição do param1.
        param2: Descrição do param2.

    Returns:
        Descrição do retorno.

    Raises:
        ValueError: Quando param2 é negativo.
        TypeError: Quando param1 não é string.

    Examples:
        >>> resultado = minha_funcao("teste", 5)
        >>> resultado
        True
    """
    if param2 < 0:
        raise ValueError("param2 deve ser positivo")
    return True
```

### Nomes de Variáveis

- Use nomes descritivos em português
- Use snake_case para variáveis e funções
- Use UPPER_CASE para constantes
- Use CamelCase para classes

```python
# ❌ Errado
d = 10
resultado_final = calcular(d)

# ✅ Correto
dias_processados = 10
resultado_final = calcular(dias_processados)
```

### Comprimento de Funções

Mantenha funções pequenas e focadas:

```python
# ❌ Errado - Função muito longa
def processar_e_gerar_e_imprimir(dados):
    # Validação
    # Processamento
    # Geração de PDF
    # Impressão
    # Backup
    pass

# ✅ Correto - Funções focadas
def validar_dados(dados: Dict) -> None:
    """Valida dados."""
    pass

def gerar_pdf(dados: List[Dict]) -> str:
    """Gera PDF e retorna caminho."""
    pass

def imprimir_arquivo(caminho: str) -> bool:
    """Imprime arquivo."""
    pass
```

### Constantes

Coloque constantes em `core/config.py`:

```python
# ❌ Errado - Magic numbers no código
def desenhar_logo(canvas):
    canvas.drawImage(..., width=28 * mm, height=10 * mm)

# ✅ Correto - Constantes definidas
# core/config.py
LOGO_WIDTH: int = 28 * mm
LOGO_HEIGHT: int = 10 * mm

# layouts/adm.py
def desenhar_logo(canvas):
    canvas.drawImage(..., width=LOGO_WIDTH, height=LOGO_HEIGHT)
```

### Logging

Use logging em vez de print():

```python
import logging

logger = logging.getLogger(__name__)

# ❌ Errado
print(f"PDF gerado: {caminho}")

# ✅ Correto
logger.info(f"PDF gerado: {caminho}")
logger.warning(f"Arquivo ocupado: {arquivo}")
logger.error(f"Erro ao gerar PDF: {erro}")
```

## 📁 Estrutura de Diretórios

Ao adicionar novos módulos:

```
GlassPrinter/
├── core/              # Módulos core
│   ├── novo_modulo.py # Novo módulo aqui
│   └── __init__.py
├── layouts/           # Layouts
│   ├── novo_layout.py # Novo layout aqui
│   └── __init__.py
└── README.md
```

## 🔄 Workflow de Contribuição

### 0. Configuração Inicial (Primeira vez)
```bash
git init
git remote add origin <URL_DO_REPOSITORIO>
git add .
git commit -m "Initial commit"
git branch -M main
git push -u origin main
```

### 1. Criar Branch
```bash
git checkout -b feature/nome-da-funcionalidade
# ou
git checkout -b fix/nome-do-bug
```

### 2. Desenvolver

- Siga os padrões de código acima
- Teste suas mudanças localmente
- Adicione/atualize docstrings
- Adicione logging apropriado

### 3. Validar Sintaxe

```bash
python -m py_compile seu_arquivo.py
```

### 4. Testar

Antes de fazer commit:
```bash
# Teste manual
python main.py

# Validação de sintaxe
python -m py_compile core/*.py layouts/*.py main.py
```

### 5. Commit

```bash
git add .
git commit -m "Descrição clara da mudança"
# Exemplos:
# "feat: adiciona novo layout 'premium'"
# "fix: corrige erro ao imprimir QR code"
# "refactor: melhora validação de dados"
# "docs: atualiza README com novo layout"
```

### 6. Push e Pull Request

```bash
git push origin feature/nome-da-funcionalidade
```

Depois crie um Pull Request no GitHub.

## 🐛 Reportar Bugs

Ao reportar um bug, inclua:

1. **Versão do Python**
```bash
python --version
```

2. **Passos para reproduzir**
- Ação 1
- Ação 2
- Resultado esperado
- Resultado obtido

3. **Stack trace/Erro**
```python
Traceback (most recent call last):
  File "main.py", line 123, in gerar_pdf
    ...
```

4. **Ambiente**
- Windows/Linux/Mac
- Versão do sistema operacional
- Dependências instaladas

## ✨ Sugerir Funcionalidades

Ao sugerir uma funcionalidade:

1. Descreva o problema que resolve
2. Explique a solução proposta
3. Forneça exemplos de uso
4. Avalie o impacto no código existente

## 📚 Adicionando Novo Layout

### Passo 1: Criar arquivo

Crie `layouts/novo_layout.py`:

```python
"""
Layout NOVO para geração de etiquetas GlassPrinter.

Este módulo implementa o design para [descrição].
"""

import logging
from typing import Dict, Any
from reportlab.pdfgen.canvas import Canvas

from core.utils import get_resource_path, safe_get_dict_value
from core.config import LOGO_FILE, FONT_BOLD, FONT_DEFAULT

logger = logging.getLogger(__name__)

# Constantes de posição
LOGO_X: int = 3 * mm
LOGO_Y: int = 68 * mm

def desenhar_novo(canvas_obj: Canvas, dados: Dict[str, Any]) -> None:
    """
    Desenha o layout NOVO.

    Args:
        canvas_obj: Objeto Canvas do ReportLab.
        dados: Dicionário com os dados da etiqueta.
    """
    # Implementação aqui
    pass
```

### Passo 2: Atualizar config.py

```python
# core/config.py

LAYOUT_NOVO: str = "novo"

AVAILABLE_LAYOUTS: tuple = (LAYOUT_ADM, LAYOUT_UNIDADE, LAYOUT_NOVO)
```

### Passo 3: Atualizar main.py (se necessário)

O sistema carregará automaticamente o novo layout via `PDFEngine.set_layout()`.

## 🧪 Testes Sugeridos

Antes de submeter PR:

1. **Teste com entrada manual**
   - Adicione 3-4 registros manualmente
   - Gere PDF
   - Verifique saída

2. **Teste com importação**
   - Importe arquivo Excel
   - Verifique mapeamento
   - Gere PDF

3. **Teste com ambos os layouts**
   - Repita com ADM
   - Repita com UNIDADE

4. **Teste de impressão**
   - Tente imprimir (mesmo que não haja impressora)
   - Verifique fallback para abrir arquivo

## 📊 Cobertura de Documentação

Ao modificar código:

- [ ] Atualizou docstring da função?
- [ ] Atualizou type hints?
- [ ] Atualizou README se necessário?
- [ ] Atualizou IMPROVEMENTS.md?
- [ ] Atualizou ARCHITECTURE.md se necessário?

## 🎯 Prioridades de Contribuição

1. **Alta Prioridade**
   - Bugs críticos (aplicação trava)
   - Segurança
   - Acessibilidade

2. **Média Prioridade**
   - Melhorias de performance
   - Novos layouts
   - Melhorias de documentação

3. **Baixa Prioridade**
   - Refatorações cosméticas
   - Comentários adicionais

## 🚀 Release Checklist

Antes de fazer uma nova versão:

- [ ] Todos os testes passam
- [ ] Documentação atualizada
- [ ] IMPROVEMENTS.md atualizado
- [ ] Version bump em config.py
- [ ] Novo release no GitHub

## 📞 Contato

Para dúvidas:
- Abra uma issue no GitHub
- Deixe um comentário em um PR
- Consulte ARCHITECTURE.md

## ✅ Code Review Checklist

Ao revisar PR, verifique:

- [ ] Type hints presentes?
- [ ] Docstrings presentes?
- [ ] Segue padrões de código?
- [ ] Logging apropriado?
- [ ] Tratamento de erros?
- [ ] Funcionalidades originais mantidas?
- [ ] Sem código comentado?
- [ ] Sem imports não utilizados?

## 🎓 Recursos

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Google Style Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [ReportLab Documentation](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)

---

Obrigado por contribuir com o GlassPrinter! 🎉
