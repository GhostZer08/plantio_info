from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from flask_bootstrap import Bootstrap
import qrcode
from io import BytesIO
import base64
import json
from datetime import datetime
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
import uuid
import json

app = Flask(__name__)
app.secret_key = 'siplan_plantio_qrcode_secret_key'  # Chave secreta para a sessão
Bootstrap(app)

# Diretório para armazenar os dados dos plantios
DATA_DIR = 'dados_plantio'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Constantes para status de acompanhamento
STATUS_TYPES = {
    1: "Em Formação",
    2: "Em Transporte",
    3: "Em Plantio",
    4: "Plantado"
}

# Diretório para armazenar histórico de status
STATUS_DIR = 'status_historico'
if not os.path.exists(STATUS_DIR):
    os.makedirs(STATUS_DIR)

def validar_cpf(cpf):
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    if len(cpf) != 11:
        return False
        
    # Verifica se todos os dígitos são iguais
    if len(set(cpf)) == 1:
        return False
    
    # Calcula primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito = (soma * 10) % 11
    if digito == 10:
        digito = 0
    if digito != int(cpf[9]):
        return False
    
    # Calcula segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito = (soma * 10) % 11
    if digito == 10:
        digito = 0
    if digito != int(cpf[10]):
        return False
    
    return True

def validar_cnpj(cnpj):
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    if len(cnpj) != 14:
        return False
        
    # Verifica se todos os dígitos são iguais
    if len(set(cnpj)) == 1:
        return False
    
    # Primeiro dígito
    soma = sum(int(cnpj[i]) * (5 - i if i < 4 else 13 - i) for i in range(12))
    digito = 11 - (soma % 11)
    if digito >= 10:
        digito = 0
    if digito != int(cnpj[12]):
        return False
    
    # Segundo dígito
    soma = sum(int(cnpj[i]) * (6 - i if i < 5 else 14 - i) for i in range(13))
    digito = 11 - (soma % 11)
    if digito >= 10:
        digito = 0
    if digito != int(cnpj[13]):
        return False
    
    return True

def gerar_codigo_unico(documento):
    # Gera um código único baseado no timestamp e últimos 4 dígitos do documento
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    ultimos_digitos = re.sub(r'[^0-9]', '', documento)[-4:]
    return f"{timestamp}-{ultimos_digitos}"

