"""Interface de contas: navegação por teclado, F12 e validação por campo."""
import math
import re
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from services.finance_manager import (
    TIPOS, STATUS_OPCOES, carregar_contas, salvar_contas,
    calcular_resumo, adicionar_conta, atualizar_conta, excluir_conta,
)


def moeda(valor):
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


class CampoOpcao(ttk.Entry):
    """Campo de escolha de um caractere: R/D ou P/A; F12 abre consulta."""
    def __init__(self, parent, variavel, opcoes, codigos, **kwargs):
        super().__init__(parent, textvariable=variavel, **kwargs)
        self.variavel = variavel
        self.opcoes = opcoes
        self.codigos = {letra.upper(): opcao for letra, opcao in codigos.items()}
        # O campo exibe apenas um caractere. Nomes completos ficam só no F12.
        self.configure(width=4)
        # Vincula diretamente ao widget. O bind anterior em uma tag personalizada
        # não era executado de forma confiável no Windows/Tk.
        self.bind('<<Paste>>', lambda _e: 'break')
        self.bind('<<Cut>>', lambda _e: 'break')
        self.bind('<Control-v>', lambda _e: 'break')
        self.bind('<Control-V>', lambda _e: 'break')

    def _abrir(self, _evento=None):
        self.abrir_consulta()
        return 'break'

    def abrir_consulta(self):
        topo = tk.Toplevel(self)
        topo.title('Selecionar opção (F12)')
        topo.transient(self.winfo_toplevel())
        topo.resizable(False, False)
        painel = ttk.Frame(topo, padding=18)
        painel.pack(fill='both', expand=True)
        ttk.Label(painel, text='Selecione uma opção', font=('Segoe UI', 12, 'bold')).pack(anchor='w')
        ttk.Label(painel, text='↑ ↓ para navegar  •  Enter para confirmar  •  Esc para sair').pack(anchor='w', pady=(4, 12))
        lista = tk.Listbox(painel, width=46, height=len(self.opcoes),
                           font=('Segoe UI', 12), activestyle='none',
                           selectmode='browse', exportselection=False)
        lista.pack(fill='x')
        for codigo, opcao in self.codigos.items():
            lista.insert('end', f'{codigo} - {opcao}')
        atual = self.variavel.get()
        indice = list(self.codigos).index(atual) if atual in self.codigos else 0
        lista.selection_set(indice)
        lista.activate(indice)
        lista.see(indice)

        # Mantemos um índice único para evitar divergência entre o item ativo
        # (foco pontilhado do Tk) e o item realmente selecionado (faixa azul).
        selecionado = [indice]

        def selecionar_indice(novo):
            novo = max(0, min(len(self.opcoes) - 1, novo))
            selecionado[0] = novo
            lista.selection_clear(0, tk.END)
            lista.selection_set(novo)
            lista.activate(novo)
            lista.see(novo)

        def mover(delta):
            selecionar_indice(selecionado[0] + delta)
            return 'break'

        def confirmar(_evento=None):
            self.variavel.set(list(self.codigos)[selecionado[0]])
            topo.destroy()
            self.focus_set()
            return 'break'

        def cancelar(_evento=None):
            topo.destroy()
            self.focus_set()
            return 'break'

        def letra(_evento):
            codigo = _evento.char.upper()
            if codigo in self.codigos:
                valor = self.codigos[codigo]
                idx = self.opcoes.index(valor)
                selecionar_indice(idx)
                return 'break'
            return None

        lista.bind('<Up>', lambda _e: mover(-1))
        lista.bind('<Down>', lambda _e: mover(1))
        lista.bind('<Home>', lambda _e: (selecionar_indice(0), 'break')[1])
        lista.bind('<End>', lambda _e: (selecionar_indice(len(self.opcoes) - 1), 'break')[1])
        lista.bind('<Return>', confirmar)
        lista.bind('<KP_Enter>', confirmar)
        def clique(_evento):
            idx = lista.nearest(_evento.y)
            selecionar_indice(idx)

        lista.bind('<ButtonRelease-1>', clique)
        lista.bind('<Double-Button-1>', lambda e: (clique(e), confirmar(e))[1])
        lista.bind('<KeyPress>', letra, add='+')
        topo.bind('<Escape>', cancelar)
        topo.protocol('WM_DELETE_WINDOW', cancelar)
        topo.grab_set()
        topo.update_idletasks()
        topo.geometry(f'+{self.winfo_rootx()}+{self.winfo_rooty() + self.winfo_height()}')
        lista.focus_set()


