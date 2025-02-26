# Sistema de Cadastro de Plantio

Este programa permite cadastrar informações sobre o plantio de vegetais e gera um QR Code contendo todas as informações registradas.

## Requisitos

- Python 3.x
- Bibliotecas necessárias (instale usando o requirements.txt)

## Como instalar

1. Clone ou baixe este repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Como usar

1. Execute o programa:
```bash
python plantio.py
```

2. Preencha as informações solicitadas sobre o plantio
3. O programa irá gerar um QR Code em formato PNG no mesmo diretório
4. Use qualquer leitor de QR Code para visualizar as informações cadastradas

## Informações coletadas

- Nome do vegetal
- Data do plantio
- Tipo de solo
- Frequência de rega
- Exposição ao sol necessária
- Tempo estimado até a colheita
- Observações adicionais
- Data e hora do cadastro

## Como hospedar no Render

1. Crie uma conta no [Render](https://render.com)

2. Conecte sua conta do GitHub ao Render

3. Crie um novo repositório no GitHub e faça push do seu código:
   ```bash
   git init
   git add .
   git commit -m "Primeira versão"
   git remote add origin <seu-repositorio>
   git push -u origin main
   ```

4. No Render:
   - Clique em "New +"
   - Selecione "Web Service"
   - Conecte seu repositório do GitHub
   - O Render detectará automaticamente que é uma aplicação Python
   - Use as seguintes configurações:
     - Name: plantio-info (ou outro nome de sua escolha)
     - Environment: Python
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn app:app`

5. Clique em "Create Web Service"

O Render irá automaticamente fazer deploy da sua aplicação e fornecerá uma URL pública.

## Importante

Após o deploy, atualize a URL no código do QR Code em `app.py` para usar a URL fornecida pelo Render ao invés do IP local.
