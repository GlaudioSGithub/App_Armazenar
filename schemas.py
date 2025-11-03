# schemas.py
from pydantic import BaseModel
from datetime import date
from datetime import date, datetime


# Produto (já temos)
class ProdutoBase(BaseModel):
    sku: str
    descricao: str
    lote: str | None = None
    validade: date | None = None

class ProdutoCreate(ProdutoBase):
    pass

class Produto(ProdutoBase):
    id: int
    class Config:
        from_attributes = True

# Local
class LocalBase(BaseModel):
    codigo: str
    armazem: str
    corredor: str
    rack_nivel: str
    descricao: str | None = None

class LocalCreate(LocalBase):
    pass

class Local(LocalBase):
    id: int
    class Config:
        from_attributes = True

# Estoque
class EstoqueBase(BaseModel):
    produto_id: int
    local_id: int
    quantidade: int = 0

class EstoqueCreate(EstoqueBase):
    pass

class Estoque(EstoqueBase):
    id: int
    produto: Produto
    local: Local
    atualizado_em: datetime  # <- adicionar
    class Config:
        from_attributes = True

class LocalOut(BaseModel):
    id: int
    codigo: str
    armazem: str
    corredor: str
    rack_nivel: str
    descricao: str

    class Config:
        from_attributes = True

class EstoqueProdutoOut(BaseModel):
    local: LocalOut
    quantidade: int
    atualizado_em: datetime  # <- alterar de str para datetime
    class Config:
        from_attributes = True

class MovimentacaoBase(BaseModel):
    tipo: str  # 'entrada' ou 'saida'
    produto_id: int
    local_id: int
    quantidade: int

class MovimentacaoCreate(MovimentacaoBase):
    pass

class Movimentacao(MovimentacaoBase):
    id: int
    data_movimentacao: datetime
    class Config:
        from_attributes = True