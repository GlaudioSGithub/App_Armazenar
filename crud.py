# crud.py
from sqlalchemy.orm import relationship, Session
import models, schemas
from fastapi import HTTPException
from datetime import datetime, date, timedelta
from sqlalchemy import and_, func
from models import Movimentacao, Produto, Local


# Produtos
def get_produtos(db: Session):
    return db.query(models.Produto).all()

def create_produto(db: Session, produto: schemas.ProdutoCreate):
    db_produto = models.Produto(**produto.model_dump())
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    return db_produto

# Locais
def get_locais(db: Session):
    return db.query(models.Local).all()

def create_local(db: Session, local: schemas.LocalCreate):
    db_local = models.Local(**local.model_dump())
    db.add(db_local)
    db.commit()
    db.refresh(db_local)
    return db_local

# Estoque
def get_estoque(db: Session):
    return db.query(models.Estoque).all()

def create_estoque(db: Session, estoque: schemas.EstoqueCreate):
    db_estoque = models.Estoque(**estoque.model_dump())
    db.add(db_estoque)
    db.commit()
    db.refresh(db_estoque)
    return db_estoque

def popular_estoque(db: Session, produtos_ids: list[int], locais_ids: list[int], quantidade_default: int = 10):
    for produto_id in produtos_ids:
        for local_id in locais_ids:
            exists = db.query(models.Estoque).filter_by(
                produto_id=produto_id, local_id=local_id
            ).first()
            if not exists:
                db_estoque = models.Estoque(
                    produto_id=produto_id,
                    local_id=local_id,
                    quantidade=quantidade_default
                )
                db.add(db_estoque)
    db.commit()

def create_estoque(db: Session, estoque: schemas.EstoqueCreate):
    if estoque.quantidade < 0:
        raise ValueError("Quantidade não pode ser negativa")
    db_estoque = models.Estoque(**estoque.model_dump())
    db.add(db_estoque)
    db.commit()
    db.refresh(db_estoque)
    return db_estoque

# Movimentações
def create_movimentacao(db: Session, movimentacao: schemas.MovimentacaoCreate):
    # 1. Verifica se produto e local existem
    produto = db.query(models.Produto).filter(models.Produto.id == movimentacao.produto_id).first()
    local = db.query(models.Local).filter(models.Local.id == movimentacao.local_id).first()
    if not produto or not local:
        raise HTTPException(status_code=404, detail="Produto ou local não encontrado")

    # 2. Busca o registro de estoque correspondente
    estoque = db.query(models.Estoque).filter(
        models.Estoque.produto_id == movimentacao.produto_id,
        models.Estoque.local_id == movimentacao.local_id
    ).first()

    # Se não existe, cria um novo (somente se for entrada)
    if not estoque:
        if movimentacao.tipo == "entrada":
            estoque = models.Estoque(
                produto_id=movimentacao.produto_id,
                local_id=movimentacao.local_id,
                quantidade=0
            )
            db.add(estoque)
        else:
            raise HTTPException(status_code=400, detail="Estoque não encontrado para saída")

    # 3. Atualiza a quantidade
    if movimentacao.tipo == "entrada":
        estoque.quantidade += movimentacao.quantidade
    elif movimentacao.tipo == "saida":
        if estoque.quantidade < movimentacao.quantidade:
            raise HTTPException(status_code=400, detail="Quantidade insuficiente em estoque")
        estoque.quantidade -= movimentacao.quantidade
    else:
        raise HTTPException(status_code=400, detail="Tipo de movimentação inválido (use 'entrada' ou 'saida')")

    # 4. Cria o registro de movimentação
    db_mov = models.Movimentacao(**movimentacao.model_dump())
    db.add(db_mov)
    db.commit()
    db.refresh(db_mov)
    db.refresh(estoque)

    return db_mov

def get_movimentacoes(db: Session):
    return db.query(models.Movimentacao).order_by(models.Movimentacao.data_movimentacao.desc()).all()

def get_movimentacoes_filtradas(
    db: Session,
    tipo: str | None = None,
    produto_id: int | None = None,
    local_id: int | None = None,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None
):
    query = db.query(models.Movimentacao)

    if tipo:
        query = query.filter(models.Movimentacao.tipo == tipo)
    if produto_id:
        query = query.filter(models.Movimentacao.produto_id == produto_id)
    if local_id:
        query = query.filter(models.Movimentacao.local_id == local_id)
    if data_inicio:
        query = query.filter(models.Movimentacao.data_movimentacao >= data_inicio)
    if data_fim:
        query = query.filter(models.Movimentacao.data_movimentacao <= data_fim)

    return query.order_by(models.Movimentacao.data_movimentacao.desc()).all()

# --- Relatório de estoque geral ---
def relatorio_estoque_geral(db: Session):
    resultados = (
        db.query(
            models.Produto.descricao.label("produto"),
            models.Local.codigo.label("local"),
            models.Estoque.quantidade.label("quantidade")
        )
        .join(models.Produto, models.Estoque.produto_id == models.Produto.id)
        .join(models.Local, models.Estoque.local_id == models.Local.id)
        .order_by(models.Produto.descricao, models.Local.codigo)
        .all()
    )

    # Converter cada linha (Row) em dicionário
    return [
        {
            "produto": r.produto,
            "local": r.local,
            "quantidade": r.quantidade
        }
        for r in resultados
    ]


