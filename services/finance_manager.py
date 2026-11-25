"""Operações de contas a pagar e receber, sem banco de dados."""
from pathlib import Path

TIPOS = ('Receita', 'Despesa')
STATUS_OPCOES = ('Pendente', 'Pago')
CAMPOS = ('id', 'descricao', 'valor', 'tipo', 'vencimento', 'status')


def carregar_contas(caminho='contas.txt'):
    """Lê contas do TXT (id;descricao;valor;tipo;vencimento;status)."""
    contas = []
    try:
        with open(caminho, 'r', encoding='utf-8') as arq:
            for numero_linha, linha in enumerate(arq, start=1):
                dados = linha.strip().split(';')
                if len(dados) != 6:
                    continue
                try:
                    conta = {
                        'id': int(dados[0]), 'descricao': dados[1],
                        'valor': float(dados[2]), 'tipo': dados[3],
                        'vencimento': dados[4], 'status': dados[5]
                    }
                    if (conta['tipo'] in TIPOS and conta['status'] in STATUS_OPCOES
                            and conta['valor'] > 0 and conta['descricao'].strip()
                            and not any(c['id'] == conta['id'] for c in contas)):
                        contas.append(conta)
                except (ValueError, IndexError):
                    continue
    except FileNotFoundError:
        pass
    return contas


def salvar_contas(contas, caminho='contas.txt'):
    """Regrava todos os registros no TXT."""
    with open(caminho, 'w', encoding='utf-8') as arq:
        for conta in contas:
            descricao = conta['descricao'].replace(';', ',').replace('\n', ' ')
            linha = f"{conta['id']};{descricao};{conta['valor']:.2f};{conta['tipo']};{conta['vencimento']};{conta['status']}\n"
            arq.write(linha)


def proximo_id(contas):
    return max((c['id'] for c in contas), default=0) + 1


def calcular_resumo(contas):
    """Calcula receitas, despesas e saldo (receitas - despesas)."""
    rec = sum(c['valor'] for c in contas if c['tipo'] == 'Receita')
    desp = sum(c['valor'] for c in contas if c['tipo'] == 'Despesa')
    return rec, desp, rec - desp


def adicionar_conta(contas, descricao, valor, tipo, vencimento, status):
    conta = {'id': proximo_id(contas), 'descricao': descricao, 'valor': valor,
             'tipo': tipo, 'vencimento': vencimento, 'status': status}
    contas.append(conta)
    return conta


def atualizar_conta(contas, identificador, descricao, valor, tipo, vencimento, status):
    for conta in contas:
        if conta['id'] == identificador:
            conta.update(descricao=descricao, valor=valor, tipo=tipo,
                         vencimento=vencimento, status=status)
            return True
    return False


def excluir_conta(contas, identificador):
    for i, conta in enumerate(contas):
        if conta['id'] == identificador:
            contas.pop(i)
            return True
    return False
