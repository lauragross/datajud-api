import os, re, time, json
import pandas as pd
import requests
from datetime import datetime, timezone
from sqlalchemy import create_engine, text

# =========================
# CONFIGURAÇÕES
# =========================
# 1) Excel de entrada com uma coluna "numeroProcesso"
lista_processos = "processos.xlsx"

# 2) Banco SQLite de saída
db_path = "datajud_processos.db"

# 3) URL do componente de consulta aos tribunais
TRIBUNAIS_API_URL = os.getenv("TRIBUNAIS_API_URL", "http://localhost:5001")

# 4) Modo de operação: 'api' para usar API separada, 'direto' para consulta direta
MODO_OPERACAO = os.getenv("MODO_OPERACAO", "api")  # Modo API

# 5) Limites e tolerância
sleep_between = 0.3  # pausa entre requisições
request_timeout = 30
size = 10

# 6) Tribunais e API Key (para modo direto)
endpoints = {
    "TJAC": "https://api-publica.datajud.cnj.jus.br/api_publica_tjac/_search",
    "TJAL": "https://api-publica.datajud.cnj.jus.br/api_publica_tjal/_search",
    "TJAM": "https://api-publica.datajud.cnj.jus.br/api_publica_tjam/_search",
    "TJAP": "https://api-publica.datajud.cnj.jus.br/api_publica_tjap/_search",
    "TJBA": "https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search",
    "TJCE": "https://api-publica.datajud.cnj.jus.br/api_publica_tjce/_search",
    "TJDFT": "https://api-publica.datajud.cnj.jus.br/api_publica_tjdft/_search",
    "TJES": "https://api-publica.datajud.cnj.jus.br/api_publica_tjes/_search",
    "TJGO": "https://api-publica.datajud.cnj.jus.br/api_publica_tjgo/_search",
    "TJMA": "https://api-publica.datajud.cnj.jus.br/api_publica_tjma/_search",
    "TJMG": "https://api-publica.datajud.cnj.jus.br/api_publica_tjmg/_search",
    "TJMS": "https://api-publica.datajud.cnj.jus.br/api_publica_tjms/_search",
    "TJMT": "https://api-publica.datajud.cnj.jus.br/api_publica_tjmt/_search",
    "TJPA": "https://api-publica.datajud.cnj.jus.br/api_publica_tjpa/_search",
    "TJPB": "https://api-publica.datajud.cnj.jus.br/api_publica_tjpb/_search",
    "TJPE": "https://api-publica.datajud.cnj.jus.br/api_publica_tjpe/_search",
    "TJPI": "https://api-publica.datajud.cnj.jus.br/api_publica_tjpi/_search",
    "TJPR": "https://api-publica.datajud.cnj.jus.br/api_publica_tjpr/_search",
    "TJRJ": "https://api-publica.datajud.cnj.jus.br/api_publica_tjrj/_search",
    "TJRN": "https://api-publica.datajud.cnj.jus.br/api_publica_tjrn/_search",
    "TJRO": "https://api-publica.datajud.cnj.jus.br/api_publica_tjro/_search",
    "TJRR": "https://api-publica.datajud.cnj.jus.br/api_publica_tjrr/_search",
    "TJRS": "https://api-publica.datajud.cnj.jus.br/api_publica_tjrs/_search",
    "TJSC": "https://api-publica.datajud.cnj.jus.br/api_publica_tjsc/_search",
    "TJSE": "https://api-publica.datajud.cnj.jus.br/api_publica_tjse/_search",
    "TJSP": "https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search",
    "TJTO": "https://api-publica.datajud.cnj.jus.br/api_publica_tjto/_search"
}

api_key = os.getenv("DATAJUD_APIKEY", "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==")

# =========================
# FUNÇÕES
# =========================
def normaliza_nup(n):
    """
    Remove tudo que não for dígito e corrige notação científica vinda do Excel.
    Aceita entradas como:
      '0425144-44.2016.8.19.0001' -> '04251444420168190001'
      1.01779912E+18 -> '101779912017501000'
    """
    s = str(n).strip()
    # Se veio como notação científica, pandas pode ter convertido para float
    if re.match(r"^\d+(\.\d+)?e\+\d+$", s, re.I):
        try:
            as_int = int(float(s))
            return re.sub(r"\D", "", str(as_int))
        except Exception:
            pass
    # remove tudo que não for dígito
    return re.sub(r"\D", "", s)

