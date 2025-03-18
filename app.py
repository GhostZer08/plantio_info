from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_bootstrap import Bootstrap
import os
import json
import qrcode
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
import uuid
import json
from db.queries import salvar_usuario, buscar_usuario

from reportlab.lib.utils import ImageReader
from datetime import datetime
import random
import string
from models import db, Usuario, Plantio, StatusPlantio
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'
Bootstrap(app)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plantio_info.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

# Configuração do login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Diretórios para armazenamento de dados (para compatibilidade com o sistema antigo)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'dados_plantio')
STATUS_DIR = os.path.join(BASE_DIR, 'status_historico')

# Criar diretórios se não existirem
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(STATUS_DIR):
    os.makedirs(STATUS_DIR)

# Função para gerar código único
def gerar_codigo_unico(tamanho=8):
    caracteres = string.ascii_lowercase + string.digits
    return ''.join(random.choice(caracteres) for _ in range(tamanho))

@app.route('/')
def index():
    if 'tipo_pessoa' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        tipo_pessoa = request.form.get('tipo_pessoa')
        
        if tipo_pessoa == 'fisica':
            cpf = request.form.get('cpf')
            nome = request.form.get('nome')
            
            # Buscar usuário no banco de dados
            usuario = Usuario.query.filter_by(cpf=cpf).first()
            
            # Se não existir, criar novo usuário
            if not usuario:
                usuario = Usuario(
                    tipo_pessoa='fisica',
                    nome=nome,
                    cpf=cpf
                )
                db.session.add(usuario)
                db.session.commit()
            
            # Login do usuário
            login_user(usuario)
            
            # Manter compatibilidade com o sistema antigo
            session['tipo_pessoa'] = 'fisica'
            session['cpf'] = cpf
            session['nome'] = nome
            
            return redirect(url_for('dashboard'))
        
        elif tipo_pessoa == 'juridica':
            cnpj = request.form.get('cnpj')
            razao_social = request.form.get('razao_social')
            
            # Buscar usuário no banco de dados
            usuario = Usuario.query.filter_by(cnpj=cnpj).first()
            
            # Se não existir, criar novo usuário
            if not usuario:
                usuario = Usuario(
                    tipo_pessoa='juridica',
                    razao_social=razao_social,
                    cnpj=cnpj
                )
                db.session.add(usuario)
                db.session.commit()
            
            # Login do usuário
            login_user(usuario)
            
            # Manter compatibilidade com o sistema antigo
            session['tipo_pessoa'] = 'juridica'
            session['cnpj'] = cnpj
            session['razao_social'] = razao_social
            
            return redirect(url_for('dashboard'))
    
    return render_template('index.html')

@app.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/cadastrar-plantio', methods=['GET', 'POST'])
@login_required
def cadastrar_plantio():
    if request.method == 'POST':
        # Gerar código único
        codigo_unico = gerar_codigo_unico()
        
        # Obter dados do formulário
        nome_vegetal = request.form.get('nome_vegetal')
        data_plantio = request.form.get('data_plantio')
        tipo_solo = request.form.get('tipo_solo')
        frequencia_rega = request.form.get('frequencia_rega')
        exposicao_sol = request.form.get('exposicao_sol')
        tempo_colheita = request.form.get('tempo_colheita')
        observacoes = request.form.get('observacoes')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        precisao = request.form.get('precisao')
        
        # Converter string de data para objeto date
        data_plantio_obj = datetime.strptime(data_plantio, '%Y-%m-%d').date()
        
        # Criar novo plantio no banco de dados
        plantio = Plantio(
            codigo_unico=codigo_unico,
            nome_vegetal=nome_vegetal,
            data_plantio=data_plantio_obj,
            tipo_solo=tipo_solo,
            frequencia_rega=frequencia_rega,
            exposicao_sol=exposicao_sol,
            tempo_colheita=tempo_colheita,
            observacoes=observacoes,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            precisao=float(precisao) if precisao else None,
            usuario_id=current_user.id
        )
        db.session.add(plantio)
        db.session.commit()
        
        # Manter compatibilidade com o sistema antigo
        dados = {
            'codigo_unico': codigo_unico,
            'tipo_documento': 'cpf' if current_user.tipo_pessoa == 'fisica' else 'cnpj',
            'documento': current_user.cpf if current_user.tipo_pessoa == 'fisica' else current_user.cnpj,
            'nome_vegetal': nome_vegetal,
            'data_plantio': data_plantio,
            'tipo_solo': tipo_solo,
            'frequencia_rega': frequencia_rega,
            'exposicao_sol': exposicao_sol,
            'tempo_colheita': tempo_colheita,
            'observacoes': observacoes,
            'data_cadastro': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'latitude': latitude,
            'longitude': longitude,
            'precisao': precisao
        }
        
        # Salvar dados no arquivo JSON (para compatibilidade)
        with open(os.path.join(DATA_DIR, f'{codigo_unico}.json'), 'w') as f:
            json.dump(dados, f)
        
        return redirect(url_for('visualizar_plantio', codigo=codigo_unico))
    
    return render_template('cadastrar_plantio.html')

