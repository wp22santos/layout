from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import calendar
from functools import wraps
from supabase import create_client
from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Verifica se as variáveis de ambiente necessárias estão presentes
required_env_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_SERVICE_ROLE_KEY']
for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"Variável de ambiente {var} não encontrada")

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Inicializa o cliente Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# Cliente com service_role para operações administrativas
service_role_client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

def create_users_table():
    try:
        # Verifica se a tabela existe
        supabase.table('users').select('*').limit(1).execute()
        print("Tabela 'users' já existe")
    except Exception as e:
        if "'public.users' does not exist" in str(e):
            try:
                # Cria a tabela users usando SQL
                supabase.postgrest.rpc('create_users_table', {}).execute()
                print("Tabela 'users' criada com sucesso")
            except Exception as create_error:
                print(f"Erro ao criar tabela: {str(create_error)}")

# Tenta criar a tabela users ao iniciar a aplicação
create_users_table()

# Decorator para verificar se o usuário está logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def parse_date(date_str):
    """Tenta converter uma string de data para objeto datetime"""
    formats = ['%d/%m/%Y', '%Y-%m-%d']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Data '{date_str}' não está em um formato válido")

def format_date(date_obj):
    """Converte um objeto datetime para string no formato DD/MM/YYYY"""
    return date_obj.strftime('%d/%m/%Y')

def parse_time(time_str):
    """Tenta converter uma string de hora para objeto datetime"""
    formats = ['%H:%M', '%H:%M:%S', '%H:%M:00']
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Hora '{time_str}' não está em um formato válido")

def format_time(time_obj):
    """Converte um objeto datetime para string no formato HH:MM"""
    return time_obj.strftime('%H:%M')

def get_quarter_data(user_id, year):
    try:
        # Inicializa dados dos trimestres
        quarters = [
            {"name": "1º Trimestre", "months": [1, 2, 3], "previsto": "0:00", "trabalhado": "0:00", "saldo": "0:00"},
            {"name": "2º Trimestre", "months": [4, 5, 6], "previsto": "0:00", "trabalhado": "0:00", "saldo": "0:00"},
            {"name": "3º Trimestre", "months": [7, 8, 9], "previsto": "0:00", "trabalhado": "0:00", "saldo": "0:00"},
            {"name": "4º Trimestre", "months": [10, 11, 12], "previsto": "0:00", "trabalhado": "0:00", "saldo": "0:00"}
        ]

        # Busca todos os turnos do usuário para o ano especificado
        turnos = supabase.table('turnos').select('*').eq('user_id', user_id).execute()
        turnos = turnos.data if turnos.data else []

        # Busca dias não contábeis
        dias_nao_contabeis = supabase.table('dias_nao_contabeis').select('*').eq('user_id', user_id).execute()
        dias_nao_contabeis = dias_nao_contabeis.data if dias_nao_contabeis.data else []

        # Processa os turnos
        for turno in turnos:
            try:
                data = parse_date(turno['data'])
                if data.year == year:
                    # Calcula horas trabalhadas
                    inicio = parse_time(turno['hora_inicial'])
                    fim = parse_time(turno['hora_final'])
                    horas_trabalhadas = (fim - inicio).total_seconds() / 3600

                    # Adiciona ao trimestre correspondente
                    quarter_index = (data.month - 1) // 3
                    current_hours = float(str(quarters[quarter_index]["trabalhado"]).split(':')[0])
                    quarters[quarter_index]["trabalhado"] = current_hours + horas_trabalhadas
            except (ValueError, KeyError, IndexError) as e:
                print(f"Erro ao processar turno: {str(e)}")
                continue

        # Processa dias não contábeis e calcula horas previstas
        for quarter in quarters:
            dias_uteis_total = 0
            for month_num in quarter["months"]:
                total_dias = calendar.monthrange(year, month_num)[1]
                dias_nao_contabeis_mes = sum(1 for d in dias_nao_contabeis 
                                           if parse_date(d['data']).month == month_num 
                                           and parse_date(d['data']).year == year)
                dias_uteis = total_dias - dias_nao_contabeis_mes
                dias_uteis_total += dias_uteis
            
            # Calcula horas previstas (8 horas por dia útil)
            horas_previstas = dias_uteis_total * 8
            
            # Converte string para float para cálculos
            try:
                horas_trabalhadas = float(str(quarter["trabalhado"]).split(':')[0])
            except (ValueError, AttributeError):
                horas_trabalhadas = quarter["trabalhado"] if isinstance(quarter["trabalhado"], (int, float)) else 0
            
            # Calcula saldo
            saldo = horas_trabalhadas - horas_previstas
            
            # Formata as horas
            quarter["previsto"] = f"{int(horas_previstas)}:{int((horas_previstas % 1) * 60):02d}"
            quarter["trabalhado"] = f"{int(horas_trabalhadas)}:{int((horas_trabalhadas % 1) * 60):02d}"
            quarter["saldo"] = f"{'+' if saldo >= 0 else ''}{int(saldo)}:{int(abs(saldo % 1) * 60):02d}"

        return quarters
    except Exception as e:
        print(f"Erro ao buscar dados dos trimestres: {str(e)}")
        return [
            {"name": "1º Trimestre", "months": [1, 2, 3], "previsto": "0:00", "trabalhado": "0:00", "saldo": "0:00"},
            {"name": "2º Trimestre", "months": [4, 5, 6], "previsto": "0:00", "trabalhado": "0:00", "saldo": "0:00"},
            {"name": "3º Trimestre", "months": [7, 8, 9], "previsto": "0:00", "trabalhado": "0:00", "saldo": "0:00"},
            {"name": "4º Trimestre", "months": [10, 11, 12], "previsto": "0:00", "trabalhado": "0:00", "saldo": "0:00"}
        ]

