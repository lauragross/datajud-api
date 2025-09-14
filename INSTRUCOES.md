# Instruções de Uso - DataJud API Principal

## 🚀 Inicialização Rápida

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar Ambiente
```bash
# Copiar arquivo de configuração
cp config.env.example config.env

# Editar configurações se necessário
# (opcional - valores padrão funcionam para desenvolvimento)
```

### 3. Iniciar API
```bash
python app.py
```

### 4. Verificar Funcionamento
- **API**: http://localhost:5000
- **Swagger**: http://localhost:5000/apidocs
- **Health**: http://localhost:5000/health

## 🔧 Configurações Importantes

### Dependências da API de Tribunais
A API Principal depende da API de Tribunais rodando na porta 5001. Certifique-se de que ela está iniciada antes de usar esta API.

### Banco de Dados
- **Arquivo**: `datajud_processos.db`
- **Tipo**: SQLite
- **Localização**: Mesmo diretório da API
- **Criação**: Automática na primeira execução

## 📊 Endpoints Principais

### Consulta de Processos
```bash
# Listar processos
curl http://localhost:5000/processos

# Detalhes de um processo
curl http://localhost:5000/processo/1234567-89.2023.8.26.0100

# Movimentações de um processo
curl http://localhost:5000/movimentos/1234567-89.2023.8.26.0100
```

### Atualização do Banco
```bash
# Atualizar banco de dados
curl -X POST http://localhost:5000/update-database-stream
```

## 🛠️ Desenvolvimento

### Estrutura de Arquivos
```
datajud-api/
├── app.py              # Aplicação principal Flask
├── database.py         # Configuração do banco de dados
├── utils.py           # Utilitários gerais
├── dataframe_utils.py # Utilitários para dataframes
├── requirements.txt   # Dependências Python
├── config.env.example # Exemplo de configuração
└── README.md         # Documentação principal
```

### Logs e Debug
- Logs são exibidos no console
- Modo debug ativado por padrão em desenvolvimento
- Use `FLASK_DEBUG=False` em produção

## 🔍 Solução de Problemas

### API não inicia
1. Verifique se a porta 5000 está disponível
2. Confirme se todas as dependências foram instaladas
3. Verifique se a API de Tribunais está rodando

### Erro de banco de dados
1. Verifique permissões de escrita no diretório
2. Confirme se o arquivo `datajud_processos.db` pode ser criado
3. Verifique logs para erros específicos

### Erro de comunicação com API de Tribunais
1. Confirme se a API de Tribunais está rodando na porta 5001
2. Teste: `curl http://localhost:5001/health`
3. Verifique configuração `TRIBUNAIS_API_URL`