def consulta_por_numero_direto(endpoint, numero):
    """
    Consulta um tribunal específico pelo numeroProcesso (modo direto).
    Retorna o JSON (dict) ou erro em dict.
    """
    headers = {
        "Authorization": f"ApiKey {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "size": size,
        "query": {
            "match": {
                "numeroProcesso": numero
            }
        }
    }
    try:
        r = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=request_timeout)
        if r.status_code == 200:
            return r.json()
        else:
            return {"_error": True, "status": r.status_code, "text": r.text}
    except requests.RequestException as e:
        return {"_error": True, "exception": str(e)}

def consulta_via_tribunais_api(numero, tribunal=None):
    """
    Consulta um processo via API de tribunais ou modo direto.
    Retorna o JSON (dict) ou erro em dict.
    """
    if MODO_OPERACAO == "direto":
        # Modo direto - consulta direta aos tribunais
        if tribunal:
            endpoint = endpoints.get(tribunal)
            if endpoint:
                return consulta_por_numero_direto(endpoint, numero)
            else:
                return {"_error": True, "message": f"Tribunal {tribunal} não encontrado"}
        else:
            # Buscar em todos os tribunais
            for trib, endpoint in endpoints.items():
                resp = consulta_por_numero_direto(endpoint, numero)
                if resp and not resp.get("_error"):
                    hits = resp.get("hits", {}).get("hits", [])
                    if hits:
                        return resp
                time.sleep(sleep_between)
            return {"_error": True, "message": "Processo não encontrado em nenhum tribunal"}
    else:
        # Modo API - usar API separada
        try:
            url = f"{TRIBUNAIS_API_URL}/consultar-processo"
            payload = {"numero": numero}
            if tribunal:
                payload["tribunal"] = tribunal
            
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("sucesso") and result.get("encontrado"):
                    return result["dados"]
                else:
                    return {"_error": True, "message": result.get("erro", "Processo não encontrado")}
            else:
                return {"_error": True, "status": response.status_code, "text": response.text}
        except requests.RequestException as e:
            return {"_error": True, "exception": str(e)}

def extrai_registros(hit_json):
    """
    A partir do JSON do DataJud, extrai 1..N documentos (hits) em duas tabelas:
      - processos: capa e campos principais
      - movimentos: lista de movimentos (1:N)
    Retorna (df_proc, df_mov)
    """
    if not hit_json or "hits" not in hit_json or "hits" not in hit_json["hits"]:
        return pd.DataFrame(), pd.DataFrame()

    procs, movs = [], []
    for h in hit_json["hits"]["hits"]:
        src = h.get("_source", {})
        numero = src.get("numeroProcesso")
        procs.append({
            "id": src.get("id"),
            "tribunal": src.get("tribunal"),
            "numeroProcesso": numero,
            "grau": src.get("grau"),
            "dataAjuizamento": src.get("dataAjuizamento"),
            "nivelSigilo": src.get("nivelSigilo"),
            "classe_codigo": (src.get("classe") or {}).get("codigo"),
            "classe_nome": (src.get("classe") or {}).get("nome"),
            "formato_codigo": (src.get("formato") or {}).get("codigo"),
            "formato_nome": (src.get("formato") or {}).get("nome"),
            "sistema_codigo": (src.get("sistema") or {}).get("codigo"),
            "sistema_nome": (src.get("sistema") or {}).get("nome"),
            "orgaoJulgador_codigo": (src.get("orgaoJulgador") or {}).get("codigo"),
            "orgaoJulgador_nome": (src.get("orgaoJulgador") or {}).get("nome"),
            "orgaoJulgador_codigoMunicipioIBGE": (src.get("orgaoJulgador") or {}).get("codigoMunicipioIBGE"),
            "dataHoraUltimaAtualizacao": src.get("dataHoraUltimaAtualizacao"),
            "timestamp_indice": src.get("@timestamp"),
        })
        for m in (src.get("movimentos") or []):
            movs.append({
                "numeroProcesso": numero,
                "mov_codigo": m.get("codigo"),
                "mov_nome": m.get("nome"),
                "mov_dataHora": m.get("dataHora"),
                "mov_orgao_codigo": (m.get("orgaoJulgador") or {}).get("codigoOrgao"),
                "mov_orgao_nome": (m.get("orgaoJulgador") or {}).get("nomeOrgao"),
            })
    return pd.DataFrame(procs), pd.DataFrame(movs)

