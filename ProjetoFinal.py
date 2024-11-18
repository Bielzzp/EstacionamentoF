import cv2
import sqlite3
import time
import re
import mediapipe as mp

# Conectar ao banco de dados SQLite
conn = sqlite3.connect("estacionamento.db")
cursor = conn.cursor()

# Criar a tabela de cadastro
cursor.execute(""" 
CREATE TABLE IF NOT EXISTS veiculos (
    placa TEXT PRIMARY KEY,
    nome_cliente TEXT,
    modelo_carro TEXT,
    vezes_visita INTEGER DEFAULT 0,
    entrada TIMESTAMP,
    saida TIMESTAMP,
    valor_a_pagar REAL,
    pago INTEGER DEFAULT 0
)
""")
conn.commit()

# Função para validar a placa
def validar_placa(placa):
    return re.match(r'^[A-Z]{3}\d[A-Z]\d{2}$', placa) is not None

# Função para validar se a entrada é apenas texto (letras e espaços)
def validar_texto(texto):
    return bool(re.match(r"^[A-Za-z\s]+$", texto))  # Aceita apenas letras e espaços

# Função para cadastrar novo veículo
def cadastrar_veiculo(placa, nome_cliente, modelo_carro):
    cursor.execute("SELECT * FROM veiculos WHERE placa = ?", (placa,))
    veiculo = cursor.fetchone()

    if veiculo:
        # Cliente já cadastrado, incrementar visitas
        vezes_visita = veiculo[3] + 1
        cursor.execute(""" 
            UPDATE veiculos SET vezes_visita = ?, entrada = ?, pago = 0 WHERE placa = ? 
        """, (vezes_visita, time.time(), placa))
    else:
        # Novo cadastro
        cursor.execute(""" 
            INSERT INTO veiculos (placa, nome_cliente, modelo_carro, vezes_visita, entrada) 
            VALUES (?, ?, ?, ?, ?) 
        """, (placa, nome_cliente, modelo_carro, 1, time.time()))

    conn.commit()

# Função para registrar a saída
def registrar_saida(placa, valor_hora):
    cursor.execute("SELECT * FROM veiculos WHERE placa = ?", (placa,))
    veiculo = cursor.fetchone()

    if veiculo:
        entrada = veiculo[4]
        vezes_visita = veiculo[3]
        saida = time.time()
        tempo_passado = (saida - entrada) / 3600  # Converter para horas
        valor_a_pagar = tempo_passado * valor_hora if vezes_visita % 10 != 0 else 0  # Saída grátis a cada 10 visitas

        # Garantir que o valor a pagar não seja negativo
        if valor_a_pagar < 0:
            valor_a_pagar = 0

        cursor.execute(""" 
            UPDATE veiculos 
            SET saida = ?, valor_a_pagar = ?, pago = ? 
            WHERE placa = ? 
        """, (saida, valor_a_pagar, 1 if valor_a_pagar == 0 else 0, placa))

        conn.commit()
        return valor_a_pagar
    else:
        print("Veículo não encontrado.")
        return None

# Função para processar o pagamento
def processar_pagamento(placa):
    cursor.execute("SELECT valor_a_pagar FROM veiculos WHERE placa = ?", (placa,))
    valor_a_pagar = cursor.fetchone()

    if valor_a_pagar and valor_a_pagar[0] > 0:
        pagamento = int(input("Digite 1 se foi pago ou 2 se não foi: "))
        cursor.execute("UPDATE veiculos SET pago = ? WHERE placa = ?", (pagamento == 1, placa))
        conn.commit()
    else:
        print("Nenhum pagamento pendente ou saída gratuita por fidelidade.")

