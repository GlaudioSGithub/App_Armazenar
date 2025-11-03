from io import BytesIO
import qrcode
from PIL import Image, ImageDraw, ImageFont
from fastapi.responses import StreamingResponse
from datetime import datetime

# Caminho da fonte
FONT_PATH = "arial.ttf"

# --- Geração do QR Code ---
def gerar_qr_code_img(dados: str, tamanho_qr: int = 150):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=3,
        border=4,
    )
    qr.add_data(dados)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img = img.resize((tamanho_qr, tamanho_qr))
    return img


# --- Etiqueta simples (para locais / racks) ---
def gerar_etiqueta_qr_rack(codigo: str, descricao: str, rack_nivel: str, id_item: int):
    qr_img = gerar_qr_code_img(f"{codigo} - {descricao} - ID: {id_item}")

    largura, altura = 510, 200
    etiqueta = Image.new("RGB", (largura, altura), "white")
    draw = ImageDraw.Draw(etiqueta)

    etiqueta.paste(qr_img, (10, 25))

    try:
        font_size = qr_img.height
        font = ImageFont.truetype(FONT_PATH, size=font_size)
    except:
        font = ImageFont.load_default()

    x_text = 10 + qr_img.width + 10
    y_text = 20

    # Texto do rack (negrito simulado com largura maior)
    txt_img = Image.new("RGB", (400, qr_img.height), (255, 255, 255))
    draw_txt = ImageDraw.Draw(txt_img)
    draw_txt.text((0, 0), rack_nivel, font=font, fill="black")

    largura_desejada = 400
    txt_img = txt_img.resize((largura_desejada, qr_img.height))
    etiqueta.paste(txt_img, (x_text, y_text))

    buf = BytesIO()
    etiqueta.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


# --- Etiqueta completa (para produtos) ---
def gerar_etiqueta_qr_produto(produto):
    qr_img = gerar_qr_code_img(f"{produto.sku} - {produto.descricao} - ID: {produto.id}")

    largura, altura = 400, 150
    etiqueta = Image.new("RGB", (largura, altura), "white")
    draw = ImageDraw.Draw(etiqueta)

    etiqueta.paste(qr_img, (2, 2))

    try:
        font_bold = ImageFont.truetype(FONT_PATH, 16)
        font_regular = ImageFont.truetype(FONT_PATH, 16)
    except:
        font_bold = ImageFont.load_default()
        font_regular = ImageFont.load_default()

    x_text = 5 + qr_img.width + 10
    y_text = 20

    # SKU
    font_sku = ImageFont.truetype(FONT_PATH, 20)
    draw.text((x_text, y_text), f"SKU: {produto.sku}", fill="black", font=font_sku)
    y_text += 30

    # Descrição
    texto_desc = f"Descrição: {produto.descricao}"
    max_width = largura - x_text - 20
    espaco_disponivel = 50

    font_desc, linhas_desc = ajustar_fonte_para_cabimento(draw, texto_desc, max_width, espaco_disponivel, FONT_PATH, tamanho_inicial=16)
    for linha in linhas_desc:
        bbox = draw.textbbox((0,0), linha, font=font_desc)
        altura_linha = bbox[3] - bbox[1]
        draw.text((x_text, y_text), linha, fill="black", font=font_desc)
        y_text += altura_linha + 4

    # AUMENTAR ESPAÇAMENTO ANTES DO LOTE
    y_text += 10  # adiciona 10px de espaço extra

    # Lote e Validade
    lote = getattr(produto, "lote", "") or ""
    validade = getattr(produto, "validade", "") or ""

    if validade:
        try:
            validade_date = (
                datetime.strptime(validade, "%Y-%m-%d").strftime("%d/%m/%Y")
                if isinstance(validade, str)
                else validade.strftime("%d/%m/%Y")
            )
        except:
            validade_date = str(validade)
    else:
        validade_date = ""

    draw.text((x_text, y_text), f"LOTE: {lote}", fill="black", font=font_regular)
    y_text += 20
    draw.text((x_text, y_text), f"Validade: {validade_date}", fill="black", font=font_regular)

    buf = BytesIO()
    etiqueta.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


# --- Ajuste automático da fonte da descrição ---
def ajustar_fonte_para_cabimento(draw, texto, max_width, max_altura, font_path, tamanho_inicial=16):
    tamanho = tamanho_inicial
    try:
        font = ImageFont.truetype(font_path, tamanho)
    except:
        font = ImageFont.load_default()
    
    while True:
        linhas = []
        palavras = texto.split()
        linha = ""
        for palavra in palavras:
            teste = linha + palavra + " "
            largura_linha = draw.textlength(teste, font=font)
            if largura_linha <= max_width:
                linha = teste
            else:
                linhas.append(linha.strip())
                linha = palavra + " "
        if linha:
            linhas.append(linha.strip())

        altura_texto = 0
        for l in linhas:
            bbox = draw.textbbox((0,0), l, font=font)
            altura_linha = bbox[3] - bbox[1]
            altura_texto += altura_linha + 4

        if altura_texto <= max_altura or tamanho <= 8:
            break
        tamanho -= 1
        try:
            font = ImageFont.truetype(font_path, tamanho)
        except:
            font = ImageFont.load_default()

    return font, linhas


# --- Funções de acesso rápido ---
def gerar_qr_code_local(local):
    return gerar_etiqueta_qr_rack(local.codigo, local.descricao, local.descricao, local.id)


def gerar_qr_code_produto(produto):
    return gerar_etiqueta_qr_produto(produto)
