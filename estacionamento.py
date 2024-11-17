import sqlite3
from datetime import datetime

# Conectar ao banco de dados SQLite
conn = sqlite3.connect("estacionamento.db")
cursor = conn.cursor()

# Consultar todos os registros na tabela veiculos
cursor.execute("SELECT * FROM veiculos")
veiculos = cursor.fetchall()

# Exibir os registros encontrados de forma legível
if veiculos:
    for veiculo in veiculos:
        placa, nome_cliente, modelo_carro, vezes_visita, entrada, saida, valor_a_pagar, pago, rosto = veiculo

        # Converter os timestamps de entrada e saída para formato legível
        entrada_data = datetime.fromtimestamp(entrada).strftime('%Y-%m-%d %H:%M:%S') if entrada else "N/A"
        saida_data = datetime.fromtimestamp(saida).strftime('%Y-%m-%d %H:%M:%S') if saida else "N/A"

        # Verificar se o valor_a_pagar não é None antes de formatá-lo
        if valor_a_pagar is None:
            valor_a_pagar_display = "N/A"  # Valor não disponível
        else:
            valor_a_pagar_display = f"R$ {valor_a_pagar:.2f}"

        # Exibir as informações no formato desejado
        print(f"Placa: {placa}")
        print(f"Cliente: {nome_cliente}")
        print(f"Modelo do Carro: {modelo_carro}")
        print(f"Vezes de Visita: {vezes_visita}")
        print(f"Entrada: {entrada_data}")
        print(f"Saída: {saida_data}")
        print(f"Valor a Pagar: {valor_a_pagar_display}")
        print(f"Pago: {'Sim' if pago == 1 else 'Não'}")
        print(f"Rosto: {rosto}")
        print("-" * 40)  # Linha separadora para visualização mais clara
else:
    print("Nenhum veículo encontrado.")

# Fechar a conexão
conn.close()
