from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_pessoa = db.Column(db.String(10), nullable=False)  # 'fisica' ou 'juridica'
    nome = db.Column(db.String(100))
    cpf = db.Column(db.String(14), unique=True, index=True)
    razao_social = db.Column(db.String(100))
    cnpj = db.Column(db.String(18), unique=True, index=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.now)
    
    # Relacionamento com plantios
    plantios = db.relationship('Plantio', backref='usuario', lazy=True)
    
    def __repr__(self):
        if self.tipo_pessoa == 'fisica':
            return f'<Usuario {self.nome}>'
        else:
            return f'<Usuario {self.razao_social}>'
    
    def to_dict(self):
        if self.tipo_pessoa == 'fisica':
            return {
                'id': self.id,
                'tipo_pessoa': self.tipo_pessoa,
                'nome': self.nome,
                'cpf': self.cpf,
                'data_cadastro': self.data_cadastro.strftime('%d/%m/%Y %H:%M:%S')
            }
        else:
            return {
                'id': self.id,
                'tipo_pessoa': self.tipo_pessoa,
                'razao_social': self.razao_social,
                'cnpj': self.cnpj,
                'data_cadastro': self.data_cadastro.strftime('%d/%m/%Y %H:%M:%S')
            }

class Plantio(db.Model):
    __tablename__ = 'plantios'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_unico = db.Column(db.String(8), unique=True, index=True, nullable=False)
    nome_vegetal = db.Column(db.String(100), nullable=False)
    data_plantio = db.Column(db.Date, nullable=False)
    tipo_solo = db.Column(db.String(50))
    frequencia_rega = db.Column(db.String(50))
    exposicao_sol = db.Column(db.String(50))
    tempo_colheita = db.Column(db.Integer)
    observacoes = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=datetime.now)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    precisao = db.Column(db.Float)
    
    # Chave estrangeira para o usuário
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Relacionamento com status
    status_historico = db.relationship('StatusPlantio', backref='plantio', lazy=True, order_by='StatusPlantio.data_hora')
    
    def __repr__(self):
        return f'<Plantio {self.nome_vegetal} ({self.codigo_unico})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo_unico': self.codigo_unico,
            'nome_vegetal': self.nome_vegetal,
            'data_plantio': self.data_plantio.strftime('%Y-%m-%d'),
            'tipo_solo': self.tipo_solo,
            'frequencia_rega': self.frequencia_rega,
            'exposicao_sol': self.exposicao_sol,
            'tempo_colheita': self.tempo_colheita,
            'observacoes': self.observacoes,
            'data_cadastro': self.data_cadastro.strftime('%d/%m/%Y %H:%M:%S'),
            'latitude': self.latitude,
            'longitude': self.longitude,
            'precisao': self.precisao
        }
    
    def ultimo_status(self):
        if self.status_historico:
            return self.status_historico[-1]
        return None

class StatusPlantio(db.Model):
    __tablename__ = 'status_plantio'
    
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Integer, nullable=False)  # 1, 2, 3, 4
    status_texto = db.Column(db.String(50), nullable=False)
    observacao = db.Column(db.Text)
    usuario = db.Column(db.String(100))
    data_hora = db.Column(db.DateTime, default=datetime.now)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    precisao = db.Column(db.Float)
    
    # Chave estrangeira para o plantio
    plantio_id = db.Column(db.Integer, db.ForeignKey('plantios.id'), nullable=False)
    
    def __repr__(self):
        return f'<StatusPlantio {self.status_texto} ({self.data_hora})>'
    
    def to_dict(self):
        status_dict = {
            'id': self.id,
            'status': self.status,
            'status_texto': self.status_texto,
            'observacao': self.observacao,
            'usuario': self.usuario,
            'data_hora': self.data_hora.strftime('%d/%m/%Y %H:%M:%S')
        }
        
        if self.latitude and self.longitude:
            status_dict['localizacao'] = {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'precisao': self.precisao
            }
        
        return status_dict
