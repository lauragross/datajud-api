# DataJud API Principal

API principal do sistema DataJud para consulta de processos jurídicos com arquitetura de microserviços.

## 🏗️ Arquitetura

Este é o componente central do sistema DataJud, responsável por:
- Lógica de negócio e persistência de dados
- Comunicação com a API de Tribunais
- Gerenciamento do banco de dados SQLite
- Endpoints REST para o frontend

## 🚀 Como Executar

### Pré-requisitos
- Python 3.7+
- API de Tribunais rodando na porta 5001

### Instalação
```bash
pip install -r requirements.txt
```

### Execução
```bash
python app.py
```

A API estará disponível em: `http://localhost:5000`

## 📊 Endpoints

### Processos
- `GET /processos` - Lista processos com filtros
- `GET /processo/{numero}` - Detalhes completos de um processo
- `GET /movimentos/{numero}` - Movimentações de um processo
- `GET /processos-lista` - Lista mestre de processos

### Filtros e Atualizações
- `GET /tribunais` - Lista tribunais disponíveis
- `GET /categorias` - Lista categorias disponíveis
- `GET /atualizacoes-dataframe` - Processos agrupados por período
- `POST /update-database-stream` - Atualização do banco com streaming

### Sistema
- `GET /health` - Health check
- `GET /apidocs` - Documentação Swagger

## 🗄️ Banco de Dados

Utiliza SQLite (`datajud_processos.db`) com as seguintes tabelas:
- **processos**: Informações principais dos processos jurídicos
- **movimentos**: Histórico de movimentações (relacionamento 1:N)
- **processos_lista**: Lista mestre para controle de atualizações

## 🔧 Configuração

### Variáveis de Ambiente
```bash
MODO_OPERACAO=api
TRIBUNAIS_API_URL=http://localhost:5001
DATAJUD_APIKEY=cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==
```

### Dependências
- Flask 2.3.0+
- SQLAlchemy 2.0.0+
- Flask-CORS 4.0.0+
- Pandas 2.0.0+
- Requests 2.31.0+

## 📚 Documentação

- **Swagger**: http://localhost:5000/apidocs
- **Health Check**: http://localhost:5000/health

## 🔄 Comunicação

### Com API de Tribunais
```python
# Consulta processo via API de Tribunais
def consulta_via_tribunais_api(numero, tribunal=None):
    url = f"{TRIBUNAIS_API_URL}/consultar-processo"
    payload = {"numero": numero}
    response = requests.post(url, json=payload, timeout=60)
    return response.json()
```

### Com Frontend
- CORS habilitado para `datajud-ui`
- Endpoints REST com JSON
- Paginação e filtros

## 🧪 Testes

```bash
# Teste de health check
curl http://localhost:5000/health

# Teste de listagem de processos
curl http://localhost:5000/processos
```

## 📝 Notas

- Porta padrão: 5000
- Modo API-only (sem dependências diretas)
- Cache inteligente no SQLite
- Documentação automática via Swagger
