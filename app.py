from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
import calendar

app = Flask(__name__)

def get_quarter_data():
    return [
        {
            "name": "1º Trimestre",
            "previsto": "528:00",
            "trabalhado": "532:00",
            "saldo": "+4:00",
            "months": ["Jan", "Fev", "Mar"]
        },
        {
            "name": "2º Trimestre",
            "previsto": "528:00",
            "trabalhado": "520:00",
            "saldo": "-8:00",
            "months": ["Abr", "Mai", "Jun"]
        },
        {
            "name": "3º Trimestre",
            "previsto": "528:00",
            "trabalhado": "528:00",
            "saldo": "0:00",
            "months": ["Jul", "Ago", "Set"]
        },
        {
            "name": "4º Trimestre",
            "previsto": "528:00",
            "trabalhado": "530:00",
            "saldo": "+2:00",
            "months": ["Out", "Nov", "Dez"]
        }
    ]

def get_month_data():
    return [
        {"month": "Jan", "previsto": "176:00", "trabalhado": "178:00", "saldo": "+2:00"},
        {"month": "Fev", "previsto": "176:00", "trabalhado": "175:00", "saldo": "-1:00"},
        {"month": "Mar", "previsto": "176:00", "trabalhado": "179:00", "saldo": "+3:00"},
        {"month": "Abr", "previsto": "176:00", "trabalhado": "176:00", "saldo": "0:00"},
        {"month": "Mai", "previsto": "176:00", "trabalhado": "174:00", "saldo": "-2:00"},
        {"month": "Jun", "previsto": "176:00", "trabalhado": "170:00", "saldo": "-6:00"},
        {"month": "Jul", "previsto": "176:00", "trabalhado": "176:00", "saldo": "0:00"},
        {"month": "Ago", "previsto": "176:00", "trabalhado": "176:00", "saldo": "0:00"},
        {"month": "Set", "previsto": "176:00", "trabalhado": "176:00", "saldo": "0:00"},
        {"month": "Out", "previsto": "176:00", "trabalhado": "177:00", "saldo": "+1:00"},
        {"month": "Nov", "previsto": "176:00", "trabalhado": "177:00", "saldo": "+1:00"},
        {"month": "Dez", "previsto": "176:00", "trabalhado": "176:00", "saldo": "0:00"}
    ]

# Dados simulados para a página de detalhes do mês
meses_dados = {
    '2024': {
        '1': {
            'previsto': '168h',
            'trabalhado': '170h',
            'saldo': '+2h',
            'turnos': [
                {'id': 1, 'data': '15/01/2024', 'hora_inicial': '08:00', 'hora_final': '17:00', 'descricao': 'Trabalho normal'},
                {'id': 2, 'data': '16/01/2024', 'hora_inicial': '08:00', 'hora_final': '18:00', 'descricao': 'Hora extra projeto X'}
            ],
            'dias_nao_contabeis': [
                {'id': 1, 'data': '01/01/2024', 'tipo': 'outros'},
                {'id': 2, 'data': '02/01/2024', 'tipo': 'ferias'}
            ]
        }
    }
}

@app.route('/')
def index():
    current_year = datetime.now().year
    current_month = datetime.now().month
    quarter_data = get_quarter_data()
    month_data = get_month_data()
    return render_template('index.html', 
                         year=current_year,
                         current_month=current_month,
                         quarter_data=quarter_data,
                         month_data=month_data)

@app.route('/mes/<int:mes>')
def mes_detalhe(mes):
    ano = datetime.now().year
    ano_str = str(ano)
    mes_str = str(mes)
    
    # Get month name in Portuguese
    meses_nomes = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    nome_mes = meses_nomes[mes]
    
    # Se o mês não existe nos dados, cria uma estrutura vazia
    if ano_str not in meses_dados:
        meses_dados[ano_str] = {}
    if mes_str not in meses_dados[ano_str]:
        meses_dados[ano_str][mes_str] = {
            'previsto': '0h',
            'trabalhado': '0h',
            'saldo': '0h',
            'turnos': [],
            'dias_nao_contabeis': []
        }
    
    mes_data = meses_dados[ano_str][mes_str]
    
    # Calcula os dias do mês
    total_dias = calendar.monthrange(ano, mes)[1]
    dias_nao_contabeis = len(mes_data.get('dias_nao_contabeis', []))  # Pega a lista de dias não contábeis
    dias_previstos = total_dias - dias_nao_contabeis
    
    # Adiciona as informações de dias ao mes_data
    mes_data['total_dias'] = total_dias
    mes_data['dias_nao_contabeis_count'] = dias_nao_contabeis  # Número de dias não contábeis
    mes_data['dias_previstos'] = dias_previstos

    # Ordenar dias não contábeis e turnos em ordem decrescente por data
    turnos_ordenados = sorted(mes_data['turnos'], 
                            key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y'), 
                            reverse=True)
    
    dias_nao_contabeis_ordenados = sorted(mes_data['dias_nao_contabeis'], 
                                        key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y'), 
                                        reverse=True)
    
    return render_template('mes.html', 
                         mes=mes,
                         ano=ano,
                         nome_mes=nome_mes,
                         mes_data=mes_data,
                         turnos=turnos_ordenados,
                         dias_nao_contabeis=dias_nao_contabeis_ordenados)

@app.route('/lancar_turno', methods=['POST'])
def lancar_turno():
    mes = request.form['mes']
    ano = request.form['ano']
    data = datetime.strptime(request.form['data'], '%Y-%m-%d').strftime('%d/%m/%Y')  # Converte para o formato dd/mm/yyyy
    hora_inicial = request.form['hora_inicial']
    hora_final = request.form['hora_final']
    descricao = request.form['descricao']
    
    # Gera um ID único para o novo turno (em produção, isso seria feito pelo banco de dados)
    novo_id = max([t['id'] for t in meses_dados[ano][mes]['turnos']], default=0) + 1
    
    # Adiciona o novo turno
    novo_turno = {
        'id': novo_id,
        'data': data,
        'hora_inicial': hora_inicial,
        'hora_final': hora_final,
        'descricao': descricao
    }
    meses_dados[ano][mes]['turnos'].append(novo_turno)
    
    return redirect(url_for('mes_detalhe', mes=int(mes)))

@app.route('/lancar_dia_nao_contabil', methods=['POST'])
def lancar_dia_nao_contabil():
    mes = request.form['mes']
    ano = request.form['ano']
    dias = request.form['dias'].split(',')  # O flatpickr envia múltiplas datas separadas por vírgula
    tipo = request.form['tipo']
    
    for data in dias:
        # Converte a data para o formato dd/mm/yyyy
        data_formatada = datetime.strptime(data.strip(), '%Y-%m-%d').strftime('%d/%m/%Y')
        
        # Gera um ID único para o novo dia não contábil
        novo_id = max([d['id'] for d in meses_dados[ano][mes]['dias_nao_contabeis']], default=0) + 1
        
        # Adiciona o novo dia não contábil
        novo_dia = {
            'id': novo_id,
            'data': data_formatada,
            'tipo': tipo
        }
        meses_dados[ano][mes]['dias_nao_contabeis'].append(novo_dia)
    
    return redirect(url_for('mes_detalhe', mes=int(mes)))

if __name__ == '__main__':
    app.run(debug=True)