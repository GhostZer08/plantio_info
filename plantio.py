import qrcode
import json
from datetime import datetime

def coletar_informacoes():
    print("\n=== Cadastro de Informações de Plantio ===\n")
    
    info = {}
    
    info['nome_vegetal'] = input("Nome do vegetal: ")
    info['data_plantio'] = input("Data do plantio (DD/MM/AAAA): ")
    info['tipo_solo'] = input("Tipo de solo: ")
    info['frequencia_rega'] = input("Frequência de rega (ex: 2 vezes por semana): ")
    info['exposicao_sol'] = input("Exposição ao sol necessária (ex: pleno sol, meia sombra): ")
    info['tempo_colheita'] = input("Tempo estimado até a colheita (em dias): ")
    info['observacoes'] = input("Observações adicionais: ")
    
    # Adiciona data e hora do cadastro
    info['data_cadastro'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    return info

def gerar_qr_code(info):
    # Converte as informações para JSON
    dados_json = json.dumps(info, ensure_ascii=False, indent=2)
    
    # Gera o QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(dados_json)
    qr.make(fit=True)

    # Cria a imagem do QR Code
    imagem_qr = qr.make_image(fill_color="black", back_color="white")
    
    # Salva o QR Code
    nome_arquivo = f"plantio_qrcode_{info['nome_vegetal'].lower().replace(' ', '_')}.png"
    imagem_qr.save(nome_arquivo)
    return nome_arquivo

def main():
    print("Bem-vindo ao Sistema de Cadastro de Plantio!")
    
    # Coleta as informações
    info = coletar_informacoes()
    
    # Gera o QR Code
    nome_arquivo = gerar_qr_code(info)
    
    print(f"\nInformações cadastradas com sucesso!")
    print(f"QR Code gerado e salvo como: {nome_arquivo}")
    print("\nAo ler o QR Code, você verá todas as informações cadastradas.")

if __name__ == "__main__":
    main()
