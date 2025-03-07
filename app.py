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
app.secret_key = 'siblam_plantio_qrcode_secret_key'  # Chave secreta para a sessão
Bootstrap(app)

# Diretório para armazenar os dados dos plantios
DATA_DIR = 'dados_plantio'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

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
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Centralizado
    )
    
    # Título
    elements.append(Paragraph("Informações do Plantio", title_style))
    elements.append(Spacer(1, 12))
    
    # Adiciona o código único em destaque
    codigo_style = ParagraphStyle(
        'CodigoStyle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#28a745'),
        spaceAfter=20,
        alignment=1
    )
    elements.append(Paragraph(f"Código: {dados['codigo_unico']}", codigo_style))
    elements.append(Spacer(1, 12))
    
    # Prepara os dados para a tabela
    table_data = []
    labels = {
        'tipo_documento': 'Tipo de Documento',
        'documento': 'Documento',
        'nome_vegetal': 'Nome do Vegetal',
        'data_plantio': 'Data do Plantio',
        'tipo_solo': 'Tipo de Solo',
        'frequencia_rega': 'Frequência de Rega',
        'exposicao_sol': 'Exposição ao Sol',
        'tempo_colheita': 'Tempo até Colheita',
        'observacoes': 'Observações',
        'data_cadastro': 'Data do Cadastro',
        'latitude': 'Latitude',
        'longitude': 'Longitude',
        'precisao': 'Precisão'
    }
    
    for key, label in labels.items():
        if key in dados:
            table_data.append([Paragraph(label, styles['Normal']), 
                             Paragraph(str(dados[key]), styles['Normal'])])
    
    # Cria a tabela
    table = Table(table_data, colWidths=[2.5*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
    ]))
    
    elements.append(table)
    
    # Gera o PDF
    doc.build(elements)
    
    # Retorna o PDF em base64
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

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    try:
        # Verificar se o usuário está logado
        if 'tipo_pessoa' not in session:
            return jsonify({
                'success': False,
                'error': 'Usuário não está logado'
            }), 401
        
        # Obter documento da sessão
        documento = None
        tipo_documento = None
        
        if session.get('tipo_pessoa') == 'fisica':
            documento = session.get('cpf')
            tipo_documento = 'CPF'
        elif session.get('tipo_pessoa') == 'juridica':
            documento = session.get('cnpj')
            tipo_documento = 'CNPJ'
        
        # Verificar se o documento está disponível
        if not documento:
            return jsonify({
                'success': False,
                'error': 'Documento não encontrado na sessão'
            }), 400
            
        # Obter os dados do formulário
        nome_vegetal = request.form.get('nome_vegetal')
        data_plantio = request.form.get('data_plantio')
        tipo_solo = request.form.get('tipo_solo')
        frequencia_rega = request.form.get('frequencia_rega')
        exposicao_sol = request.form.get('exposicao_sol')
        tempo_colheita = request.form.get('tempo_colheita')
        observacoes = request.form.get('observacoes', '')
        
        # Obter dados de localização
        latitude = request.form.get('latitude', '')
        longitude = request.form.get('longitude', '')
        precisao = request.form.get('precisao', '')
        
        # Log para debug
        print(f"Usando documento da sessão: {documento}, Tipo: {tipo_documento}")
        
        # Gerar um código único para o plantio
        codigo_unico = str(uuid.uuid4())[:8]
        
        # Criar um dicionário com os dados
        dados = {
            'codigo_unico': codigo_unico,
            'tipo_documento': tipo_documento,
            'documento': documento,
            'nome_vegetal': nome_vegetal,
            'data_plantio': data_plantio,
            'tipo_solo': tipo_solo,
            'frequencia_rega': frequencia_rega,
            'exposicao_sol': exposicao_sol,
            'tempo_colheita': tempo_colheita,
            'observacoes': observacoes,
            'data_cadastro': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        
        # Adicionar dados de localização se disponíveis
        if latitude and longitude:
            dados['latitude'] = latitude
            dados['longitude'] = longitude
            dados['precisao'] = precisao
        
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

@app.route('/plantio/<codigo_unico>')
def plantio_redirect(codigo_unico):
    # Redirecionar para a rota de visualização
    return redirect(url_for('visualizar_plantio', codigo_unico=codigo_unico))

@app.route('/visualizar/<codigo_unico>')
def visualizar_plantio(codigo_unico):
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
        
        # Formatação do documento para exibição
        if dados['tipo_documento'] == 'CPF':
            cpf = dados['documento']
            if len(cpf) == 11:
                dados['documento'] = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        elif dados['tipo_documento'] == 'CNPJ':
            cnpj = dados['documento']
            if len(cnpj) == 14:
                dados['documento'] = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        
        return render_template('visualizar_plantio.html', info=dados)
    except Exception as e:
        print("Erro ao visualizar plantio:", str(e))
        return render_template('error.html', error=f"Erro ao visualizar plantio: {str(e)}"), 500

@app.route('/gerar-pdf', methods=['POST'])
def gerar_pdf():
    try:
        dados = request.json
        if not dados:
            return jsonify({'success': False, 'error': 'Dados não fornecidos'})
            
        pdf_base64 = gerar_pdf_plantio(dados)
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
