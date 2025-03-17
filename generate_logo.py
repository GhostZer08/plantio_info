from PIL import Image, ImageDraw, ImageFont
import os

# Criar uma nova imagem com fundo transparente
width = 400
height = 200
image = Image.new('RGBA', (width, height), (255, 255, 255, 0))
draw = ImageDraw.Draw(image)

# Cores do SIPLAN
verde_escuro = (46, 139, 87)  # Verde escuro
verde_claro = (154, 205, 50)  # Verde claro

# Desenhar o texto "SIPLAN"
try:
    font = ImageFont.truetype("arial.ttf", 60)
except:
    font = ImageFont.load_default()

# Posição do texto
text_bbox = draw.textbbox((0, 0), "SIPLAN", font=font)
text_width = text_bbox[2] - text_bbox[0]
text_height = text_bbox[3] - text_bbox[1]
text_x = (width - text_width) // 2
text_y = (height - text_height) // 2

# Desenhar o texto
draw.text((text_x, text_y), "SIPLAN", fill=verde_escuro, font=font)

# Desenhar a barra verde clara
bar_height = 30
bar_y = text_y + text_height + 10
draw.rectangle([(0, bar_y), (width, bar_y + bar_height)], fill=verde_claro)

# Texto menor
subtitle = "SISTEMA BRASILEIRO DE LICENCIAMENTO AMBIENTAL"
try:
    small_font = ImageFont.truetype("arial.ttf", 14)
except:
    small_font = ImageFont.load_default()

# Centralizar o subtítulo
sub_bbox = draw.textbbox((0, 0), subtitle, font=small_font)
sub_width = sub_bbox[2] - sub_bbox[0]
sub_x = (width - sub_width) // 2
sub_y = bar_y + (bar_height - 14) // 2

# Desenhar o subtítulo
draw.text((sub_x, sub_y), subtitle, fill="white", font=small_font)

# Salvar a imagem
image.save(os.path.join("static", "logo.png"), "PNG")