def relatorio_resumo_movimentacoes(db: Session):
    resultados = (
        db.query(
            models.Produto.descricao.label("produto"),
            models.Movimentacao.tipo.label("tipo"),
            func.sum(models.Movimentacao.quantidade).label("total")
        )
        .join(models.Produto, models.Movimentacao.produto_id == models.Produto.id)
        .group_by(models.Produto.descricao, models.Movimentacao.tipo)
        .order_by(models.Produto.descricao)
        .all()
    )

    return [
        {"produto": r.produto, "tipo": r.tipo, "total": r.total}
        for r in resultados
    ]


# Estoque por produto
def relatorio_estoque_por_produto(db: Session, produto_id: int):
    resultados = (
        db.query(
            models.Produto.descricao.label("produto"),
            models.Local.codigo.label("local"),
            models.Estoque.quantidade.label("quantidade")
        )
        .join(models.Produto, models.Estoque.produto_id == models.Produto.id)
        .join(models.Local, models.Estoque.local_id == models.Local.id)
        .filter(models.Produto.id == produto_id)
        .all()
    )

    return [
        {"produto": r.produto, "local": r.local, "quantidade": r.quantidade}
        for r in resultados
    ]

# Movimentações por data
def relatorio_movimentacoes_por_periodo(db: Session, data_inicio, data_fim):
    # Converte para datetime se vier como string
    if isinstance(data_inicio, str):
        data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
    else:
        data_inicio = datetime.combine(data_inicio, datetime.min.time())

    if isinstance(data_fim, str):
        data_fim = datetime.strptime(data_fim, "%Y-%m-%d")
    else:
        data_fim = datetime.combine(data_fim, datetime.min.time())

    # Inclui todo o último dia
    data_fim = data_fim + timedelta(days=1) - timedelta(microseconds=1)

    # Debug
    print("Data início:", data_inicio, type(data_inicio))
    print("Data fim:", data_fim, type(data_fim))

    query = (
        db.query(
            Movimentacao.id,
            Movimentacao.tipo,
            Produto.descricao.label("produto"),
            Movimentacao.quantidade,
            Local.codigo.label("local"),
            Movimentacao.data_movimentacao.label("data")
        )
        .join(Produto, Movimentacao.produto_id == Produto.id)
        .join(Local, Movimentacao.local_id == Local.id)
        .filter(Movimentacao.data_movimentacao.between(data_inicio, data_fim))
        .order_by(Movimentacao.data_movimentacao)
    )

    resultados = query.all()

    # Converter para lista de dicionários
    return [
        {
            "id": r.id,
            "tipo": r.tipo,
            "produto": r.produto,
            "quantidade": r.quantidade,
            "local": r.local,
            "data": r.data.strftime("%Y-%m-%d %H:%M:%S")
        }
        for r in resultados
    ]

# --- Relatório de estoque geral ---
def relatorio_estoque_geral(db: Session):
    resultados = (
        db.query(
            models.Produto.descricao.label("produto"),
            models.Local.codigo.label("local"),
            models.Estoque.quantidade.label("quantidade")
        )
        .join(models.Produto, models.Estoque.produto_id == models.Produto.id)
        .join(models.Local, models.Estoque.local_id == models.Local.id)
        .order_by(models.Produto.descricao, models.Local.codigo)
        .all()
    )

    return [
        {
            "produto": r.produto,
            "local": r.local,
            "quantidade": r.quantidade
        }
        for r in resultados
    ]

# --- Relatório de estoque por produto ---
def relatorio_estoque_por_produto(db: Session, produto_id: int):
    resultados = (
        db.query(
            models.Produto.descricao.label("produto"),
            models.Local.codigo.label("local"),
            models.Estoque.quantidade.label("quantidade")
        )
        .join(models.Produto, models.Estoque.produto_id == models.Produto.id)
        .join(models.Local, models.Estoque.local_id == models.Local.id)
        .filter(models.Produto.id == produto_id)
        .order_by(models.Local.codigo)
        .all()
    )

    return [
        {
            "produto": r.produto,
            "local": r.local,
            "quantidade": r.quantidade
        }
        for r in resultados
    ]

def relatorio_inventario_por_local(db: Session):
    resultados = (
        db.query(
            models.Local.codigo.label("local"),
            models.Produto.descricao.label("produto"),
            models.Estoque.quantidade.label("quantidade")
        )
        .join(models.Produto, models.Estoque.produto_id == models.Produto.id)
        .join(models.Local, models.Estoque.local_id == models.Local.id)
        .order_by(models.Local.codigo, models.Produto.descricao)
        .all()
    )

    return [
        {"local": r.local, "produto": r.produto, "quantidade": r.quantidade}
        for r in resultados
    ]

# --- Relatórios de movimentações específicas
def relatorio_operacoes(db: Session):
    resultados = (
        db.query(
            models.Movimentacao.tipo.label("operacao"),
            models.Produto.descricao.label("produto"),
            models.Local.codigo.label("local"),
            models.Movimentacao.quantidade.label("quantidade"),
            models.Movimentacao.data_movimentacao.label("data")
        )
        .order_by(models.Movimentacao.data_movimentacao)
        .all()
    )

    return [
        {
            "operacao": r.operacao,
            "produto": r.produto,
            "local": r.local,
            "quantidade": r.quantidade,
            "data": r.data.strftime("%Y-%m-%d %H:%M:%S")
        }
        for r in resultados
    ]
