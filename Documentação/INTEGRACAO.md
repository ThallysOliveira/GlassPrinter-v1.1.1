# Integração Power Query - Guia Rápido

## ✅ Instalação Concluída

O módulo Power Query agora está integrado ao GlassPrinter! 

## 🚀 Como Usar

### No App GlassPrinter (UI)

1. **Abra o GlassPrinter**

2. **Clique em "Importar Lote"**

3. **Selecione os 3 arquivos em sequência:**
   - `kit.colaborador.promovido.xlsx`
   - `kit.novo.colaborador.xlsx`
   - `Solicitar.equipamento.xlsx`

4. **O app detecta automaticamente e usa o novo Power Query**

### Detecção Automática

✓ Se você selecionar os **3 arquivos** → Usa o novo `data_transformer`  
✓ Se você selecionar **outros arquivos** → Usa modo genérico (compatível com código antigo)

## 📝 Fluxo de Dados

```
Seleção de Arquivos (main.py)
         ↓
importar_lote()
         ↓
pdf_engine.importar_e_consolidar()
         ↓
Detecta 3 arquivos PQ?
    ↓                ↓
   SIM              NÃO
    ↓                ↓
transform_power_query()    _importar_modo_generico()
    ↓                ↓
Consolida dados     Consolida dados
    ↓                ↓
Retorna Dict[]      Retorna Dict[]
    ↓                ↓
    └────────┬───────┘
             ↓
        Adiciona na tabela
             ↓
     Pronto para gerar PDF
```

## 🔍 O que Muda na Importação

### Antes (Manual)
- Tela de mapeamento de colunas
- Seleção manual de campos
- Processamento limitado

### Depois (Power Query Automático)
- ✅ Lê os 3 arquivos
- ✅ Aplica todas as transformações
- ✅ Formata equipamentos automaticamente
- ✅ Adiciona sufixos ADM/DEV
- ✅ Filtra por localidade
- ✅ Adiciona data de retirada
- ✅ Pronto para impressão

## 📊 Exemplo de Saída

| Chamado | Nome Completo | Centro de Custo | Destino | Equipamentos | Data de retirada |
|---------|---------------|-----------------|---------|--------------|------------------|
| AB-123 | João Silva | CC001 | Azular | 1 - Notebook Dell - ADM | 2026-05-05 |
| AB-124 | Maria Santos | CC002 | MG09 | 2 - Monitor 24" | 2026-05-05 |

## 🛠️ Troubleshooting

### "Nem todos os 3 arquivos foram encontrados"
- Certifique-se de que os arquivos têm os nomes corretos:
  - Contém "promovido" → Kit Promovido ✓
  - Contém "novo" e "colaborador" → Kit Novo ✓
  - Contém "solicitar" ou "equipamento" → Solicitar Equipamento ✓

### Erros de Processamento
- Verifique se as sheets são nomeadas "Forms"
- Confirme que os arquivos estão em formato Excel válido
- Verifique os logs em `main.py`

### Modo Genérico Ativado
- Se o app usar o modo genérico, significa que:
  - Não encontrou os 3 arquivos corretos
  - Ou os nomes estão diferentes
  - Verifique os nomes dos arquivos

## 📂 Arquivos Modificados

- `core/engine.py` - Adicionado suporte a Power Query
- `core/data_transformer.py` - Novo módulo (não modificado pelo app)
- `main.py` - Atualizado texto da caixa de diálogo

## 💡 Dica Pro

Para testar o novo módulo **sem usar o app**, rode:

```bash
python example_power_query.py
```

Ou abra o Jupyter Notebook:

```bash
jupyter notebook power_query_transformation.ipynb
```

## 📞 Próximas Funcionalidades

- [ ] Salvar últimos caminhos de arquivo
- [ ] Interface para escolher modo (Power Query vs Genérico)
- [ ] Pré-visualização de dados antes de importar
- [ ] Histórico de transformações
- [ ] Validação de integridade de dados

---

**Status**: ✅ Integração completa e funcionando