def get_month_data(user_id, year):
    try:
        # Inicializa dados dos meses
        meses_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", 
                      "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        months = []

        # Busca todos os turnos do usuário para o ano especificado
        turnos = supabase.table('turnos').select('*').eq('user_id', user_id).execute()
        turnos = turnos.data if turnos.data else []

        # Busca dias não contábeis
        dias_nao_contabeis = supabase.table('dias_nao_contabeis').select('*').eq('user_id', user_id).execute()
        dias_nao_contabeis = dias_nao_contabeis.data if dias_nao_contabeis.data else []

        for month_num in range(1, 13):
            # Calcula dias úteis
            total_dias = calendar.monthrange(year, month_num)[1]
            dias_nao_contabeis_mes = sum(1 for d in dias_nao_contabeis 
                                       if parse_date(d['data']).month == month_num
                                       and parse_date(d['data']).year == year)
            dias_uteis = total_dias - dias_nao_contabeis_mes
            
            # Calcula horas previstas (8 horas por dia útil)
            horas_previstas = dias_uteis * 8

            # Calcula horas trabalhadas
            horas_trabalhadas = 0
            for t in turnos:
                try:
                    if parse_date(t['data']).month == month_num and parse_date(t['data']).year == year:
                        inicio = parse_time(t['hora_inicial'])
                        fim = parse_time(t['hora_final'])
                        horas_trabalhadas += (fim - inicio).total_seconds() / 3600
                except (ValueError, KeyError) as e:
                    print(f"Erro ao processar turno: {str(e)}")
                    continue

            # Calcula saldo
            saldo = horas_trabalhadas - horas_previstas

            # Formata as horas
            month_data = {
                "month": meses_nomes[month_num - 1],
                "previsto": f"{int(horas_previstas)}:{int((horas_previstas % 1) * 60):02d}",
                "trabalhado": f"{int(horas_trabalhadas)}:{int((horas_trabalhadas % 1) * 60):02d}",
                "saldo": f"{'+' if saldo >= 0 else ''}{int(saldo)}:{int(abs(saldo % 1) * 60):02d}"
            }
            months.append(month_data)

        return months
    except Exception as e:
        print(f"Erro ao buscar dados dos meses: {str(e)}")
        return [{"month": m, "previsto": "0:00", "trabalhado": "0:00", "saldo": "0:00"} 
                for m in ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", 
                         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]]