def ensure_schema(sqlite_path=db_path):
    """
    Cria as tabelas base e a nova tabela processos_lista (índice mestre).
    A tabela processos_lista impede reprocessamentos: se o número já está lá,
    o script ignora esse processo em execuções futuras.
    """
    eng = create_engine(f"sqlite:///{sqlite_path}")
    with eng.begin() as con:
        # Tabela principal de processos
        con.execute(text("""
        CREATE TABLE IF NOT EXISTS processos (
            id TEXT,
            tribunal TEXT,
            numeroProcesso TEXT,
            grau TEXT,
            dataAjuizamento TEXT,
            nivelSigilo INTEGER,
            classe_codigo INTEGER,
            classe_nome TEXT,
            formato_codigo INTEGER,
            formato_nome TEXT,
            sistema_codigo INTEGER,
            sistema_nome TEXT,
            orgaoJulgador_codigo INTEGER,
            orgaoJulgador_nome TEXT,
            orgaoJulgador_codigoMunicipioIBGE INTEGER,
            dataHoraUltimaAtualizacao TEXT,
            timestamp_indice TEXT
        )
        """))

        # Movimentos (1:N)
        con.execute(text("""
        CREATE TABLE IF NOT EXISTS movimentos (
            numeroProcesso TEXT,
            mov_codigo INTEGER,
            mov_nome TEXT,
            mov_dataHora TEXT,
            mov_orgao_codigo INTEGER,
            mov_orgao_nome TEXT
        )
        """))

        # NOVA TABELA: índice mestre de processos
        # - numeroProcesso como PRIMARY KEY evita duplicatas
        # - armazena quando entrou e onde foi encontrado pela primeira vez
        con.execute(text("""
        CREATE TABLE IF NOT EXISTS processos_lista (
            numeroProcesso TEXT PRIMARY KEY,
            tribunal_inicial TEXT,
            primeiraInclusao TEXT,
            ultimoUpdate TEXT
        )
        """))

        # Índices úteis (opcionais)
        con.execute(text("CREATE INDEX IF NOT EXISTS ix_proc_numero ON processos (numeroProcesso)"))
        con.execute(text("CREATE INDEX IF NOT EXISTS ix_mov_numero ON movimentos (numeroProcesso)"))

def carrega_lista_existente(sqlite_path=db_path):
    """
    Lê a lista de processos já cadastrados em processos_lista e retorna um set.
    """
    eng = create_engine(f"sqlite:///{sqlite_path}")
    try:
        df_exist = pd.read_sql("SELECT numeroProcesso FROM processos_lista", eng)
        return set(df_exist["numeroProcesso"].astype(str).tolist())
    except Exception:
        return set()

def insere_na_processos_lista(numero, tribunal, sqlite_path=db_path):
    """
    Insere o número na tabela processos_lista (se ainda não existir).
    Como a PRIMARY KEY é numeroProcesso, repetição será ignorada usando UPSERT.
    """
    eng = create_engine(f"sqlite:///{sqlite_path}")
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds").replace('+00:00', 'Z')
    with eng.begin() as con:
        con.execute(text("""
            INSERT INTO processos_lista (numeroProcesso, tribunal_inicial, primeiraInclusao, ultimoUpdate)
            VALUES (:n, :t, :agora, :agora)
            ON CONFLICT(numeroProcesso) DO UPDATE SET ultimoUpdate = excluded.ultimoUpdate
        """), {"n": numero, "t": tribunal, "agora": agora})

def grava_sqlite(dfp, dfm, sqlite_path=db_path):
    eng = create_engine(f"sqlite:///{sqlite_path}")
    with eng.begin() as con:
        if not dfp.empty:
            dfp.to_sql("processos", con, if_exists="append", index=False)
        if not dfm.empty:
            dfm.to_sql("movimentos", con, if_exists="append", index=False)

def limpar_banco_dados(sqlite_path=db_path):
    """
    Limpa completamente o banco de dados, removendo todos os dados das tabelas.
    """
    eng = create_engine(f"sqlite:///{sqlite_path}")
    with eng.begin() as con:
        # Limpar todas as tabelas
        con.execute(text("DELETE FROM processos"))
        con.execute(text("DELETE FROM movimentos"))
        con.execute(text("DELETE FROM processos_lista"))
        print("Banco de dados limpo com sucesso.")