# Função para detectar rostos e identificar cliente
def detectar_rosto():
    
    # Inicializando o MediaPipe
    mp_face_detection = mp.solutions.face_detection
    mp_drawing = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(0)

    # Verificar se a captura foi iniciada corretamente
    if not cap.isOpened():
        print("Erro ao abrir o vídeo ou câmera.")
        exit()

    rosto_detectado = False

    with mp_face_detection.FaceDetection(min_detection_confidence=0.6) as face_detection:
     # O 'with' cria um contexto para o uso do modelo de detecção facial. Assim, ele é iniciado e, ao final, liberado automaticamente.
        
        while True:
            confirmar, imagem = cap.read() # 'confirmar' é um valor booleano que indica se a captura foi bem-sucedida;
            if not confirmar: 
                print("Não foi possível capturar o vídeo.")
                break

            imagem_rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB) #'cv2.COLOR_BGR2RGB' -> parâmetro que especifica o tipo de conversão;
            resultados = face_detection.process(imagem_rgb)

            # Verifica se há alguma detecção de rosto na imagem
            if resultados.detections:
                rosto_detectado = True
                
                # Itera sobre todas as detecções de rostos detectadas na imagem (caso haja mais de um rosto)
                for detection in resultados.detections:
                    
                    # Acessa a caixa delimitadora (bounding box) do rosto detectado
                    bboxC = detection.location_data.relative_bounding_box
                     
                    # Obtém as dimensões da imagem capturada
                    ih, iw, _ = imagem.shape
                    
                    # Calcula as coordenadas x, y, largura (w) e altura (h) da caixa delimitadora
                     # A caixa delimitadora retornada pelo MediaPipe está normalizada (valores entre 0 e 1), por isso multiplicam   
                     # pelas dimensões da imagem para obter as coordenadas reais em pixels.
                    x, y, w, h = int(bboxC.xmin * iw), int(bboxC.ymin * ih), int(bboxC.width * iw), int(bboxC.height * ih)
                    
                    # Desenhar a caixa de detecção no rosto
                    cv2.rectangle(imagem, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    # x = linha horizontal superior esquerda
                    # y = linha vertical superior esquerda
                    # Desenhar retângulos ao redor das faces de perfil detectadas            
                    # (x + w, y + h): Coordenadas do canto inferior direito do retângulo; w é a largura e h é a altura.
                    # (0, 255, 0): Cor do retângulo em formato RGB (verde).
                    # 2: Espessura da linha do retângulo, em pixels.

             # Mostrar a imagem com as faces detectadas
            cv2.imshow("Reconhecimento Facial", imagem)

            # Sair do loop se a tecla 'q' for pressionada
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    # Liberar a captura e fechar as janelas            
    cap.release()
    cv2.destroyAllWindows()
    return rosto_detectado

# Função principal para controlar entrada e saída
def controle_estacionamento():
    while True:
        acao = input("Digite 'entrar' para novo veículo ou 'sair' para veículo saindo (pressione 'q' para sair do programa): ").strip().lower()

        if acao == "entrar":
            if detectar_rosto():
                print("Cliente reconhecido.")
                placa = input("Placa do carro (formato AAA1A11): ")

                if validar_placa(placa):
                    cadastrar_veiculo(placa, None, None)
                    cursor.execute("SELECT * FROM veiculos WHERE placa = ?", (placa,))
                    veiculo = cursor.fetchone()

                    if veiculo and veiculo[3] == 1:  # Se a contagem de visitas for 1, significa que é um novo cadastro
                        nome_cliente = input("Nome do cliente: ")
                    
                        # Garantir que o nome do cliente seja válido
                        while not validar_texto(nome_cliente):
                            print("Nome inválido. O nome deve conter apenas letras e espaços.")
                            nome_cliente = input("Nome do cliente: ")
                            
                        modelo_carro = input("Modelo do carro: ")

                        cursor.execute("""
                            UPDATE veiculos SET nome_cliente = ?, modelo_carro = ? WHERE placa = ?
                        """, (nome_cliente, modelo_carro, placa))
                        conn.commit()

                    print("Veículo registrado com sucesso.")
                else:
                    print("Placa inválida. A placa deve seguir o formato AAA1A11.")

            else:
                print("Nenhum rosto detectado. Tente novamente.")

        elif acao == "sair":
            if detectar_rosto():
                print("Cliente reconhecido.")
            placa = input("Placa do carro: ")
            valor_hora = float(input("Valor da hora: "))

            # Garantir que o valor da hora seja positivo
            while valor_hora < 0:
                print("O valor da hora não pode ser negativo.")
                valor_hora = float(input("Valor da hora: "))

            valor_a_pagar = registrar_saida(placa, valor_hora)

            if valor_a_pagar == 0:
                print("Saída gratuita por fidelidade!")
            elif valor_a_pagar is not None:
                print(f"Valor a ser pago: R$ {valor_a_pagar:.2f}")
                processar_pagamento(placa)
            else:
                print("Veículo não encontrado.")

        elif acao == "q":
            print("Saindo do programa...")
            break

        else:
            print("Ação inválida. Tente novamente.")

# Executar o controle de estacionamento
if __name__ == "__main__":
    controle_estacionamento()
