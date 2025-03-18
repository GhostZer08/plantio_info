from .db_connection import get_connection

def salvar_usuario(tipo_pessoa, dados):
    """Insere ou atualiza um usuário no banco."""
    conn = get_connection()
    cur = conn.cursor()
    
    if tipo_pessoa == "fisica":
        sql = """
        INSERT INTO usuarios (tipo_pessoa, cpf, nome, email, telefone, estado, municipio, distrito, comunidade_rio, nome_propriedade, numero_propriedade, numero_caf)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (cpf) DO UPDATE
        SET nome = EXCLUDED.nome, email = EXCLUDED.email, telefone = EXCLUDED.telefone;
        """
        valores = (
            "fisica", dados['cpf'], dados['nome'], dados['email'], dados['telefone'],
            dados['estado'], dados['municipio'], dados['distrito'], dados['comunidade_rio'],
            dados['nome_propriedade'], dados['numero_propriedade'], dados['numero_caf']
        )
    
    elif tipo_pessoa == "juridica":
        sql = """
        INSERT INTO usuarios (tipo_pessoa, cnpj, razao_social, nome_fantasia, email, telefone)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (cnpj) DO UPDATE
        SET razao_social = EXCLUDED.razao_social, nome_fantasia = EXCLUDED.nome_fantasia, email = EXCLUDED.email, telefone = EXCLUDED.telefone;
        """
        valores = (
            "juridica", dados['cnpj'], dados['razao_social'], dados['nome_fantasia'],
            dados['email'], dados['telefone']
        )

    cur.execute(sql, valores)
    conn.commit()
    
    cur.close()
    conn.close()
def buscar_usuario(documento, tipo_documento):
    """Busca um usuário pelo CPF ou CNPJ."""
    conn = get_connection()
    cur = conn.cursor()
    
    if tipo_documento == "CPF":
        sql = "SELECT * FROM usuarios WHERE cpf = %s"
    elif tipo_documento == "CNPJ":
        sql = "SELECT * FROM usuarios WHERE cnpj = %s"
    else:
        return None
    
    cur.execute(sql, (documento,))
    usuario = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return usuario

