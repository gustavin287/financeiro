# Controle Financeiro em Python - v14

Aplicação desktop feita em Tkinter, com armazenamento no arquivo `contas.txt`.

## Executar

Abra a pasta `projeto_contas_gui` no VS Code e execute:

```bash
python main.py
```

## Teclado

- **Tipo:** campo de uma letra, somente `R` (Receita) ou `D` (Despesa).
- **Status:** campo de uma letra, somente `P` (Pendente) ou `A` (Pago).
- **F12:** consulta de opções usando setas e Enter.
- **Vencimento:** `DD/MM/AA`, data de hoje ao iniciar. Os números substituem dígitos; barras são fixas.
- **Enter / Seta para baixo:** valida o campo e avança.
- **Seta para cima:** campo anterior; no primeiro, vai à tabela.
- **Espaço:** digita espaços normalmente na descrição; não possui atalho de navegação.
- **Alt+S:** salvar/atualizar; **Alt+N:** novo/limpar; **Alt+E:** excluir.
- **F2:** salvar/atualizar; **Esc:** limpar.
- **Na tabela:** setas navegam, Enter edita, Esc retorna ao formulário.

Os campos Tipo e Status exibem apenas as letras, mas no TXT e na tabela são mantidos os nomes completos para compatibilidade com os cadastros anteriores.

**Atenção:** preserve o seu `contas.txt` ao atualizar o sistema.

## Correção v10 (teclado)
- Tipo e status são campos de um caractere: R/D e P/A.
- F12 abre a consulta em ambos, com setas e Enter para confirmar.
- A data usa DD/MM/AA preenchida inicialmente com a data atual. Digitando um número, ele substitui o dígito na posição do cursor, sem deslocar as barras.
- Enter e seta para baixo validam e avançam; seta para cima retorna; Espaço não abre a tabela a partir dos campos (v13).
- Os atalhos Alt+S, Alt+N e Alt+E continuam disponíveis.
- Os eventos são processados diretamente em cada campo especial, preservando os eventos normais do Tkinter e impedindo a inserção duplicada.


## Versão 12
Eventos específicos por tecla, sem filtro manual de Alt. Título identificado como [v12].

## Versão 13
Espaço normal na descrição, bloqueado nos campos restritos. Use ↑ no primeiro campo para acessar a tabela.

## Versão 14
Removido o atalho de navegação por Espaço, inclusive na tabela. A seta ↑ abre a tabela apenas a partir da descrição; nos demais campos, volta ao anterior.
