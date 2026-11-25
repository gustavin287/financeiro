# Planejamento e estruturas de dados

## Objetivo

Registrar contas a pagar e receber em uma interface Tkinter, usando somente estruturas em memória e um arquivo TXT para persistência.

## Tuplas

`TIPOS = ('Receita', 'Despesa')` e `STATUS_OPCOES = ('Pendente', 'Pago')` representam opções fixas que o usuário seleciona.

## Dicionários

Cada conta é um dicionário com seis campos:

```python
{
    'id': 1,
    'descricao': 'Salário',
    'valor': 2500.00,
    'tipo': 'Receita',
    'vencimento': '10/11/26',
    'status': 'Pago'
}
```

O `id` identifica a conta. `descricao` é o nome. `valor` é numérico (float). `tipo`, `vencimento` e `status` são textos.

## Lista

A variável `self.contas` na interface armazena uma lista de dicionários. O serviço lê o arquivo e produz essa lista, que pode ser alterada com as operações CRUD.

## Arquivo TXT

Cada linha tem campos separados por ponto e vírgula:

```text
1;Salário;2500.00;Receita;10/11/26;Pago
2;Energia elétrica;180.50;Despesa;15/11/26;Pendente
```

A leitura percorre as linhas usando `for`, divide os dados com `split(';')` e converte `id` e `valor` para os tipos corretos. Linhas malformadas são ignoradas. A escrita percorre a lista com `for` e regrava os registros. A ausência do arquivo inicialmente é tratada sem erro.

## Funções financeiras

`calcular_resumo(contas)` soma separadamente os valores do tipo `Receita` e `Despesa` e retorna `(receitas, despesas, receitas - despesas)`. Todas as contas entram nesse total, independentemente do status.

## Interface

O Tkinter apresenta um formulário, botões de cadastrar/alterar/excluir/limpar, tabela `ttk.Treeview`, resumo financeiro e alertas com `messagebox`.

## Fluxo do programa

1. `main.py` inicia a interface.
2. `carregar_contas()` lê o arquivo TXT e monta a lista.
3. Usuário executa uma operação pelo formulário ou pela tabela.
4. Após cada alteração, `salvar_contas()` persiste a lista no TXT.
5. A Treeview e o resumo financeiro são atualizados.
