import os
import json
from datetime import datetime
from models import db, Usuario, Plantio, StatusPlantio
from app import app, DATA_DIR, STATUS_DIR

def migrate_data():
    """Migra os dados dos arquivos JSON para o banco de dados SQLite."""
    with app.app_context():
        # Criar tabelas
        db.create_all()
        
        # Migrar usuários (criar um usuário padrão para os dados existentes)
        usuario = Usuario.query.filter_by(cpf='00000000000').first()
        if not usuario:
            usuario = Usuario(
                tipo_pessoa='fisica',
                nome='Usuário Migrado',
                cpf='00000000000',
                data_cadastro=datetime.now()
            )
            db.session.add(usuario)
            db.session.commit()
            print(f"Usuário padrão criado com ID: {usuario.id}")
        
        # Migrar plantios
        if os.path.exists(DATA_DIR):
            for arquivo in os.listdir(DATA_DIR):
                if arquivo.endswith('.json'):
                    with open(os.path.join(DATA_DIR, arquivo), 'r') as f:
                        try:
                            dados = json.load(f)
                            codigo_unico = dados.get('codigo_unico')
                            
                            # Verificar se o plantio já existe
                            plantio_existente = Plantio.query.filter_by(codigo_unico=codigo_unico).first()
                            if plantio_existente:
                                print(f"Plantio {codigo_unico} já existe, pulando...")
                                continue
                            
                            # Converter string de data para objeto date
                            data_plantio_str = dados.get('data_plantio')
                            try:
                                data_plantio = datetime.strptime(data_plantio_str, '%Y-%m-%d').date()
                            except:
                                data_plantio = datetime.now().date()
                            
                            # Criar novo plantio
                            plantio = Plantio(
                                codigo_unico=codigo_unico,
                                nome_vegetal=dados.get('nome_vegetal'),
                                data_plantio=data_plantio,
                                tipo_solo=dados.get('tipo_solo'),
                                frequencia_rega=dados.get('frequencia_rega'),
                                exposicao_sol=dados.get('exposicao_sol'),
                                tempo_colheita=dados.get('tempo_colheita'),
                                observacoes=dados.get('observacoes'),
                                latitude=float(dados.get('latitude', 0)),
                                longitude=float(dados.get('longitude', 0)),
                                precisao=float(dados.get('precisao', 0)),
                                usuario_id=usuario.id
                            )
                            db.session.add(plantio)
                            db.session.commit()
                            print(f"Plantio {codigo_unico} migrado com sucesso!")
                            
                            # Migrar histórico de status
                            arquivo_status = os.path.join(STATUS_DIR, f"status_{codigo_unico}.json")
                            if os.path.exists(arquivo_status):
                                with open(arquivo_status, 'r') as fs:
                                    try:
                                        historico = json.load(fs)
                                        for status_data in historico:
                                            data_hora_str = status_data.get('data_hora')
                                            try:
                                                data_hora = datetime.strptime(data_hora_str, '%Y-%m-%d %H:%M:%S')
                                            except:
                                                data_hora = datetime.now()
                                            
                                            status = StatusPlantio(
                                                plantio_id=plantio.id,
                                                status=status_data.get('status', 1),
                                                status_texto=status_data.get('status_texto', ''),
                                                observacao=status_data.get('observacao', ''),
                                                usuario=status_data.get('usuario', ''),
                                                data_hora=data_hora
                                            )
                                            
                                            # Adicionar localização se existir
                                            localizacao = status_data.get('localizacao')
                                            if localizacao:
                                                status.latitude = localizacao.get('latitude')
                                                status.longitude = localizacao.get('longitude')
                                                status.precisao = localizacao.get('precisao', 0)
                                            
                                            db.session.add(status)
                                        
                                        db.session.commit()
                                        print(f"Histórico de status para {codigo_unico} migrado com sucesso!")
                                    except Exception as e:
                                        print(f"Erro ao migrar histórico de status para {codigo_unico}: {str(e)}")
                                        db.session.rollback()
                        except Exception as e:
                            print(f"Erro ao migrar plantio {arquivo}: {str(e)}")
                            db.session.rollback()
        
        print("Migração concluída!")

if __name__ == "__main__":
    migrate_data()