def get_month_detail(user_id, year, month):
    try:
        # Busca turnos do mês
        turnos = supabase.table('turnos')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        
        # Filtra turnos do mês específico e converte datas
        turnos_processados = []
        for t in (turnos.data or []):
            try:
                if parse_date(t['data']).month == month and parse_date(t['data']).year == year:
                    turno_processado = {**t}
                    turno_processado['data'] = format_date(parse_date(t['data']))
                    turno_processado['hora_inicial'] = format_time(parse_time(t['hora_inicial']))
                    turno_processado['hora_final'] = format_time(parse_time(t['hora_final']))
                    turnos_processados.append(turno_processado)
            except (ValueError, KeyError) as e:
                print(f"Erro ao processar turno: {str(e)}")
                continue

        # Busca dias não contábeis do mês
        dias_nao_contabeis = supabase.table('dias_nao_contabeis')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        
        # Filtra dias não contábeis do mês específico e converte datas
        dias_nao_contabeis_processados = []
        for d in (dias_nao_contabeis.data or []):
            try:
                if parse_date(d['data']).month == month and parse_date(d['data']).year == year:
                    dia_processado = {**d}
                    dia_processado['data'] = format_date(parse_date(d['data']))
                    dias_nao_contabeis_processados.append(dia_processado)
            except (ValueError, KeyError) as e:
                print(f"Erro ao processar dia não contábil: {str(e)}")
                continue

        # Calcula total de dias e dias previstos
        total_dias = calendar.monthrange(year, month)[1]
        dias_nao_contabeis_count = len(dias_nao_contabeis_processados)
        dias_previstos = total_dias - dias_nao_contabeis_count

        # Calcula horas previstas e trabalhadas
        horas_previstas = dias_previstos * 8  # 8 horas por dia útil
        horas_trabalhadas = 0
        for t in turnos_processados:
            try:
                inicio = parse_time(t['hora_inicial'])
                fim = parse_time(t['hora_final'])
                horas_trabalhadas += (fim - inicio).total_seconds() / 3600
            except (ValueError, KeyError) as e:
                print(f"Erro ao calcular horas trabalhadas: {str(e)}")
                continue

        # Calcula saldo
        saldo = horas_trabalhadas - horas_previstas

        # Prepara dados do mês
        mes_data = {
            'previsto': f"{int(horas_previstas)}:{int((horas_previstas % 1) * 60):02d}",
            'trabalhado': f"{int(horas_trabalhadas)}:{int((horas_trabalhadas % 1) * 60):02d}",
            'saldo': f"{'+' if saldo >= 0 else ''}{int(saldo)}:{int(abs(saldo % 1) * 60):02d}",
            'total_dias': total_dias,
            'dias_nao_contabeis_count': dias_nao_contabeis_count,
            'dias_previstos': dias_previstos,
            'turnos': sorted(turnos_processados, key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y'), reverse=True),
            'dias_nao_contabeis': sorted(dias_nao_contabeis_processados, key=lambda x: datetime.strptime(x['data'], '%d/%m/%Y'), reverse=True)
        }

        return mes_data
    except Exception as e:
        print(f"Erro ao buscar detalhes do mês: {str(e)}")
        return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Autenticação com Supabase
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            session['user_id'] = response.user.id
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash('Email ou senha inválidos!', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            print("=== Iniciando processo de registro ===")
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            
            print(f"Dados recebidos - Nome: {name}, Email: {email}, Tamanho da senha: {len(password)} caracteres")
            
            # Validações básicas
            if not name or not email or not password:
                print("Erro: Campos obrigatórios faltando")
                flash('Todos os campos são obrigatórios.', 'error')
                return render_template('register.html')
            
            if len(password) < 6:
                print("Erro: Senha muito curta")
                flash('A senha deve ter pelo menos 6 caracteres.', 'error')
                return render_template('register.html')
            
            print("Iniciando registro no Supabase...")
            # Registro com Supabase
            try:
                # Primeiro, tenta criar o usuário na autenticação
                auth_response = supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "name": name
                        }
                    }
                })
                
                print(f"Resposta da autenticação Supabase: {auth_response}")
                
                if not auth_response.user or not auth_response.user.id:
                    print("Erro: Resposta da autenticação não contém ID do usuário")
                    flash('Erro ao registrar usuário. Por favor, tente novamente.', 'error')
                    return render_template('register.html')
                
                user_id = auth_response.user.id
                print(f"Usuário criado com sucesso. ID: {user_id}")
                
                try:
                    # Tenta criar o perfil do usuário usando service_role
                    print("Criando perfil do usuário na tabela 'users'...")
                    
                    # Insere os dados do usuário usando o client global com service_role
                    user_data = service_role_client.table('users').insert({
                        'id': user_id,
                        'name': name,
                        'email': email
                    }).execute()
                    
                    print("Perfil do usuário criado com sucesso")
                    
                except Exception as profile_error:
                    print(f"Erro ao criar perfil do usuário: {str(profile_error)}")
                    # Se falhar ao criar o perfil, ainda podemos prosseguir pois o usuário foi criado
                
                # Sempre exibe a mensagem de sucesso e redireciona
                flash('Registro realizado com sucesso! Por favor, verifique seu email para confirmar o cadastro.', 'success')
                return redirect(url_for('login'))
                
            except Exception as auth_error:
                error_msg = str(auth_error).lower()
                print(f"Erro na autenticação: {error_msg}")
                
                if "already registered" in error_msg:
                    flash('Este email já está registrado.', 'error')
                elif "rate limit" in error_msg or "security purposes" in error_msg:
                    flash('Por favor, aguarde alguns segundos antes de tentar novamente.', 'warning')
                else:
                    flash('Erro ao registrar usuário. Por favor, tente novamente.', 'error')
                return render_template('register.html')
                
        except Exception as e:
            print(f"=== Erro geral no registro ===")
            print(f"Tipo do erro: {type(e)}")
            print(f"Mensagem do erro: {str(e)}")
            print(f"Detalhes adicionais: {getattr(e, 'args', [])}")
            flash('Erro ao registrar usuário. Por favor, tente novamente.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    # Logout do Supabase
    supabase.auth.sign_out()
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    # Pega o ano da query string ou usa o ano atual como padrão
    selected_year = request.args.get('year', type=int, default=datetime.now().year)
    current_month = datetime.now().month
    
    # Busca dados do usuário
    user_id = session['user_id']
    
    quarter_data = get_quarter_data(user_id, selected_year)
    month_data = get_month_data(user_id, selected_year)
    
    return render_template('index.html', 
                         year=selected_year,
                         current_month=current_month,
                         quarter_data=quarter_data,
                         month_data=month_data)

@app.route('/mes/<int:mes>')
@login_required
def mes_detalhe(mes):
    # Pega o ano da query string ou usa o ano atual como padrão
    selected_year = request.args.get('year', type=int, default=datetime.now().year)
    
    # Get month name in Portuguese
    meses_nomes = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    nome_mes = meses_nomes[mes]
    
    # Busca dados do usuário
    user_id = session['user_id']
    
    # Calcula total de dias no mês
    total_dias = calendar.monthrange(selected_year, mes)[1]
    
    # Busca dias não contábeis
    dias_nao_contabeis = supabase.table('dias_nao_contabeis')\
        .select('*')\
        .eq('user_id', user_id)\
        .execute()
    
    # Filtra dias não contábeis do mês específico
    dias_nao_contabeis_mes = []
    for d in (dias_nao_contabeis.data or []):
        try:
            data = parse_date(d['data'])
            if data.month == mes and data.year == selected_year:
                d['data'] = format_date(data)
                dias_nao_contabeis_mes.append(d)
        except (ValueError, KeyError) as e:
            print(f"Erro ao processar dia não contábil: {str(e)}")
            continue
    
    # Calcula dias a trabalhar
    dias_nao_contabeis_count = len(dias_nao_contabeis_mes)
    dias_trabalhar = total_dias - dias_nao_contabeis_count
    
    # Busca turnos do mês
    turnos = supabase.table('turnos')\
        .select('*')\
        .eq('user_id', user_id)\
        .execute()
    
    # Filtra e processa turnos do mês
    turnos_mes = []
    for t in (turnos.data or []):
        try:
            data = parse_date(t['data'])
            if data.month == mes and data.year == selected_year:
                t['data'] = format_date(data)
                t['hora_inicial'] = format_time(parse_time(t['hora_inicial']))
                t['hora_final'] = format_time(parse_time(t['hora_final']))
                turnos_mes.append(t)
        except (ValueError, KeyError) as e:
            print(f"Erro ao processar turno: {str(e)}")
            continue
    
    # Calcula horas
    horas_previstas = dias_trabalhar * 8  # 8 horas por dia útil
    horas_trabalhadas = sum(
        (parse_time(t['hora_final']).hour * 60 + parse_time(t['hora_final']).minute -
         parse_time(t['hora_inicial']).hour * 60 - parse_time(t['hora_inicial']).minute) / 60
        for t in turnos_mes
    )
    saldo = horas_trabalhadas - horas_previstas
    
    mes_data = {
        'previsto': f"{int(horas_previstas)}:{int((horas_previstas % 1) * 60):02d}",
        'trabalhado': f"{int(horas_trabalhadas)}:{int((horas_trabalhadas % 1) * 60):02d}",
        'saldo': f"{'+' if saldo >= 0 else ''}{int(saldo)}:{int(abs(saldo % 1) * 60):02d}",
        'total_dias': total_dias,
        'dias_nao_contabeis': sorted(dias_nao_contabeis_mes, key=lambda x: parse_date(x['data'])),
        'turnos': sorted(turnos_mes, key=lambda x: parse_date(x['data']))
    }
    
    return render_template('mes.html',
                         mes=mes,
                         ano=selected_year,
                         nome_mes=nome_mes,
                         mes_data=mes_data,
                         total_dias=total_dias,
                         dias_nao_contabeis=dias_nao_contabeis_count,
                         dias_trabalhar=dias_trabalhar)

@app.route('/lancar_turno', methods=['POST'])
@login_required
def lancar_turno():
    if request.method == 'POST':
        data = request.form.get('data')
        hora_inicial = request.form.get('hora_inicial')
        hora_final = request.form.get('hora_final')
        descricao = request.form.get('descricao')
        
        if not data:
            flash('Data é obrigatória!', 'error')
            return redirect(url_for('index'))
            
        try:
            # Inserir turno no Supabase
            turno = supabase.table('turnos').insert({
                'user_id': session['user_id'],
                'data': data,
                'hora_inicial': hora_inicial,
                'hora_final': hora_final,
                'descricao': descricao
            }).execute()
            
            flash('Turno lançado com sucesso!', 'success')
            
            # Tenta extrair o mês da data
            try:
                mes = data.split('/')[1]
                return redirect(url_for('mes_detalhe', mes=mes))
            except (IndexError, ValueError):
                flash('Formato de data inválido!', 'error')
                return redirect(url_for('index'))
                
        except Exception as e:
            flash('Erro ao lançar turno!', 'error')
            return redirect(url_for('index'))
            
    return redirect(url_for('index'))

@app.route('/lancar_dia_nao_contabil', methods=['POST'])
@login_required
def lancar_dia_nao_contabil():
    if request.method == 'POST':
        datas_str = request.form.get('data')
        tipo = request.form.get('tipo')
        
        if not datas_str or not tipo:
            flash('Data e tipo são obrigatórios!', 'error')
            return redirect(url_for('index'))
        
        try:
            # Divide a string de datas em uma lista
            datas = [data.strip() for data in datas_str.split(',')]
            mes = None  # Para redirecionamento
            
            # Insere cada data individualmente
            for data in datas:
                try:
                    # Converte a data para o formato aceito pelo PostgreSQL (YYYY-MM-DD)
                    data_obj = datetime.strptime(data, '%d/%m/%Y')
                    data_postgres = data_obj.strftime('%Y-%m-%d')
                    
                    # Inserir dia não contábil no Supabase
                    supabase.table('dias_nao_contabeis').insert({
                        'user_id': session['user_id'],
                        'data': data_postgres,  # Usa o formato PostgreSQL
                        'tipo': tipo
                    }).execute()
                    
                    # Pega o mês da primeira data para redirecionamento
                    if not mes:
                        mes = data.split('/')[1]
                        
                except ValueError as ve:
                    flash(f'Data inválida: {data}', 'error')
                    continue
            
            flash('Dias não contábeis registrados com sucesso!', 'success')
            
            # Redireciona para o mês da primeira data
            if mes:
                return redirect(url_for('mes_detalhe', mes=mes))
                
        except Exception as e:
            flash('Erro ao registrar dias não contábeis!', 'error')
            print(f"Erro: {str(e)}")
            
    return redirect(url_for('index'))

@app.route('/excluir_turno/<int:turno_id>', methods=['POST'])
@login_required
def excluir_turno(turno_id):
    try:
        # Primeiro, busca o turno para pegar a data
        turno = supabase.table('turnos')\
            .select('*')\
            .eq('id', turno_id)\
            .eq('user_id', session['user_id'])\
            .execute()
            
        if not turno.data:
            flash('Turno não encontrado!', 'error')
            return redirect(url_for('index'))
            
        # Armazena o mês para redirecionamento
        data = turno.data[0]['data']
        mes = data.split('/')[1]
        
        # Exclui o turno
        supabase.table('turnos')\
            .delete()\
            .eq('id', turno_id)\
            .eq('user_id', session['user_id'])\
            .execute()
            
        flash('Turno excluído com sucesso!', 'success')
        return redirect(url_for('mes_detalhe', mes=mes))
        
    except Exception as e:
        flash('Erro ao excluir turno!', 'error')
        return redirect(url_for('index'))

@app.route('/excluir_dia_nao_contabil/<int:dia_id>', methods=['POST'])
@login_required
def excluir_dia_nao_contabil(dia_id):
    try:
        # Primeiro, busca o dia para pegar a data
        dia = supabase.table('dias_nao_contabeis')\
            .select('*')\
            .eq('id', dia_id)\
            .eq('user_id', session['user_id'])\
            .execute()
            
        if not dia.data:
            flash('Dia não contábil não encontrado!', 'error')
            return redirect(url_for('index'))
            
        # Armazena o mês para redirecionamento
        data = dia.data[0]['data']
        mes = data.split('/')[1]
        
        # Exclui o dia não contábil
        supabase.table('dias_nao_contabeis')\
            .delete()\
            .eq('id', dia_id)\
            .eq('user_id', session['user_id'])\
            .execute()
            
        flash('Dia não contábil excluído com sucesso!', 'success')
        return redirect(url_for('mes_detalhe', mes=mes))
        
    except Exception as e:
        flash('Erro ao excluir dia não contábil!', 'error')
        return redirect(url_for('index'))

# Forgot Password route
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        if email in supabase.auth.users():
            # TODO: Implement password reset logic
            # 1. Generate reset token
            # 2. Send reset email
            pass
        # Always show the same message for security
        flash('Se o email existir em nossa base de dados, você receberá as instruções para redefinir sua senha.', 'success')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/mes/<mes>/<ano>')
def mes(mes, ano):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    try:
        mes = int(mes)
        ano = int(ano)
        if not (1 <= mes <= 12):
            flash('Mês inválido', 'error')
            return redirect(url_for('index'))
            
        user_id = session['user_id']
        mes_data = get_month_detail(user_id, ano, mes)
        
        if not mes_data:
            flash('Erro ao carregar dados do mês', 'error')
            return redirect(url_for('index'))
            
        nome_mes = calendar.month_name[mes]
        
        return render_template('mes.html', 
                            mes=mes,
                            ano=ano,
                            nome_mes=nome_mes,
                            total_dias=mes_data['total_dias'],
                            dias_nao_contabeis=mes_data['dias_nao_contabeis_count'],
                            dias_trabalhados=len(mes_data['turnos']),
                            turnos=mes_data['turnos'],
                            dias_nao_contabeis_lista=mes_data['dias_nao_contabeis'],
                            horas_previstas=mes_data['previsto'],
                            horas_trabalhadas=mes_data['trabalhado'],
                            saldo_horas=mes_data['saldo'])
                            
    except ValueError as e:
        flash('Erro ao processar dados: ' + str(e), 'error')
        return redirect(url_for('index'))
    except Exception as e:
        flash('Erro inesperado: ' + str(e), 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)