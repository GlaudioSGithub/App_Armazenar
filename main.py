from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
import models, schemas, crud
from database import engine, Base, get_db
from fastapi import Query, HTTPException
from datetime import datetime, date
from crud import relatorio_resumo_movimentacoes
from database import get_db
from qrcode_utils import gerar_qr_code_local, gerar_qr_code_produto, gerar_etiqueta_qr_rack

Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])

app = FastAPI(title="WMS API")

# Raiz
@app.get("/")
def root():
    return {"mensagem": "🚀 API WMS rodando com sucesso!"}

# Produtos
@app.get("/produtos", response_model=list[schemas.Produto])
def listar_produtos(db: Session = Depends(get_db)):
    return crud.get_produtos(db)

@app.post("/produtos", response_model=schemas.Produto)
def criar_produto(produto: schemas.ProdutoCreate, db: Session = Depends(get_db)):
    db_produto = db.query(models.Produto).filter(models.Produto.sku == produto.sku).first()
    if db_produto:
        raise HTTPException(status_code=400, detail="Produto com esse SKU já existe")
    return crud.create_produto(db, produto)

# Locais
@app.get("/locais", response_model=list[schemas.Local])
def listar_locais(db: Session = Depends(get_db)):
    return crud.get_locais(db)

@app.post("/locais", response_model=schemas.Local)
def criar_local(local: schemas.LocalCreate, db: Session = Depends(get_db)):
    db_local = db.query(models.Local).filter(models.Local.codigo == local.codigo).first()
    if db_local:
        raise HTTPException(status_code=400, detail="Local já existe")
    return crud.create_local(db, local)

# Estoque
@app.get("/estoque", response_model=list[schemas.Estoque])
def listar_estoque(db: Session = Depends(get_db)):
    return crud.get_estoque(db)

@app.post("/estoque", response_model=schemas.Estoque)
def criar_estoque(estoque: schemas.EstoqueCreate, db: Session = Depends(get_db)):
    return crud.create_estoque(db, estoque)

@app.get("/produtos_por_local/{local_id}", response_model=list[schemas.Estoque])
def produtos_por_local(local_id: int, db: Session = Depends(get_db)):
    estoque_local = db.query(models.Estoque).filter(models.Estoque.local_id == local_id).all()
    if not estoque_local:
        raise HTTPException(status_code=404, detail="Nenhum produto encontrado nesse local")
    return estoque_local


@app.post("/popular_estoque")
def popular_estoque_teste(db: Session = Depends(get_db)):
    produtos = db.query(models.Produto).all()
    locais = db.query(models.Local).all()
    if not produtos or not locais:
        raise HTTPException(status_code=400, detail="Crie produtos e locais antes de popular estoque")
    
    produtos_ids = [p.id for p in produtos]
    locais_ids = [l.id for l in locais]

    crud.popular_estoque(db, produtos_ids, locais_ids, quantidade_default=20)
    return {"mensagem": "Estoque populado com sucesso!"}

@app.get("/locais_do_produto/{produto_id}", response_model=list[schemas.EstoqueProdutoOut])
def locais_do_produto(produto_id: int, db: Session = Depends(get_db)):
    estoque_produto = db.query(models.Estoque).filter(models.Estoque.produto_id == produto_id).all()
    if not estoque_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado em nenhum local")
    return estoque_produto

# Movimentações
@app.get("/movimentacoes", response_model=list[schemas.Movimentacao])
def listar_movimentacoes(db: Session = Depends(get_db)):
    return crud.get_movimentacoes(db)

@app.post("/movimentacoes", response_model=schemas.Movimentacao)
def registrar_movimentacao(movimentacao: schemas.MovimentacaoCreate, db: Session = Depends(get_db)):
    return crud.create_movimentacao(db, movimentacao)

@app.get("/movimentacoes/filtrar", response_model=list[schemas.Movimentacao])
def filtrar_movimentacoes(
    tipo: str | None = Query(None, description="entrada ou saida"),
    produto_id: int | None = Query(None),
    local_id: int | None = Query(None),
    data_inicio: datetime | None = Query(None, description="Formato: YYYY-MM-DDTHH:MM:SS"),
    data_fim: datetime | None = Query(None, description="Formato: YYYY-MM-DDTHH:MM:SS"),
    db: Session = Depends(get_db)
):
    movimentacoes = crud.get_movimentacoes_filtradas(
        db,
        tipo=tipo,
        produto_id=produto_id,
        local_id=local_id,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
    if not movimentacoes:
        raise HTTPException(status_code=404, detail="Nenhuma movimentação encontrada com os filtros aplicados")
    return movimentacoes

@app.get("/relatorios/estoque-geral")
def estoque_geral(db: Session = Depends(get_db)):
    relatorio = crud.relatorio_estoque_geral(db)
    return relatorio

@app.get("/relatorios/resumo-movimentacoes")
def relatorio_resumo_movimentacoes_endpoint(db: Session = Depends(get_db)):
    return crud.relatorio_resumo_movimentacoes(db)

@app.get("/relatorios/estoque-produto/{produto_id}")
def relatorio_estoque_produto(produto_id: int, db: Session = Depends(get_db)):
    return crud.relatorio_estoque_por_produto(db, produto_id)

@app.get("/relatorios/movimentacoes")
def relatorio_movimentacoes_periodo(
    data_inicio: date,
    data_fim: date,
    db: Session = Depends(get_db)
):
    return crud.relatorio_movimentacoes_por_periodo(db, data_inicio, data_fim)

@app.get("/relatorios/resumo-movimentacoes")
def relatorio_resumo_movimentacoes(db: Session = Depends(get_db)):
    return crud.relatorio_resumo_movimentacoes(db)

@app.get("/relatorios/movimentacoes")
def relatorio_movimentacoes_periodo(
    data_inicio: date,
    data_fim: date,
    db: Session = Depends(get_db)
):
    try:
        resultado = crud.relatorio_movimentacoes_por_periodo(db, data_inicio, data_fim)
        return resultado
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        return {"erro": str(e), "traceback": traceback_str}

# --- Relatório estoque geral ---
@app.get("/relatorios/estoque-geral")
def estoque_geral(db: Session = Depends(get_db)):
    return crud.relatorio_estoque_geral(db)

# --- Relatório estoque por produto ---
@app.get("/relatorios/estoque-produto/{produto_id}")
def estoque_produto(produto_id: int, db: Session = Depends(get_db)):
    return crud.relatorio_estoque_por_produto(db, produto_id)

@app.get("/relatorios/inventario-por-local")
def inventario_por_local(db: Session = Depends(get_db)):
    return crud.relatorio_inventario_por_local(db)

# --- Relatórios de movimentações específicas
@app.get("/relatorios/operacoes")
def relatorio_operacoes_endpoint(db: Session = Depends(get_db)):
    return crud.relatorio_operacoes(db)

# --- QR Code Local ---
@app.get("/qrcode/local/{local_id}")
def endpoint_qrcode_local(local_id: int, db: Session = Depends(get_db)):
    local = db.query(models.Local).filter(models.Local.id == local_id).first()
    if not local:
        raise HTTPException(status_code=404, detail="Local não encontrado")
    # Gerar etiqueta QR Code usando a função correta
    return gerar_etiqueta_qr_rack(local.codigo, local.descricao, getattr(local, "rack_nivel", ""), local.id)

@app.get("/qrcode/produto/{produto_id}")
def endpoint_qrcode_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Usa a função de etiqueta de produto (com SKU, descrição e ID)
    return gerar_qr_code_produto(produto)