def verificar_tribunais_api():
    """
    Verifica se a API de tribunais está disponível.
    """
    try:
        response = requests.get(f"{TRIBUNAIS_API_URL}/health", timeout=10)
        return response.status_code == 200
    except:
        return False

def main():
    try:
        print("Iniciando processamento do banco de dados...")
        print(f"[CONFIG] Modo de operação: {MODO_OPERACAO}")
        
        if MODO_OPERACAO == "api":
            # Verificar se a API de tribunais está disponível
            print(f"Verificando API de tribunais em: {TRIBUNAIS_API_URL}")
            if not verificar_tribunais_api():
                print("[ERRO] API de tribunais não está disponível!")
                print("   Para corrigir:")
                print("   1. Inicie o componente datajud-tribunais-api:")
                print("      cd datajud-tribunais-api")
                print("      python app.py")
                print("   2. Verifique se está rodando na porta 5001")
                print("   3. Execute este script novamente")
                return
            
            print("[OK] API de tribunais está disponível")
        else:
            print("[OK] Modo direto ativado - consultando tribunais diretamente")
        
        # Garante o schema (inclui a nova tabela processos_lista)
        ensure_schema(db_path)
        print("Schema do banco verificado")
        
        # Verificar estado atual do banco antes de limpar
        eng = create_engine(f"sqlite:///{db_path}")
        with eng.begin() as con:
            count_before = con.execute(text("SELECT COUNT(*) FROM processos")).fetchone()[0]
            print(f"Processos existentes no banco: {count_before}")
        
        # Limpar o banco de dados completamente
        limpar_banco_dados(db_path)
        print("Banco de dados limpo para nova atualização")

        # Verificar se o arquivo existe
        if not os.path.exists(lista_processos):
            raise FileNotFoundError(f"Arquivo {lista_processos} não encontrado")

        # Ler Excel
        print(f"Lendo arquivo: {lista_processos}")
        df = pd.read_excel(lista_processos)
        
        if df.empty:
            raise ValueError("Arquivo Excel está vazio")
            
        if "numeroProcesso" not in df.columns:
            raise ValueError("O Excel precisa ter a coluna 'numeroProcesso'.")

        print(f"Arquivo lido com {len(df)} linhas")

        # Verificar se tem coluna tribunal
        tem_tribunal = "tribunal" in df.columns
        if tem_tribunal:
            print("[OK] Coluna 'tribunal' encontrada - usando otimização por tribunal específico")
        else:
            print("[AVISO] Coluna 'tribunal' não encontrada - usando busca em todos os tribunais")

        # Normalizar números
        df["numero_limpo"] = df["numeroProcesso"].map(normaliza_nup)
        
        # Separar números válidos e inválidos
        df_validos = df[df["numero_limpo"].str.len() >= 15]
        df_invalidos = df[df["numero_limpo"].str.len() < 15]
        
        numeros_excel = df_validos["numero_limpo"].astype(str).unique().tolist()
        numeros_invalidos = df_invalidos["numeroProcesso"].astype(str).unique().tolist()
        
        print(f"Processando {len(numeros_excel)} números únicos válidos do Excel...")
        if numeros_invalidos:
            print(f"[AVISO] {len(numeros_invalidos)} números inválidos (muito curtos) serão reportados como não encontrados: {numeros_invalidos}")

        total_ok = 0
        total_nao_encontrados = 0
        total_tribunais_nao_encontrados = 0
        total_invalidos = len(numeros_invalidos)

        # Iterar e consultar cada número
        for i, numero in enumerate(numeros_excel, 1):
            print(f"[{i}/{len(numeros_excel)}] Processando {numero}...")
            encontrado = False
            
            # Obter dados do processo
            processo_row = df[df["numero_limpo"] == numero].iloc[0]
            tribunal_especifico = processo_row.get("tribunal") if tem_tribunal else None

            if tem_tribunal and tribunal_especifico:
                # OTIMIZAÇÃO: consultar apenas o tribunal específico
                print(f"  [ALVO] Consultando apenas {tribunal_especifico}...")
                try:
                    resp = consulta_via_tribunais_api(numero, tribunal_especifico)
                    if resp and not resp.get("_error"):
                        hits = resp.get("hits", {}).get("hits", [])
                        if hits:
                            dfp, dfm = extrai_registros(resp)
                            grava_sqlite(dfp, dfm, db_path)
                            # registra no índice mestre (processos_lista)
                            insere_na_processos_lista(numero, tribunal_especifico, db_path)
                            print(f"[OK] {numero} encontrado em {tribunal_especifico}")
                            total_ok += 1
                            encontrado = True
                        else:
                            print(f"[AVISO] {numero} não encontrado em {tribunal_especifico}")
                    else:
                        print(f"[AVISO] {numero} erro em {tribunal_especifico}: {resp.get('message', 'Erro desconhecido')}")
                except Exception as e:
                    print(f"[AVISO] {numero} erro em {tribunal_especifico}: {str(e)}")
                    
                time.sleep(sleep_between)
                
                if not encontrado:
                    total_tribunais_nao_encontrados += 1
                    
            else:
                # Fallback: buscar em todos os tribunais
                print(f"  [BUSCA] Buscando em todos os tribunais...")
                try:
                    resp = consulta_via_tribunais_api(numero)
                    if resp and not resp.get("_error"):
                        hits = resp.get("hits", {}).get("hits", [])
                        if hits:
                            dfp, dfm = extrai_registros(resp)
                            grava_sqlite(dfp, dfm, db_path)
                            # registra no índice mestre (processos_lista)
                            # Tentar extrair tribunal do resultado
                            tribunal_encontrado = "DESCONHECIDO"
                            if hits and "_source" in hits[0]:
                                tribunal_encontrado = hits[0]["_source"].get("tribunal", "DESCONHECIDO")
                            insere_na_processos_lista(numero, tribunal_encontrado, db_path)
                            print(f"[OK] {numero} encontrado em {tribunal_encontrado}")
                            total_ok += 1
                            encontrado = True
                        else:
                            print(f"[AVISO] {numero} não encontrado em nenhum tribunal")
                    else:
                        print(f"[AVISO] {numero} erro na consulta: {resp.get('message', 'Erro desconhecido')}")
                except Exception as e:
                    print(f"[AVISO] {numero} erro na consulta: {str(e)}")
                        
                time.sleep(sleep_between)

                if not encontrado:
                    print(f"[ERRO] {numero} não encontrado")
                    total_nao_encontrados += 1

        # Verificar estado final do banco
        eng = create_engine(f"sqlite:///{db_path}")
        with eng.begin() as con:
            count_after = con.execute(text("SELECT COUNT(*) FROM processos")).fetchone()[0]
            count_movimentos = con.execute(text("SELECT COUNT(*) FROM movimentos")).fetchone()[0]
        
        print(f"\nCONCLUÍDO!")
        print(f"Processos encontrados: {total_ok}")
        if tem_tribunal:
            print(f"Processos não encontrados no tribunal específico: {total_tribunais_nao_encontrados}")
        else:
            print(f"Processos não encontrados: {total_nao_encontrados}")
        if total_invalidos > 0:
            print(f"Processos inválidos (muito curtos): {total_invalidos}")
        print(f"Banco: {db_path}")
        print(f"Total de processos no banco: {count_after}")
        print(f"Total de movimentos no banco: {count_movimentos}")
        
        if tem_tribunal:
            print(f"\n[OTIMIZAÇÃO] ATIVA: Cada processo foi consultado apenas no tribunal específico!")
            print(f"   Isso reduz significativamente o tempo de processamento.")
        
        if MODO_OPERACAO == "api":
            print(f"\n[ARQUITETURA] Usando componente separado de consulta aos tribunais!")
            print(f"   API de tribunais: {TRIBUNAIS_API_URL}")
        else:
            print(f"\n[ARQUITETURA] Usando modo direto para consulta aos tribunais!")
            print(f"   Consultas diretas para DataJud CNJ")
        
        if count_after == 0:
            print("ATENÇÃO: Banco ficou vazio! Verifique:")
            print("   - Se a API de tribunais está funcionando")
            print("   - Conexão com a internet")
            print("   - Disponibilidade da API DataJud")
            print("   - Se os números na planilha são válidos")
            if tem_tribunal:
                print("   - Se os códigos de tribunal na planilha estão corretos")
        
    except Exception as e:
        print(f"ERRO FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
