# SIPLAN - Sistema de Informações de Plantio

Sistema para gerenciamento de informações de plantio com QR Code.

## Funcionalidades

- Cadastro de plantios com informações detalhadas
- Geração de QR Codes para identificação de plantios
- Visualização de informações de plantio via QR Code
- Sistema de autenticação de usuários
- Acompanhamento de status de plantios com histórico

## Tecnologias Utilizadas

- Python
- Flask
- QR Code
- Bootstrap
- JavaScript
- JSON para armazenamento de dados
- SQLite (Banco de dados)
- Flask-SQLAlchemy (ORM)
- Flask-Migrate (Migrações de banco de dados)
- Flask-Login (Autenticação de usuários)

## Estrutura do Banco de Dados

### Tabela Usuarios
- id (PK)
- tipo_pessoa (física ou jurídica)
- nome (para pessoa física)
- cpf (para pessoa física)
- razao_social (para pessoa jurídica)
- cnpj (para pessoa jurídica)
- data_cadastro

### Tabela Plantios
- id (PK)
- codigo_unico (código para QR Code)
- nome_vegetal
- data_plantio
- tipo_solo
- frequencia_rega
- exposicao_sol
- tempo_colheita
- observacoes
- data_cadastro
- latitude
- longitude
- precisao
- usuario_id (FK para Usuarios)

### Tabela StatusPlantio
- id (PK)
- status (1, 2, 3, 4)
- status_texto (Em Formação, Em Transporte, Em Distribuição, Plantado)
- observacao
- usuario
- data_hora
- latitude
- longitude
- precisao
- plantio_id (FK para Plantios)

## Implantação no Render

### Opção 1: Implantação Automática via GitHub Actions

1. Crie uma conta no [Render](https://render.com/) se ainda não tiver uma
2. Crie um novo serviço Web no Render
3. Conecte seu repositório GitHub
4. Obtenha o ID do serviço do Render (está na URL quando você está visualizando o serviço, algo como `srv-abcdefgh`)
5. Obtenha uma chave de API do Render:
   - Faça login no Render
   - Vá para "Account Settings" > "API Keys"
   - Crie uma nova chave de API
6. Configure os segredos no GitHub:
   - Vá para seu repositório no GitHub
   - Clique em "Settings" > "Secrets and variables" > "Actions"
   - Adicione dois novos segredos:
     - Nome: `RENDER_API_KEY`, Valor: sua chave de API do Render
     - Nome: `RENDER_SERVICE_ID`, Valor: o ID do serviço do Render
7. Faça push para a branch `main` ou `master` para acionar a implantação automática

### Opção 2: Implantação Direta no Render (mais simples)

1. Faça login no [Render](https://render.com/)
2. Clique em "New" > "Web Service"
3. Conecte seu repositório GitHub
4. Configure o serviço:
   - Nome: plantio-info
   - Ambiente: Python
   - Comando de construção: `pip install -r requirements.txt`
   - Comando de início: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --log-level debug`
   - Selecione o plano gratuito ou pago conforme sua necessidade
5. Clique em "Create Web Service"

O Render irá automaticamente detectar mudanças no seu repositório GitHub e implantar o aplicativo.

## Desenvolvimento Local

1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Execute o aplicativo: `python app.py`
4. Acesse o aplicativo em `http://localhost:5000`

## Migração de Dados

Para migrar dados dos arquivos JSON para o banco de dados SQLite:

```
python migrate_data.py
```

## Acesso

- URL: http://localhost:5000
- Login: Utilize CPF (pessoa física) ou CNPJ (pessoa jurídica)