class CampoData(ttk.Entry):
    """Data DD/MM/AA com separadores fixos e substituição de dígitos."""
    POSICOES = (0, 1, 3, 4, 6, 7)

    def __init__(self, parent, variavel, **kwargs):
        super().__init__(parent, textvariable=variavel, **kwargs)
        self.variavel = variavel
        self.colocar_hoje()
        # Captura no próprio Entry antes do comportamento padrão de inserção.
        # Retornar 'break' impede o Tk de deslocar o texto da máscara.
        self.bind('<ButtonRelease-1>', self._clicar_cursor)
        self.bind('<FocusIn>', self._foco)
        self.bind('<<Paste>>', self._colar)
        self.bind('<Control-v>', self._colar)
        self.bind('<Control-V>', self._colar)
        self.bind('<<Cut>>', lambda _e: 'break')

    def colocar_hoje(self):
        self.variavel.set(datetime.now().strftime('%d/%m/%y'))
        self.after_idle(lambda: self.icursor(0) if self.winfo_exists() else None)

    def definir_data(self, valor):
        """Aceita formato novo e registros antigos DD/MM/AAAA."""
        try:
            formato = '%d/%m/%Y' if re.fullmatch(r'\d{2}/\d{2}/\d{4}', valor) else '%d/%m/%y'
            self.variavel.set(datetime.strptime(valor, formato).strftime('%d/%m/%y'))
        except (TypeError, ValueError):
            self.variavel.set('__/__/__')
        self.icursor(0)

    def _foco(self, _evento=None):
        # Desmarca a data pré-selecionada e começa no primeiro dígito.
        def posicionar():
            if self.winfo_exists():
                self.selection_clear()
                self.icursor(0)
        self.after_idle(posicionar)

    def _clicar_cursor(self, evento):
        self.focus_set()
        # Cursor de entrada em Entry sem os bindings padrão de TEntry.
        self.icursor(self.index(f'@{evento.x}'))
        self._ajustar_cursor()
        return 'break'

    def _ajustar_cursor(self, _evento=None):
        self.selection_clear()
        pos = self.index(tk.INSERT)
        proxima = next((p for p in self.POSICOES if p >= pos), self.POSICOES[-1])
        self.icursor(proxima)

    def _destino(self, pos, direcao=1):
        if direcao >= 0:
            return next((p for p in self.POSICOES if p >= pos), None)
        return next((p for p in reversed(self.POSICOES) if p <= pos), None)

    def _trocar(self, pos, caractere):
        atual = self.variavel.get()
        if len(atual) != 8 or atual[2] != '/' or atual[5] != '/':
            atual = '__/__/__'
        novo = atual[:pos] + caractere + atual[pos + 1:]
        self.variavel.set(novo)

    def _tecla(self, evento):
        if evento.keysym in ('Return', 'KP_Enter', 'Up', 'Down', 'Tab', 'ISO_Left_Tab', 'F2', 'F12', 'Escape', 'space'):
            return None
        if evento.keysym == 'Insert':
            # A máscara já opera permanentemente em modo sobrescrever.
            return 'break'
        if evento.state & 0x4 and evento.keysym.lower() in ('v', 'c', 'a', 'x'):
            if evento.keysym.lower() == 'v':
                return self._colar()
            if evento.keysym.lower() in ('x', 'a'):
                return 'break'
            return None
        pos = self.index(tk.INSERT)
        if evento.char and evento.char.isascii() and evento.char.isdigit():
            # Substitui um único caractere, inclusive se havia texto selecionado.
            self.selection_clear()
            alvo = self._destino(pos)
            if alvo is None:
                alvo = self.POSICOES[-1]
            self._trocar(alvo, evento.char)
            seguinte = self._destino(alvo + 1)
            self.icursor(seguinte if seguinte is not None else 8)
            return 'break'
        if evento.keysym in ('BackSpace', 'Delete'):
            alvo = self._destino(pos - 1, -1) if evento.keysym == 'BackSpace' else self._destino(pos)
            if alvo is not None:
                self._trocar(alvo, '_')
                self.icursor(alvo)
            return 'break'
        if evento.keysym == 'Left':
            alvo = self._destino(pos - 1, -1)
            self.icursor(0 if alvo is None else alvo)
            return 'break'
        if evento.keysym == 'Right':
            alvo = self._destino(pos + 1)
            self.icursor(8 if alvo is None else alvo)
            return 'break'
        if evento.keysym == 'Home':
            self.icursor(0)
            return 'break'
        if evento.keysym == 'End':
            self.icursor(8)
            return 'break'
        if evento.char and evento.char.isprintable():
            self.bell()
            return 'break'
        return None

    def _colar(self, _evento=None):
        try:
            texto = self.clipboard_get().strip()
        except tk.TclError:
            return 'break'
        if re.fullmatch(r'\d{2}/\d{2}/\d{4}', texto):
            texto = texto[:6] + texto[-2:]
        if re.fullmatch(r'\d{2}/\d{2}/\d{2}', texto):
            self.variavel.set(texto)
            self.icursor(0)
        elif re.fullmatch(r'\d{6}', texto):
            self.variavel.set(f'{texto[:2]}/{texto[2:4]}/{texto[4:]}')
            self.icursor(0)
        else:
            self.bell()
        return 'break'


