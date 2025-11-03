from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, date
from database import Base


class Produto(Base):
    __tablename__ = "produtos"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False)
    descricao = Column(String(255), nullable=False)
    lote = Column(String(50))
    validade = Column(Date)

class Local(Base):
    __tablename__ = "locais"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False)
    armazem = Column(String(50))
    corredor = Column(String(50))
    rack_nivel = Column(String(50))
    descricao = Column(String(255))

class Estoque(Base):
    __tablename__ = "estoque"
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id", ondelete="CASCADE"))
    local_id = Column(Integer, ForeignKey("locais.id", ondelete="CASCADE"))
    quantidade = Column(Integer, default=0)
    atualizado_em = Column(DateTime, default=datetime.utcnow)
    
    produto = relationship("Produto")
    local = relationship("Local")

class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, nullable=False)  # "entrada" ou "saida"
    quantidade = Column(Integer, nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    local_id = Column(Integer, ForeignKey("locais.id"))
    data_movimentacao = Column(Date, nullable=False)

    produto = relationship("Produto")
    local = relationship("Local")