@app.route('/visualizar-plantio/<codigo>')
@login_required
def visualizar_plantio(codigo):
    # Buscar plantio no banco de dados
    plantio = Plantio.query.filter_by(codigo_unico=codigo).first()
    
    if not plantio:
        return redirect(url_for('listar_plantios'))
    
    # Obter histórico de status
    historico_status = [status.to_dict() for status in plantio.status_historico]
    
    return render_template('visualizar_plantio.html', plantio=plantio.to_dict(), historico_status=historico_status)

@app.route('/atualizar-status/<codigo>', methods=['GET', 'POST'])
@login_required
def atualizar_status(codigo):
    # Buscar plantio no banco de dados
    plantio = Plantio.query.filter_by(codigo_unico=codigo).first()
    
    if not plantio:
        return redirect(url_for('listar_plantios'))
    
    if request.method == 'POST':
        status_id = int(request.form.get('status'))
        observacao = request.form.get('observacao')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        precisao = request.form.get('precisao')
        
        # Mapear ID do status para texto
        status_texto = {
            1: 'Em Formação',
            2: 'Em Transporte',
            3: 'Em Distribuição',
            4: 'Plantado'
        }.get(status_id, 'Desconhecido')
        
        # Criar novo status
        novo_status = StatusPlantio(
            plantio_id=plantio.id,
            status=status_id,
            status_texto=status_texto,
            observacao=observacao,
            usuario=current_user.nome if current_user.tipo_pessoa == 'fisica' else current_user.razao_social,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            precisao=float(precisao) if precisao else None
        )
        db.session.add(novo_status)
        db.session.commit()
        
        # Manter compatibilidade com o sistema antigo
        status_data = {
            'status': status_id,
            'status_texto': status_texto,
            'observacao': observacao,
            'usuario': current_user.nome if current_user.tipo_pessoa == 'fisica' else current_user.razao_social,
            'data_hora': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if latitude and longitude:
            status_data['localizacao'] = {
                'latitude': float(latitude),
                'longitude': float(longitude),
                'precisao': float(precisao) if precisao else 0
            }
        
        # Verificar se já existe arquivo de histórico
        arquivo_status = os.path.join(STATUS_DIR, f'status_{codigo}.json')
        if os.path.exists(arquivo_status):
            with open(arquivo_status, 'r') as f:
                historico = json.load(f)
        else:
            historico = []
        
        # Adicionar novo status ao histórico
        historico.append(status_data)
        
        # Salvar histórico atualizado
        with open(arquivo_status, 'w') as f:
            json.dump(historico, f)
        
        return redirect(url_for('visualizar_plantio', codigo=codigo))
    
    return render_template('login.html')

@app.route('/autenticar', methods=['POST'])
def autenticar():
    tipo_pessoa = request.form.get('tipo_pessoa')
    
    # Limpar a sessão existente
    session.clear()
    if tipo_pessoa == 'fisica':
        cpf = re.sub(r'[^0-9]', '', request.form.get('cpf'))  # Limpa CPF
        if not validar_cpf(cpf):
            return "CPF inválido", 400
        
        dados = {
            'cpf': cpf,
            'nome': request.form.get('nome'),
            'email': request.form.get('email'),
            'telefone': request.form.get('telefone'),
            'estado': request.form.get('estado', ''),
            'municipio': request.form.get('municipio', ''),
            'distrito': request.form.get('distrito', ''),
            'comunidade_rio': request.form.get('comunidade_rio', ''),
            'nome_propriedade': request.form.get('nome_propriedade', ''),
            'numero_propriedade': request.form.get('numero_propriedade', ''),
            'numero_caf': request.form.get('numero_caf', ''),
        }
        session['documento'] = cpf
        session['tipo_documento'] = 'CPF'

    elif tipo_pessoa == 'juridica':
        cnpj = re.sub(r'[^0-9]', '', request.form.get('cnpj'))  # Limpa CNPJ
        if not validar_cnpj(cnpj):
            return "CNPJ inválido", 400

        dados = {
            'cnpj': cnpj,
            'razao_social': request.form.get('razao_social'),
            'nome_fantasia': request.form.get('nome_fantasia'),
            'email': request.form.get('email'),
            'telefone': request.form.get('telefone'),
        }
        session['documento'] = cnpj
        session['tipo_documento'] = 'CNPJ'

    else:
        return "Tipo de pessoa inválido", 400

    # Buscar usuário no banco
    usuario = buscar_usuario(session['documento'], session['tipo_documento'])
    
    if not usuario:
        salvar_usuario(tipo_pessoa, dados)  # Se não existir, salvar no banco

    # Armazenar dados na sessão
    session.update(dados)
    session['tipo_pessoa'] = tipo_pessoa
    session['logged_in'] = True

    return redirect(url_for('dashboard'))
    
    # if tipo_pessoa == 'fisica':
    #     cpf = request.form.get('cpf')
    #     nome = request.form.get('nome')
    #     email = request.form.get('email')
    #     telefone = request.form.get('telefone')
        
    #     # Obter os novos campos
    #     estado = request.form.get('estado', '')
    #     municipio = request.form.get('municipio', '')
    #     distrito = request.form.get('distrito', '')
    #     comunidade_rio = request.form.get('comunidade_rio', '')
    #     nome_propriedade = request.form.get('nome_propriedade', '')
    #     numero_propriedade = request.form.get('numero_propriedade', '')
    #     numero_caf = request.form.get('numero_caf', '')
        
    #     # Validar CPF
    #     cpf_limpo = re.sub(r'[^0-9]', '', cpf)
    #     if not validar_cpf(cpf_limpo):
    #         return "CPF inválido", 400
        
    #     # Armazenar dados na sessão
    #     session['tipo_pessoa'] = 'fisica'
    #     session['cpf'] = cpf
    #     session['nome'] = nome
    #     session['email'] = email
    #     session['telefone'] = telefone
    #     session['logged_in'] = True
    #     session['documento'] = cpf
    #     session['tipo_documento'] = 'CPF'
        
    #     # Armazenar os novos campos na sessão
    #     session['estado'] = estado
    #     session['municipio'] = municipio
    #     session['distrito'] = distrito
    #     session['comunidade_rio'] = comunidade_rio
    #     session['nome_propriedade'] = nome_propriedade
    #     session['numero_propriedade'] = numero_propriedade
    #     session['numero_caf'] = numero_caf
        
    # elif tipo_pessoa == 'juridica':
    #     cnpj = request.form.get('cnpj')
    #     razao_social = request.form.get('razao_social')
    #     nome_fantasia = request.form.get('nome_fantasia')
    #     email = request.form.get('email')
    #     telefone = request.form.get('telefone')
        
    #     # Validar CNPJ
    #     cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
    #     if not validar_cnpj(cnpj_limpo):
    #         return "CNPJ inválido", 400
        
    #     # Armazenar dados na sessão
    #     session['tipo_pessoa'] = 'juridica'
    #     session['cnpj'] = cnpj
    #     session['razao_social'] = razao_social
    #     session['nome_fantasia'] = nome_fantasia
    #     session['email'] = email
    #     session['telefone'] = telefone
    #     session['logged_in'] = True
    #     session['documento'] = cnpj
    #     session['tipo_documento'] = 'CNPJ'
    
    # else:
    #     return "Tipo de pessoa inválido", 400
    
    # # Calcular estatísticas para o dashboard
    # calcular_estatisticas()
    
    # return redirect(url_for('dashboard'))

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
    return render_template('atualizar_status.html', plantio=plantio.to_dict())

@app.route('/listar-plantios')
@login_required
def listar_plantios():
    # Buscar plantios do usuário atual
    plantios_db = Plantio.query.filter_by(usuario_id=current_user.id).all()
    
    plantios = []
    for plantio in plantios_db:
        plantio_dict = plantio.to_dict()
        
        # Obter o status atual
        ultimo_status = plantio.ultimo_status()
        if ultimo_status:
            status_atual = f"{ultimo_status.status_texto}: {ultimo_status.observacao}" if ultimo_status.observacao else ultimo_status.status_texto
            plantio_dict['status_atual'] = status_atual
        
        plantios.append(plantio_dict)
    
    return render_template('listar_plantios.html', plantios=plantios)

@app.route('/gerar-qrcode/<codigo>')
@login_required
def gerar_qrcode(codigo):
    # Gerar URL para o QR Code
    url = request.host_url + 'plantio/' + codigo
    
    # Gerar QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Salvar QR Code em um buffer
    buffer = BytesIO()
    img.save(buffer)
    buffer.seek(0)
    
    return send_file(buffer, mimetype='image/png')

@app.route('/gerar-etiqueta/<codigo>')
@login_required
def gerar_etiqueta(codigo):
    # Buscar plantio no banco de dados
    plantio = Plantio.query.filter_by(codigo_unico=codigo).first()
    
    if not plantio:
        return redirect(url_for('listar_plantios'))
    
    # Gerar URL para o QR Code
    url = request.host_url + 'plantio/' + codigo
    
    # Gerar QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Salvar QR Code em um buffer
    buffer = BytesIO()
    img.save(buffer)
    buffer.seek(0)
    
    # Criar PDF
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    
    # Adicionar título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Etiqueta de Plantio")
    
    # Adicionar informações do plantio
    c.setFont("Helvetica", 12)
    c.drawString(100, 720, f"Código: {plantio.codigo_unico}")
    c.drawString(100, 700, f"Vegetal: {plantio.nome_vegetal}")
    c.drawString(100, 680, f"Data de Plantio: {plantio.data_plantio.strftime('%d/%m/%Y')}")
    c.drawString(100, 660, f"Frequência de Rega: {plantio.frequencia_rega}")
    c.drawString(100, 640, f"Exposição ao Sol: {plantio.exposicao_sol}")
    
    # Adicionar QR Code
    qr_img = ImageReader(buffer)
    c.drawImage(qr_img, 100, 450, width=200, height=200)
    
    c.showPage()
    c.save()
    
    pdf_buffer.seek(0)
    
    return send_file(pdf_buffer, mimetype='application/pdf', download_name=f'etiqueta_{codigo}.pdf')

@app.route('/plantio/<codigo>')
def plantio_publico(codigo):
    # Buscar plantio no banco de dados
    plantio = Plantio.query.filter_by(codigo_unico=codigo).first()
    
    if not plantio:
        return render_template('plantio_nao_encontrado.html')
    
    # Obter histórico de status
    historico_status = [status.to_dict() for status in plantio.status_historico]
    
    return render_template('plantio_publico.html', plantio=plantio.to_dict(), historico_status=historico_status)

# Inicializar o banco de dados
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