class AppContas(tk.Tk):
    def __init__(self, caminho='contas.txt'):
        super().__init__()
        self.title('Financeiro | Contas a pagar e receber')
        self.geometry('1120x690')
        self.minsize(850, 590)
        self.caminho = caminho
        self.contas = carregar_contas(self.caminho)
        self.id_selecionado = None
        self._montar_interface()
        self.atualizar_tabela()
        self.after(100, self.campos[0].focus_set)

    def _montar_interface(self):
        estilo = ttk.Style(self)
        if 'clam' in estilo.theme_names():
            estilo.theme_use('clam')
        estilo.configure('Titulo.TLabel', font=('Segoe UI', 18, 'bold'))
        estilo.configure('Dica.TLabel', foreground='#496579')
        estilo.configure('Total.TLabel', font=('Segoe UI', 12, 'bold'))

        tela = ttk.Frame(self, padding=18)
        tela.pack(fill='both', expand=True)
        ttk.Label(tela, text='CONTROLE FINANCEIRO', style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(tela, text='Enter/↓: avançar   •   ↑: voltar (na descrição, lista)   •   F12: opções   •   Alt+S/N/E: ações',
                  style='Dica.TLabel').pack(anchor='w', pady=(2, 15))

        formulario = ttk.LabelFrame(tela, text='Cadastro de conta', padding=14)
        formulario.pack(fill='x')
        self.descricao = tk.StringVar()
        self.valor = tk.StringVar()
        self.tipo = tk.StringVar(value='')
        self.vencimento = tk.StringVar(value=datetime.now().strftime('%d/%m/%y'))
        self.status = tk.StringVar(value='')
        campos = [
            ('Descrição', ttk.Entry(formulario, textvariable=self.descricao, width=32)),
            ('Valor (R$)', ttk.Entry(formulario, textvariable=self.valor, width=16)),
            ('Tipo [R/D]  F12', CampoOpcao(formulario, self.tipo, TIPOS,
                                          {'R': 'Receita', 'D': 'Despesa'}, width=18)),
            ('Vencimento (DD/MM/AA)', CampoData(formulario, self.vencimento, width=21)),
            ('Status [P/A]  F12', CampoOpcao(formulario, self.status, STATUS_OPCOES,
                                            {'P': 'Pendente', 'A': 'Pago'}, width=18)),
        ]
        self.campos = [campo for _, campo in campos]
        for pos, (rotulo, campo) in enumerate(campos):
            ttk.Label(formulario, text=rotulo).grid(row=0, column=pos, sticky='w', padx=(0, 11))
            campo.grid(row=1, column=pos, sticky='w' if isinstance(campo, CampoOpcao) else 'ew', padx=(0, 11), pady=(5, 10), ipady=4)
            if isinstance(campo, CampoOpcao):
                campo.bind('<KeyPress>', lambda e: 'break' if e.char and e.char.isprintable() else None)
                for codigo in campo.codigos:
                    for letra in (codigo.lower(), codigo.upper()):
                        campo.bind('<KeyPress-' + letra + '>', lambda e, c=campo, v=codigo: self._digitar_opcao(c, v))
                campo.bind('<BackSpace>', lambda e, c=campo: self._digitar_opcao(c, ''))
                campo.bind('<Delete>', lambda e, c=campo: self._digitar_opcao(c, ''))
                campo.bind('<F12>', campo._abrir)
            elif isinstance(campo, CampoData):
                campo.bind('<KeyPress>', campo._tecla)
                for numero in '0123456789':
                    campo.bind('<KeyPress-' + numero + '>', lambda e, c=campo, n=numero: self._digitar_data(c, n))
                for tecla in ('BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End', 'Insert'):
                    campo.bind('<' + tecla + '>', campo._tecla)
            campo.bind('<Return>', lambda e, i=pos: self._enter_campo(i))
            campo.bind('<KP_Enter>', lambda e, i=pos: self._enter_campo(i))
            campo.bind('<Down>', lambda e, i=pos: self._enter_campo(i))
            campo.bind('<Up>', lambda e, i=pos: self._subir_campo(i))
            # Espaço normal na descrição; não altera os campos restritos.
            if pos != 0:
                campo.bind('<space>', lambda e: 'break')
            for letra, acao in (('s', self.salvar_formulario), ('n', self.limpar), ('e', self.excluir)):
                for l in (letra, letra.upper()):
                    campo.bind(f'<Alt-KeyPress-{l}>', lambda e, cmd=acao: self._atalho_alt(cmd))
        formulario.columnconfigure(0, weight=3)
        for col in range(1, 5):
            formulario.columnconfigure(col, weight=1)
        botoes = ttk.Frame(formulario)
        botoes.grid(row=2, column=0, columnspan=5, sticky='w', pady=(6, 0))
        # O atributo underline usa índice baseado em zero. O Tk desenha
        # a letra indicada sublinhada e a tecla Alt correspondente executa.
        self.botao_salvar = ttk.Button(botoes, text='Salvar / atualizar (Alt+S)',
                                       underline=0, command=self.salvar_formulario)
        self.botao_salvar.pack(side='left', padx=(0, 8))
        self.botao_novo = ttk.Button(botoes, text='Novo / limpar (Alt+N)',
                                     underline=0, command=self.limpar)
        self.botao_novo.pack(side='left', padx=(0, 8))
        self.botao_excluir = ttk.Button(botoes, text='Excluir selecionada (Alt+E)',
                                        underline=0, command=self.excluir)
        self.botao_excluir.pack(side='left')
        self.mensagem = tk.StringVar(value='Preencha os campos. As escolhas começam vazias para exigir seleção válida.')
        ttk.Label(formulario, textvariable=self.mensagem, style='Dica.TLabel').grid(
            row=3, column=0, columnspan=5, sticky='w', pady=(10, 0))

        lista = ttk.LabelFrame(tela, text='Contas cadastradas (clique para editar)', padding=10)
        lista.pack(fill='both', expand=True, pady=(15, 10))
        colunas = ('id', 'descricao', 'valor', 'tipo', 'vencimento', 'status')
        self.tabela = ttk.Treeview(lista, columns=colunas, show='headings', selectmode='browse')
        titulos = ('ID', 'Descrição', 'Valor', 'Tipo', 'Vencimento', 'Status')
        larguras = (55, 295, 120, 115, 135, 110)
        for col, titulo, largura in zip(colunas, titulos, larguras):
            self.tabela.heading(col, text=titulo)
            self.tabela.column(col, width=largura, minwidth=55,
                               anchor='w' if col == 'descricao' else 'center')
        barra = ttk.Scrollbar(lista, orient='vertical', command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra.set)
        self.tabela.pack(side='left', fill='both', expand=True)
        barra.pack(side='right', fill='y')
        self.tabela.bind('<<TreeviewSelect>>', self.selecionar)
        self.tabela.bind('<Delete>', lambda _e: self.excluir())
        self.tabela.bind('<Return>', self._abrir_registro_lista)
        self.tabela.bind('<KP_Enter>', self._abrir_registro_lista)
        self.tabela.bind('<Double-Button-1>', self._abrir_registro_lista)
        self.tabela.bind('<space>', lambda _e: 'break')
        self.tabela.bind('<Escape>', self._sair_lista)

        resumo = ttk.LabelFrame(tela, text='Resumo financeiro (todas as contas)', padding=13)
        resumo.pack(fill='x')
        self.texto_receitas = ttk.Label(resumo, style='Total.TLabel')
        self.texto_receitas.pack(side='left', padx=(0, 38))
        self.texto_despesas = ttk.Label(resumo, style='Total.TLabel')
        self.texto_despesas.pack(side='left', padx=(0, 38))
        self.texto_saldo = ttk.Label(resumo, style='Total.TLabel')
        self.texto_saldo.pack(side='left')
        self.bind('<F2>', lambda _e: self.salvar_formulario())
        self.bind('<Escape>', self._esc_geral)
        for letra, comando in (('s', self.salvar_formulario), ('n', self.limpar), ('e', self.excluir)):
            self.bind(f'<Alt-KeyPress-{letra}>', lambda _evento, cmd=comando: self._atalho_alt(cmd))
            self.bind(f'<Alt-KeyPress-{letra.upper()}>', lambda _evento, cmd=comando: self._atalho_alt(cmd))

    @staticmethod
    def _digitar_opcao(campo, codigo):
        campo.variavel.set(codigo)
        campo.icursor(tk.END)
        return 'break'

    @staticmethod
    def _digitar_data(campo, numero):
        campo.selection_clear()
        alvo = campo._destino(campo.index(tk.INSERT))
        if alvo is None:
            alvo = campo.POSICOES[-1]
        campo._trocar(alvo, numero)
        seguinte = campo._destino(alvo + 1)
        campo.icursor(seguinte if seguinte is not None else 8)
        return 'break'

    def _atalho_alt(self, comando):
        # Não aciona botões da janela principal com a consulta F12 aberta.
        if self.grab_current() is not None and self.grab_current() is not self:
            return 'break'
        comando()
        return 'break'

    def _focar_lista(self):
        itens = self.tabela.get_children()
        if not itens:
            self.tabela.focus_set()
            self.mensagem.set('Não há contas cadastradas. Esc volta ao formulário.')
            return 'break'
        selecionado = self.tabela.selection()
        alvo = selecionado[0] if selecionado else itens[0]
        self.tabela.selection_set(alvo)
        self.tabela.focus(alvo)
        self.tabela.see(alvo)
        self.tabela.focus_set()
        self.mensagem.set('Contas cadastradas: ↑/↓ navegam; Enter edita; Esc retorna ao formulário.')
        return 'break'

    def _abrir_registro_lista(self, _evento=None):
        selecionado = self.tabela.selection()
        if selecionado:
            self.selecionar()
            self.campos[0].focus_set()
        return 'break'

    def _sair_lista(self, _evento=None):
        self.campos[0].focus_set()
        return 'break'

    def _esc_geral(self, evento):
        if isinstance(evento.widget, tk.Toplevel):
            return
        self.limpar()

    def _validar_campo(self, indice):
        if indice == 0:
            texto = self.descricao.get().strip()
            if not texto or ';' in texto or '\n' in texto:
                raise ValueError('Descrição obrigatória, sem ponto e vírgula.')
            return texto
        if indice == 1:
            texto = self.valor.get().strip().replace('R$', '').replace(' ', '')
            if not texto:
                raise ValueError('Informe o valor da conta.')
            # Aceita 1234,56 / 1234.56 / 1.234,56
            if ',' in texto and '.' in texto:
                texto = texto.replace('.', '').replace(',', '.')
            else:
                texto = texto.replace(',', '.')
            try:
                numero = float(texto)
            except ValueError:
                raise ValueError('O valor precisa ser numérico (ex.: 150,50).') from None
            if not math.isfinite(numero) or numero <= 0:
                raise ValueError('O valor deve ser maior que zero e finito.')
            return numero
        if indice == 2:
            if self.tipo.get() not in ('R', 'D'):
                raise ValueError('Escolha R (Receita) ou D (Despesa). Pressione F12 para consultar.')
            return {'R': 'Receita', 'D': 'Despesa'}[self.tipo.get()]
        if indice == 3:
            texto = self.vencimento.get().strip()
            if not re.fullmatch(r'\d{2}/\d{2}/\d{2}', texto):
                raise ValueError('Preencha o vencimento em DD/MM/AA.')
            try:
                data = datetime.strptime(texto, '%d/%m/%y')
                if data.strftime('%d/%m/%y') != texto:
                    raise ValueError
            except ValueError:
                raise ValueError('Data de vencimento inválida.') from None
            return texto
        if indice == 4:
            if self.status.get() not in ('P', 'A'):
                raise ValueError('Escolha P (Pendente) ou A (Pago). Pressione F12 para consultar.')
            return {'P': 'Pendente', 'A': 'Pago'}[self.status.get()]
        raise IndexError(indice)

    def _erro(self, indice, mensagem):
        self.mensagem.set('ERRO: ' + mensagem)
        messagebox.showwarning('Campo inválido', mensagem, parent=self)
        self.campos[indice].focus_set()
        if isinstance(self.campos[indice], ttk.Entry) and not isinstance(self.campos[indice], (CampoOpcao, CampoData)):
            self.campos[indice].selection_range(0, 'end')

    def _subir_campo(self, indice):
        if indice == 0:
            return self._focar_lista()
        if indice > 0:
            self.campos[indice - 1].focus_set()
        return 'break'

    def _enter_campo(self, indice):
        try:
            self._validar_campo(indice)
        except ValueError as erro:
            self._erro(indice, str(erro))
            return 'break'
        self.mensagem.set('Campo validado.')
        if indice + 1 < len(self.campos):
            self.campos[indice + 1].focus_set()
        else:
            self.salvar_formulario()
        return 'break'

    def _validar(self):
        dados = []
        for indice in range(len(self.campos)):
            try:
                dados.append(self._validar_campo(indice))
            except ValueError as erro:
                self._erro(indice, str(erro))
                return None
        return tuple(dados)

    def _salvar(self):
        try:
            salvar_contas(self.contas, self.caminho)
        except OSError as erro:
            messagebox.showerror('Erro ao salvar', f'Não foi possível salvar contas.txt:\n{erro}', parent=self)
            return False
        return True

    def salvar_formulario(self):
        dados = self._validar()
        if dados is None:
            return
        # Se a gravação falhar, a lista em memória também é restaurada.
        anterior = [c.copy() for c in self.contas]
        editando = self.id_selecionado is not None
        if editando:
            if not atualizar_conta(self.contas, self.id_selecionado, *dados):
                messagebox.showerror('Conta não encontrada', 'A conta selecionada não existe mais.', parent=self)
                return
        else:
            adicionar_conta(self.contas, *dados)
        if not self._salvar():
            self.contas = anterior
            return
        self.atualizar_tabela()
        self.limpar()
        self.mensagem.set('Conta atualizada.' if editando else 'Conta cadastrada.')
        self.campos[0].focus_set()

    def adicionar(self):
        """Compatibilidade com a versão anterior."""
        self.salvar_formulario()

    def atualizar(self):
        if self.id_selecionado is None:
            messagebox.showwarning('Seleção', 'Selecione uma conta na tabela.', parent=self)
            return
        self.salvar_formulario()

    def atualizar_tabela(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)
        for c in self.contas:
            self.tabela.insert('', 'end', iid=str(c['id']), values=(
                c['id'], c['descricao'], moeda(c['valor']), c['tipo'], c['vencimento'], c['status']))
        receitas, despesas, saldo = calcular_resumo(self.contas)
        self.texto_receitas.config(text='Receitas: ' + moeda(receitas))
        self.texto_despesas.config(text='Despesas: ' + moeda(despesas))
        self.texto_saldo.config(text='Saldo: ' + moeda(saldo))

    def limpar(self):
        self.id_selecionado = None
        for var in (self.descricao, self.valor, self.tipo, self.status):
            var.set('')
        self.campos[3].colocar_hoje()
        if self.tabela.selection():
            self.tabela.selection_remove(self.tabela.selection())
        self.mensagem.set('Novo cadastro. Preencha os campos e pressione Enter para avançar.')
        self.campos[0].focus_set()

    def selecionar(self, _evento=None):
        selecionados = self.tabela.selection()
        if not selecionados:
            return
        conta = next((c for c in self.contas if c['id'] == int(selecionados[0])), None)
        if conta is None:
            return
        self.id_selecionado = conta['id']
        self.descricao.set(conta['descricao'])
        self.valor.set(f"{conta['valor']:.2f}".replace('.', ','))
        self.tipo.set({'Receita': 'R', 'Despesa': 'D'}.get(conta['tipo'], ''))
        self.campos[3].definir_data(conta['vencimento'])
        self.status.set({'Pendente': 'P', 'Pago': 'A'}.get(conta['status'], ''))
        self.mensagem.set(f"Editando conta nº {conta['id']}. Enter no último campo ou F2 salva a alteração.")
        # A tabela conserva o foco para permitir navegação com setas.

    def excluir(self):
        if self.id_selecionado is None:
            messagebox.showwarning('Seleção', 'Selecione uma conta na tabela.', parent=self)
            return
        if not messagebox.askyesno('Confirmar exclusão', 'Excluir a conta selecionada?', parent=self):
            return
        anterior = [c.copy() for c in self.contas]
        excluir_conta(self.contas, self.id_selecionado)
        if not self._salvar():
            self.contas = anterior
            return
        self.atualizar_tabela()
        self.limpar()
        self.mensagem.set('Conta excluída.')
