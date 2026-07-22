import os
import pandas as pd
import numpy as np
from datetime import datetime

def test_split_logic():
    print(f"[{datetime.now()}] Iniciando SIMULAÇÃO de quebra de arquivo...")
    
    # Criando um DataFrame falso grande para simular > 50MB
    # 500.000 linhas com strings aleatórias geralmente passam de 50MB
    rows = 600000
    data = {
        'id': range(rows),
        'status': ['NEEDS_PROPOSAL_DATA'] * rows,
        'random_content': ['A' * 100] * rows # Adicionando peso
    }
    df = pd.DataFrame(data)
    
    output_dir = "/Users/thiago.dias/Documents/Safra Report Semanal/TEST_SIMULATION"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    base_filename = f"SIMULACAO_test_{timestamp}"
    temp_path = os.path.join(output_dir, f"{base_filename}_full.csv")
    
    print(f"Gerando arquivo de simulação...")
    df.to_csv(temp_path, index=False, encoding='utf-8-sig')
    file_size_mb = os.path.getsize(temp_path) / (1024 * 1024)
    
    print(f"Tamanho do arquivo simulado: {file_size_mb:.2f} MB")
    
    if file_size_mb > 50:
        print(f"[{datetime.now()}] Arquivo grande ({file_size_mb:.2f} MB). Iniciando quebra em partes de ~24.9 MB...")
        num_parts = int(-(file_size_mb // -24.9)) 
        rows_per_part = len(df) // num_parts + 1
        
        for i in range(num_parts):
            part_df = df.iloc[i*rows_per_part : (i+1)*rows_per_part]
            part_path = os.path.join(output_dir, f"{base_filename}_part{i+1}.csv")
            part_df.to_csv(part_path, index=False, encoding='utf-8-sig')
            print(f"Part {i+1} gerada: {part_path} ({os.path.getsize(part_path)/(1024*1024):.2f} MB)")
        
        os.remove(temp_path)
        print(f"[{datetime.now()}] Sucesso! Simulação concluída com {num_parts} partes.")
    else:
        print("A simulação não atingiu 50MB. Aumente o número de linhas.")

if __name__ == "__main__":
    test_split_logic()
