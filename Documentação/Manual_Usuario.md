# Manual do Usuário — GlassPrinter (GUI)

Bem-vindo(a) ao **GlassPrinter**. Este manual foi feito para você conseguir gerar etiquetas em PDF com rapidez e segurança.

---

## 1) Antes de começar

### Requisitos
- Sistema: Windows 7+ (recomendado Windows 10/11)
- Papel/fita da impressora compatível com etiquetas **100mm x 80mm**
- Arquivos do Excel para importação (quando usar)

### Arquivos e pastas usadas
- Os **PDFs** e o **histórico** ficam na pasta do Desktop:
  - `Desktop/Etiquetas_GlassPrinter/`

---

## 2) Tela inicial: escolher o tipo de etiqueta

Ao abrir o GlassPrinter, você verá dois botões:

### ✅ Layout ADM
Use quando for **estoque / requisições internas**.

### ✅ Layout UNIDADE
Use quando for **envio/logística** (formulário de unidade e rastreabilidade).

Depois de escolher um layout, você pode trocar a qualquer momento usando o botão **“Trocar Layout”**.

---

## 3) Entrada Manual (uma etiqueta por vez)

Use este modo quando tiver poucos registros (ex.: 1 a 5).

### Passo a passo
1. Vá na aba **Entrada Manual**
2. Preencha os campos.
3. Clique em **Adicionar**
4. O registro vai aparecer na **tabela de conferência**.
5. Repita para adicionar novos registros.

### Campos obrigatórios
O app exige os campos obrigatórios de acordo com o layout selecionado:
- **Chamado**
- **Beneficiário / Solicitante** (dependendo do layout)

Se faltar algum campo obrigatório, o app mostrará um aviso e não adicionará o registro.

---

## 4) Importação em Lote (vários registros de uma vez)

Use este modo quando tiver muitos registros em planilhas.

### Passo a passo
1. Vá na aba **Importar Planilhas**
2. Clique em **“Selecionar Múltiplas Planilhas”**
3. Selecione seus arquivos Excel/CSV
4. Aguarde o processamento
5. O app adicionará os registros gerados na tabela

### Importação automática
O app tenta detectar automaticamente um conjunto específico de arquivos. Quando identificado, ele aplica as transformações automáticas necessárias.

### Se não for o conjunto detectado
O app usa o modo genérico, buscando colunas pelos nomes e mapeando para os campos do formulário.

### Atenção
Após importar, revise sempre a tabela antes de gerar o PDF.

---

## 5) Conferência na Tabela

Após adicionar manualmente ou importar, revise a tabela de conferência:

### Checklist rápido
- **Todos os “Chamados” preenchidos**
- **Todos os “Beneficiários/Solicitantes” preenchidos**
- **Quantidade faz sentido**
- **Produtos/equipamentos corretos**
- **Destino/Filial correto (quando aplicável)**
- **Sem registros duplicados**

### Edição rápida do Patrimônio (clique duplo)
No layout onde “Patrimônio” existe:
- Dê **duplo clique** na linha da tabela
- Digite o novo **Patrimônio**
- Confirme com **OK**

---

## 6) Gerar PDF (botão Exportar)

Quando a tabela estiver correta:

1. Clique em **Exportar**
2. O app:
   - salva o backup/histórico,
   - gera o PDF com as etiquetas,
   - pergunta se deseja imprimir

### Nomenclatura do arquivo
Os PDFs são salvos com um padrão que inclui o layout e a data/hora do processamento.

---

## 7) Impressão

Após gerar o PDF, o app oferece a opção de impressão:

### Impressão Automática
- Se estiver configurado corretamente, o app tenta enviar direto para a impressora padrão.

### Se falhar: impressão manual
- O app abre o PDF para você imprimir manualmente.

> Dica: confirme se a impressora correta está como **“Impressora Padrão”** no Windows.

---

## 8) Solução de problemas (Troubleshooting)

### “Dados Incompletos” ao adicionar
- Verifique se **Chamado** e **Beneficiário/Solicitante** não estão vazios
- Remova espaços em branco desnecessários

### Backup/histórico não salva
- Pode estar com arquivo aberto no Excel
- Feche o `historico_etiquetas.csv` e tente novamente

### Importação não gerou registros
- Confirme se as colunas existem e têm nomes compatíveis com o app
- Verifique se a planilha está na aba/estrutura esperada (quando for Power Query automático)
- Teste com arquivos Excel `.xlsx` ou `.xls` (ou CSV)

### PDF sai vazio ou com texto estranho
- Revise os campos na tabela
- Garanta que os dados importados estão completos e coerentes

### Impressão automática não funciona
- Confirme a impressora padrão no Windows
- Se necessário, imprima manualmente abrindo o PDF e usando Ctrl+P

---

## 9) Boas práticas (para evitar erros)

- Sempre revise a tabela antes de clicar **Exportar**
- Evite duplicidades
- Use arquivos Excel bem formados (evite planilhas quebradas/mescladas)
- Se estiver ajustando “Patrimônio”, use o recurso de **duplo clique**
