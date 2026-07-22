#!/usr/bin/env python3
"""
base_queima_hv.py — Gera base de queima HV (Trino) e exporta XLS para o Desktop.
Executar manualmente quando necessário.
"""

import json
import subprocess
import sys
import os
import ast
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    print("Erro: pandas não instalado. Execute: pip install pandas openpyxl")
    sys.exit(1)

try:
    import openpyxl
except ImportError:
    print("Erro: openpyxl não instalado. Execute: pip install openpyxl")
    sys.exit(1)


TRINO_BRIDGE = "/Users/thiago.dias/Documents/Main/Brain/Bridges/trino_mcp_bridge.py"
OUTPUT_DIR = os.path.expanduser("~/Desktop")

QUERY = """
WITH base_filtrada AS (
    SELECT 
        ad.list_id_nk,
        ad.ad_id_nk,
        ad.account_id_fk,
        veh.vehicle_tag,
        ROW_NUMBER() OVER(PARTITION BY veh.vehicle_tag ORDER BY ad.ad_id_nk DESC) as rn
    FROM 
        hive.ods.ad AS ad
    INNER JOIN 
        hive.olx_auto.listing_vehicle AS veh 
        ON ad.list_id_nk = veh.list_id_nk
    WHERE 
        ad.year = EXTRACT(YEAR FROM CURRENT_DATE - INTERVAL '1' MONTH)
        AND ad.month = EXTRACT(MONTH FROM CURRENT_DATE - INTERVAL '1' MONTH)
        AND ad.category_id_fk = 46 
        AND ad.deletion_date IS NULL 
        AND ad.ad_type_id_fk = 1
        AND veh.regdate >= 2024
        AND veh.vehicle_tag IS NOT NULL 
        AND TRIM(veh.vehicle_tag) <> ''
),
base_unica AS (
    SELECT 
        list_id_nk,
        ad_id_nk,
        account_id_fk,
        vehicle_tag
    FROM 
        base_filtrada
    WHERE 
        rn = 1
)
SELECT 
    bu.list_id_nk,
    bu.ad_id_nk,
    bu.vehicle_tag,
    acc.cpf,
    acc.account_id_pk,
    acc.account_id_nk,
    bu.account_id_fk
FROM 
    base_unica bu
INNER JOIN 
    hive.ods.account acc ON bu.account_id_fk = acc.account_id_pk
WHERE 
    acc.cpf IS NOT NULL 
    AND TRIM(acc.cpf) <> ''    
    AND NOT EXISTS (
        SELECT 1 
        FROM hive.olx_vas_premium.vehicle_history_daily vhd
        WHERE CAST(bu.list_id_nk AS VARCHAR) = vhd.list_id
          AND vhd.provider_queued_status = 'finished'
          AND vhd.paid = true
          AND (
              vhd.status = 'available'
              OR (
                  vhd.status IN ('manually_excluded', 'ad_excluded')
                  AND (vhd.provider_name = 'checktudo' AND vhd.provider_response_code = '200')
              )
          )
    )
ORDER BY 
    RANDOM() 
LIMIT 25000
"""


def trino_query(sql):
    """Executa query via MCP bridge do Trino."""
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "tools/call",
        "params": {"name": "query", "arguments": {"sql": sql, "max_rows": 30000}}
    })
    result = subprocess.run(
        ["python3", TRINO_BRIDGE],
        input=payload, capture_output=True, text=True, timeout=1800
    )
    if result.returncode != 0:
        raise RuntimeError(f"Erro no bridge Trino: {result.stderr}")
    
    data = json.loads(result.stdout)
    if "error" in data:
        raise RuntimeError(f"Erro Trino: {data['error']}")
    
    return data["result"]["content"][0]["text"]


def parse_response(raw_text):
    """Parseia a resposta do bridge (formato: Colunas: [...]\nDados: [...])."""
    lines = raw_text.split("\n", 1)
    cols_str = lines[0].replace("Colunas: ", "")
    data_str = lines[1].replace("Dados: ", "")
    
    columns = ast.literal_eval(cols_str)
    rows = ast.literal_eval(data_str)
    
    return columns, rows


def main():
    print("🔄 Executando query no Trino (pode levar alguns minutos)...")
    
    try:
        raw = trino_query(QUERY)
    except Exception as e:
        print(f"❌ Erro ao executar query: {e}")
        sys.exit(1)
    
    print("📊 Parseando resultados...")
    columns, rows = parse_response(raw)
    
    if not rows:
        print("⚠️  Query retornou 0 linhas. Nenhum arquivo gerado.")
        sys.exit(0)
    
    df = pd.DataFrame(rows, columns=columns)
    
    # Gerar nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"base_queima_hv_{timestamp}.xlsx"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Exportar XLS formatado
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Base Queima HV")
        
        # Ajustar largura das colunas
        ws = writer.sheets["Base Queima HV"]
        for col_idx, col_name in enumerate(df.columns, 1):
            max_len = max(
                df[col_name].astype(str).map(len).max() if len(df) > 0 else 0,
                len(col_name)
            ) + 2
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = min(max_len, 40)
    
    print(f"✅ Arquivo gerado: {filepath}")
    print(f"   Linhas: {len(df):,} | Colunas: {len(df.columns)}")


if __name__ == "__main__":
    main()