def gerar_pdf_plantio(dados):
    # Cria um buffer para o PDF
    buffer = BytesIO()
    
    # Cria o documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        alignment=1,  # Centralizado
        spaceAfter=12,
        textColor=colors.darkgreen
    )
    subtitle_style = ParagraphStyle(
        name='SubtitleStyle',
        parent=styles['Heading2'],
        spaceAfter=6,
        textColor=colors.darkgreen
    )
    normal_style = styles['Normal']
    
    # Título
    elements.append(Paragraph("SIPLAN Plantio QR Code", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Informações do Plantio
    elements.append(Paragraph("Informações do Plantio", subtitle_style))
    
    # Dados do cadastro
    data_cadastro = [
        ["Código Único:", dados.get('codigo_unico', '')],
        ["Data do Cadastro:", dados.get('data_cadastro', '')]
    ]
    
    # Adicionar dados da pessoa física
    if dados.get('nome_pessoa'):
        data_cadastro.append(["Nome da Pessoa:", dados.get('nome_pessoa', '')])
    
    if dados.get('cpf_pessoa'):
        data_cadastro.append(["CPF:", dados.get('cpf_pessoa', '')])
    
    if dados.get('estado') or dados.get('municipio'):
        localidade = ""
        if dados.get('municipio'):
            localidade += dados.get('municipio', '')
        if dados.get('estado') and dados.get('municipio'):
            localidade += " - "
        if dados.get('estado'):
            localidade += dados.get('estado', '')
        data_cadastro.append(["Localidade:", localidade])
    
    if dados.get('distrito'):
        data_cadastro.append(["Distrito:", dados.get('distrito', '')])
    
    if dados.get('comunidade_rio'):
        data_cadastro.append(["Comunidade/Rio:", dados.get('comunidade_rio', '')])
    
    if dados.get('nome_propriedade'):
        data_cadastro.append(["Nome da Propriedade:", dados.get('nome_propriedade', '')])
    
    if dados.get('numero_propriedade'):
        data_cadastro.append(["Número da Propriedade:", dados.get('numero_propriedade', '')])
    
    if dados.get('numero_caf'):
        data_cadastro.append(["Número do CAF:", dados.get('numero_caf', '')])
    
    # Dados do plantio
    data_cadastro.extend([
        ["Nome do Vegetal:", dados.get('nome_vegetal', '')],
        ["Data do Plantio:", dados.get('data_plantio', '')],
        ["Tipo de Solo:", dados.get('tipo_solo', '')],
        ["Frequência de Rega:", dados.get('frequencia_rega', '')],
        ["Exposição ao Sol:", dados.get('exposicao_sol', '')],
        ["Tempo até Colheita:", dados.get('tempo_colheita', '')],
    ])
    
    if dados.get('observacoes'):
        data_cadastro.append(["Observações:", dados.get('observacoes', '')])
    
    # Adicionar localização se disponível
    if dados.get('latitude') and dados.get('longitude'):
        data_cadastro.append(["Localização:", f"Disponível (Ver no Google Maps)"])
    
    # Criar tabela com os dados
    table = Table(data_cadastro, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkgreen),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Adicionar QR Code
    elements.append(Paragraph("Escaneie o QR Code para acessar as informações do plantio:", normal_style))
    
    # Construir o documento
    doc.build(elements)
    
    # Retornar o buffer
    buffer.seek(0)
    return buffer

def gerar_pdf_base64(dados):
    # Gera o PDF usando a função gerar_pdf_plantio
    buffer = gerar_pdf_plantio(dados)
    
    # Converte para base64
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return base64.b64encode(pdf_bytes).decode()

@app.route('/')
def index():
    # Verificar se o usuário está logado
    if 'tipo_pessoa' not in session:
        return redirect(url_for('login'))
    
    return render_template('index.html')

@app.route('/validar-documento', methods=['POST'])
def validar_documento():
    documento = request.form.get('documento', '')
    tipo = request.form.get('tipo', '')
    
    # Remove caracteres não numéricos para validação
    documento_limpo = re.sub(r'[^0-9]', '', documento)
    
    if tipo == 'cpf':
        valido = validar_cpf(documento_limpo)
    else:  # cnpj
        valido = validar_cnpj(documento_limpo)
    
    return jsonify({'valido': valido})

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    # Verificar se o usuário está logado
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Obter dados do formulário
            nome_vegetal = request.form.get('nome_vegetal')
            data_plantio = request.form.get('data_plantio')
            tipo_solo = request.form.get('tipo_solo')
            
            # Obter dados da pessoa da sessão
            nome_pessoa = session.get('nome', '')
            cpf_pessoa = session.get('cpf', '')
            
            # Validar CPF
            if not cpf_pessoa:
                return "Usuário não autenticado. Faça login primeiro.", 400
            
            # Gerar código único
            codigo_unico = str(uuid.uuid4())
            
            # Obter data atual
            data_cadastro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Obter coordenadas de localização
            latitude = request.form.get('latitude', '')
            longitude = request.form.get('longitude', '')
            precisao = request.form.get('precisao', '')
            
            # Criar dicionário de dados
            dados = {
                'codigo_unico': codigo_unico,
                'nome_vegetal': nome_vegetal,
                'data_plantio': data_plantio,
                'tipo_solo': tipo_solo,
                'nome_pessoa': nome_pessoa,
                'cpf_pessoa': cpf_pessoa,
                'data_cadastro': data_cadastro,
                'latitude': latitude,
                'longitude': longitude,
                'precisao': precisao
            }
            
            # Salvar os dados em um arquivo JSON
            with open(os.path.join(DATA_DIR, f"{codigo_unico}.json"), 'w') as f:
                json.dump(dados, f, ensure_ascii=False)
            
            # Gera o QR Code
            try:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                
                # URL simplificada apenas com o código único
                url = f"https://plantio-info.onrender.com/plantio/{codigo_unico}"
                print("URL gerada:", url)
                
                qr.add_data(url)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Converte a imagem para base64
                buffered = BytesIO()
                img.save(buffered)
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                print("QR Code gerado com sucesso")
                
                return jsonify({
                    'success': True,
                    'qr_code': img_str,
                    'info': dados
                })
                
            except Exception as e:
                print("Erro ao gerar QR code:", str(e))
                return jsonify({
                    'success': False,
                    'error': 'Erro ao gerar QR code'
                })
                
        except Exception as e:
            print("Erro durante o cadastro:", str(e))
            return jsonify({
                'success': False,
                'error': str(e)
            })
            
    # Para GET, preparar o formulário
    documento = session.get('documento', '')
    tipo_documento = session.get('tipo_documento', '')
    
    # Obter os dados da pessoa física da sessão para pré-preencher o formulário
    nome_pessoa = session.get('nome', '')
    cpf_pessoa = session.get('cpf', '')
    estado = session.get('estado', '')
    municipio = session.get('municipio', '')
    distrito = session.get('distrito', '')
    comunidade_rio = session.get('comunidade_rio', '')
    nome_propriedade = session.get('nome_propriedade', '')
    numero_propriedade = session.get('numero_propriedade', '')
    numero_caf = session.get('numero_caf', '')
    
    return render_template('index.html', 
                          documento=documento, 
                          tipo_documento=tipo_documento,
                          nome_pessoa=nome_pessoa,
                          cpf_pessoa=cpf_pessoa,
                          estado=estado,
                          municipio=municipio,
                          distrito=distrito,
                          comunidade_rio=comunidade_rio,
                          nome_propriedade=nome_propriedade,
                          numero_propriedade=numero_propriedade,
                          numero_caf=numero_caf)

@app.route('/plantio/<codigo_unico>')
def visualizar_plantio(codigo_unico):
    try:
        # Carregar dados do plantio
        with open(os.path.join(DATA_DIR, f"{codigo_unico}.json"), 'r') as f:
            dados = json.load(f)
        
        # Carregar histórico de status
        arquivo_status = os.path.join(STATUS_DIR, f"status_{codigo_unico}.json")
        if os.path.exists(arquivo_status):
            with open(arquivo_status, 'r') as f:
                historico_status = json.load(f)
        else:
            historico_status = []
        
        # Formatar data de cadastro
        if 'data_cadastro' in dados:
            data_cadastro = dados['data_cadastro']
        else:
            data_cadastro = "Não disponível"
        
        # Verificar se há dados de localização
        tem_localizacao = 'latitude' in dados and 'longitude' in dados and dados['latitude'] and dados['longitude']
        
        # Preparar link do Google Maps
        google_maps_link = ""
        if tem_localizacao:
            google_maps_link = f"https://www.google.com/maps?q={dados['latitude']},{dados['longitude']}"
        
        # Gerar QR Code para a visualização
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # URL para o plantio
        url = f"{request.host_url}plantio/{codigo_unico}"
        
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converte a imagem para base64
        buffered = BytesIO()
        img.save(buffered)
        qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return render_template('plantio_publico.html', 
                              info=dados, 
                              data_cadastro=data_cadastro,
                              tem_localizacao=tem_localizacao,
                              google_maps_link=google_maps_link,
                              qr_code=qr_code_base64,
                              historico_status=historico_status)
    except FileNotFoundError:
        return "Plantio não encontrado", 404

@app.route('/visualizar/<codigo_unico>')
def visualizar_plantio_logado(codigo_unico):
    # Verificar se o usuário está logado
    if 'tipo_pessoa' not in session:
        return redirect(url_for('login'))
        
    try:
        # Tentar carregar os dados do arquivo
        arquivo_json = os.path.join(DATA_DIR, f"{codigo_unico}.json")
        
        # Se o arquivo existir, carrega os dados dele
        if os.path.exists(arquivo_json):
            with open(arquivo_json, 'r') as f:
                dados = json.load(f)
        else:
            # Caso o arquivo não exista, retorna erro
            return render_template('error.html', error=f"Plantio com código {codigo_unico} não encontrado"), 404
        
        # Carregar histórico de status
        arquivo_status = os.path.join(STATUS_DIR, f"status_{codigo_unico}.json")
        if os.path.exists(arquivo_status):
            with open(arquivo_status, 'r') as f:
                historico_status = json.load(f)
        else:
            historico_status = []
            
        # Verificar se há dados de localização
        tem_localizacao = 'latitude' in dados and 'longitude' in dados and dados['latitude'] and dados['longitude']
        
        # Preparar link do Google Maps
        google_maps_link = ""
        if tem_localizacao:
            google_maps_link = f"https://www.google.com/maps?q={dados['latitude']},{dados['longitude']}"
        
        # Formatar data de cadastro
        if 'data_cadastro' in dados:
            data_cadastro = dados['data_cadastro']
        else:
            data_cadastro = "Não disponível"
        
        return render_template('visualizar_plantio.html', 
                              dados=dados, 
                              data_cadastro=data_cadastro,
                              tem_localizacao=tem_localizacao,
                              google_maps_link=google_maps_link,
                              historico_status=historico_status)
    except Exception as e:
        print("Erro ao visualizar plantio:", str(e))
        return render_template('error.html', error=f"Erro ao visualizar plantio: {str(e)}"), 500

@app.route('/adicionar-status/<codigo_unico>', methods=['POST'])
def adicionar_status(codigo_unico):
    # Verificar se o usuário está logado
    if 'tipo_pessoa' not in session:
        return redirect(url_for('login'))
        
    try:
        # Obter os dados do formulário
        comentario = request.form.get('comentario')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        precisao = request.form.get('precisao')
        
        # Obter a data e hora atual
        data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Carregar os dados do arquivo
        arquivo_json = os.path.join(DATA_DIR, f"{codigo_unico}.json")
        
        if not os.path.exists(arquivo_json):
            return render_template('error.html', error=f"Plantio com código {codigo_unico} não encontrado"), 404
            
        with open(arquivo_json, 'r') as f:
            dados = json.load(f)
        
        # Criar o objeto de status
        status = {
            "comentario": comentario,
            "data_hora": data_hora,
        }
        
        # Adicionar localização se disponível
        if latitude and longitude:
            status["latitude"] = latitude
            status["longitude"] = longitude
            status["precisao"] = precisao
        
        # Adicionar o status ao histórico
        if "status_historico" not in dados:
            dados["status_historico"] = []
            
        dados["status_historico"].append(status)
        
        # Salvar os dados atualizados
        with open(arquivo_json, 'w') as f:
            json.dump(dados, f, indent=4)
        
        # Redirecionar para a página de visualização
        return redirect(url_for('visualizar_plantio_logado', codigo_unico=codigo_unico))
        
    except Exception as e:
        print("Erro ao adicionar status:", str(e))
        return render_template('error.html', error=f"Erro ao adicionar status: {str(e)}"), 500

@app.route('/atualizar-status', methods=['POST'])
def atualizar_status():
    try:
        # Verificar se o usuário está logado
        if 'tipo_pessoa' not in session:
            return jsonify({
                'success': False,
                'message': 'Usuário não está logado'
            })
            
        data = request.json
        codigo = data['codigo']
        
        # Nome do arquivo de histórico
        arquivo_status = os.path.join(STATUS_DIR, f"status_{codigo}.json")
        
        # Carregar histórico existente ou criar novo
        if os.path.exists(arquivo_status):
            with open(arquivo_status, 'r') as f:
                historico = json.load(f)
        else:
            historico = []
        
        # Usar o nome do usuário da sessão se disponível
        usuario = data.get('usuario', '')
        if not usuario and 'nome' in session:
            usuario = session['nome']
        
        # Criar novo registro de status
        novo_status = {
            'status': int(data['status']),
            'status_texto': STATUS_TYPES[int(data['status'])],
            'observacao': data['observacao'],
            'usuario': usuario,
            'data_hora': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Adicionar coordenadas se disponíveis
        if 'latitude' in data and 'longitude' in data:
            novo_status['localizacao'] = {
                'latitude': data['latitude'],
                'longitude': data['longitude']
            }
        
        # Adicionar ao histórico
        historico.append(novo_status)
        
        # Salvar histórico atualizado
        with open(arquivo_status, 'w') as f:
            json.dump(historico, f, indent=4, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'message': 'Status atualizado com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao atualizar status: {str(e)}'
        })

@app.route('/historico-status/<codigo>')
def historico_status(codigo):
    try:
        arquivo_status = os.path.join(STATUS_DIR, f"status_{codigo}.json")
        
        if os.path.exists(arquivo_status):
            with open(arquivo_status, 'r') as f:
                historico = json.load(f)
            return jsonify({
                'success': True,
                'historico': historico
            })
        else:
            return jsonify({
                'success': True,
                'historico': []
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao carregar histórico: {str(e)}'
        })

@app.route('/gerar-pdf', methods=['POST'])
def gerar_pdf():
    try:
        dados = request.json
        if not dados:
            return jsonify({'success': False, 'error': 'Dados não fornecidos'})
            
        pdf_base64 = gerar_pdf_base64(dados)
        return jsonify({'success': True, 'pdf': pdf_base64})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/login')
def login():
    # Se o usuário já estiver logado, redirecionar para o dashboard
    if 'tipo_pessoa' in session:
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/autenticar', methods=['POST'])
def autenticar():
    tipo_pessoa = request.form.get('tipo_pessoa')
    
    # Limpar a sessão existente
    session.clear()
    
    if tipo_pessoa == 'fisica':
        cpf = request.form.get('cpf')
        nome = request.form.get('nome')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        
        # Obter os novos campos
        estado = request.form.get('estado', '')
        municipio = request.form.get('municipio', '')
        distrito = request.form.get('distrito', '')
        comunidade_rio = request.form.get('comunidade_rio', '')
        nome_propriedade = request.form.get('nome_propriedade', '')
        numero_propriedade = request.form.get('numero_propriedade', '')
        numero_caf = request.form.get('numero_caf', '')
        
        # Validar CPF
        cpf_limpo = re.sub(r'[^0-9]', '', cpf)
        if not validar_cpf(cpf_limpo):
            return "CPF inválido", 400
        
        # Armazenar dados na sessão
        session['tipo_pessoa'] = 'fisica'
        session['cpf'] = cpf
        session['nome'] = nome
        session['email'] = email
        session['telefone'] = telefone
        session['logged_in'] = True
        session['documento'] = cpf
        session['tipo_documento'] = 'CPF'
        
        # Armazenar os novos campos na sessão
        session['estado'] = estado
        session['municipio'] = municipio
        session['distrito'] = distrito
        session['comunidade_rio'] = comunidade_rio
        session['nome_propriedade'] = nome_propriedade
        session['numero_propriedade'] = numero_propriedade
        session['numero_caf'] = numero_caf
        
    elif tipo_pessoa == 'juridica':
        cnpj = request.form.get('cnpj')
        razao_social = request.form.get('razao_social')
        nome_fantasia = request.form.get('nome_fantasia')
        email = request.form.get('email')
        telefone = request.form.get('telefone')
        
        # Validar CNPJ
        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
        if not validar_cnpj(cnpj_limpo):
            return "CNPJ inválido", 400
        
        # Armazenar dados na sessão
        session['tipo_pessoa'] = 'juridica'
        session['cnpj'] = cnpj
        session['razao_social'] = razao_social
        session['nome_fantasia'] = nome_fantasia
        session['email'] = email
        session['telefone'] = telefone
        session['logged_in'] = True
        session['documento'] = cnpj
        session['tipo_documento'] = 'CNPJ'
    
    else:
        return "Tipo de pessoa inválido", 400
    
    # Calcular estatísticas para o dashboard
    calcular_estatisticas()
    
    return redirect(url_for('dashboard'))

def calcular_estatisticas():
    """Calcula estatísticas para exibir no dashboard"""
    plantios = []
    especies = set()
    ultimo_plantio = None
    
    # Verificar se o diretório existe
    if os.path.exists(DATA_DIR):
        for arquivo in os.listdir(DATA_DIR):
            if arquivo.endswith('.json'):
                with open(os.path.join(DATA_DIR, arquivo), 'r') as f:
                    dados = json.load(f)
                    plantios.append(dados)
                    
                    if 'especie' in dados:
                        especies.add(dados['especie'])
                    
                    # Verificar se é o plantio mais recente
                    if 'data_plantio' in dados:
                        data_plantio = dados['data_plantio']
                        if ultimo_plantio is None or data_plantio > ultimo_plantio:
                            ultimo_plantio = data_plantio
    
    # Armazenar estatísticas na sessão
    session['total_plantios'] = len(plantios)
    session['total_especies'] = len(especies)
    session['ultimo_plantio'] = ultimo_plantio if ultimo_plantio else "Nenhum"

@app.route('/dashboard')
def dashboard():
    # Verificar se o usuário está logado
    if 'tipo_pessoa' not in session:
        return redirect(url_for('login'))
    
    return render_template('dashboard.html')

@app.route('/listar-plantios')
def listar_plantios():
    # Verificar se o usuário está logado
    if 'tipo_pessoa' not in session:
        return redirect(url_for('login'))
    
    # Carregar os dados dos plantios
    plantios = []
    if os.path.exists(DATA_DIR):
        for arquivo in os.listdir(DATA_DIR):
            if arquivo.endswith('.json'):
                with open(os.path.join(DATA_DIR, arquivo), 'r') as f:
                    dados = json.load(f)
                    plantios.append(dados)
    
    return render_template('listar_plantios.html', plantios=plantios)

@app.route('/escanear')
def escanear():
    # Verificar se o usuário está logado
    if 'tipo_pessoa' not in session:
        return redirect(url_for('login'))
    
    return render_template('escanear.html')

@app.route('/logout')
def logout():
    # Limpar todos os dados da sessão
    session.clear()
    return redirect(url_for('login'))

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return render_template('error.html', error=error), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error=error), 404

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
