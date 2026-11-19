# IC-Bovi-Scan 🐄📸

**Sistema Inteligente de Análise Biométrica e Estimativa de Peso Corporal Bovino por Visão Computacional**

Projeto desenvolvido no âmbito de Iniciação Científica (IC). O objetivo é fornecer uma solução automatizada e não invasiva capaz de analisar fotografias de perfil lateral de bovinos (*side profile*), delimitar a silhueta corporal do animal através de segmentação semântica e estimar seu peso corporal em quilogramas (kg) utilizando redes neurais convolucionais profundas.

---

## 🧠 Modelos de Inteligência Artificial

Os modelos treinados encontram-se no diretório `modelos/` e são versionados com **Git LFS**:

1. **Segmentação Corporal (`best_seg_model_y.zip`)**:
   - **Arquitetura:** `EfficientNetB4_UNet`
   - **Framework:** Keras 3 (TensorFlow backend)
   - **Dimensão de Entrada:** `224 x 224 x 3` (RGB)
   - **Objetivo:** Isolar a área corporal do animal (máscara binária) e calcular a área percentual ocupada pela silhueta.

2. **Regressão de Peso (`best_transfer_reg_model.zip`)**:
   - **Arquitetura:** `EfficientNetB0_SideProfile_Regressor`
   - **Framework:** Keras 3 (TensorFlow backend)
   - **Dimensão de Entrada:** `224 x 224 x 3` (RGB)
   - **Objetivo:** Predição contínua do peso vivo do bovino em kg.

---

## 📐 Padrões e Convenções do Código

Para manter a organização, legibilidade e compatibilidade em ambientes corporativos e acadêmicos:
- **Código (Identificadores, Variáveis, Métodos, Classes e URLs):** Totalmente em **Inglês** (ex: `BovineAnalysis`, `predict_weight()`, `/api/v1/cattle/analyze/`).
- **Documentação (Docstrings, Comentários e README):** Em **Português (pt-br)**, explicando detalhadamente regras de negócio, parâmetros de entrada, tipos de retorno e exceções.
- **Transição de Etapas (Quality Gates):** Cada etapa do desenvolvimento é acompanhada de testes automatizados para garantir a estabilidade do sistema antes de avançar para a próxima fase.

---

## 📁 Estrutura do Projeto

```text
IC-Bovi-Scan/
├── config/                  # Configurações globais do Django (settings, urls, wsgi, asgi)
├── core/                    # Aplicativo principal
│   ├── migrations/          # Histórico de migrações do banco de dados
│   ├── services/            # Camada de serviços (Pipeline de IA, Pré/Pós-processamento)
│   ├── static/core/         # Arquivos estáticos (mockup visual)
│   ├── templates/core/      # Templates HTML (interface gráfica)
│   ├── admin.py             # Configuração do Django Admin
│   ├── api_views.py         # Endpoints da API REST
│   ├── models.py            # Entidades do Banco de Dados (BovineAnalysis)
│   ├── serializers.py       # Serializadores do Django REST Framework
│   ├── tests.py             # Testes automatizados (Unitários e Integração)
│   ├── urls.py              # Rotas internas do app core
│   └── views.py             # Views para renderização de páginas
├── media/                   # Diretório de armazenamento de uploads e máscaras (ignorado no git)
├── modelos/                 # Modelos treinados (.zip gerenciados via Git LFS)
├── .env.example             # Exemplo de configuração de variáveis de ambiente
├── .gitattributes           # Regras do Git LFS para arquivos pesados
├── .gitignore               # Arquivos e diretórios ignorados pelo controle de versão
├── manage.py                # Utilitário CLI do Django
├── README.md                # Documentação técnica do projeto
└── requirements.txt         # Especificação de dependências do Python
```

---

## 🚀 Guia de Instalação e Execução

### Pré-requisitos
- **Python 3.10+** (Recomendado: Python 3.11)
- **Git** e **Git LFS** instalados na máquina

### 1. Clonar o Repositório e Baixar os Modelos (Git LFS)
```bash
git clone https://github.com/lrocha97/IC-Bovi-Scan.git
cd IC-Bovi-Scan

# Garantir que os arquivos .zip dos modelos foram baixados integralmente pelo Git LFS
git lfs pull
```

### 2. Criar e Ativar o Ambiente Virtual (`venv`)

- **No Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

- **No macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as Dependências
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar as Variáveis de Ambiente
Copie o arquivo de exemplo `.env.example` para `.env`:
```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

### 5. Executar as Migrações do Banco de Dados
```bash
python manage.py migrate
```

### 6. Iniciar o Servidor de Desenvolvimento
```bash
python manage.py runserver
```
O servidor estará acessível em: `http://127.0.0.1:8000/`.

---

## 📖 Documentação da API (Swagger / OpenAPI 3)

Com o servidor em execução, acesse a documentação interativa para testar os endpoints e inspecionar os esquemas de dados:
- **Swagger UI:** [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **Schema OpenAPI (YAML/JSON):** [http://127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/)

---

## 🧪 Execução dos Testes Automatizados

Para rodar todos os testes de validação das camadas de IA, persistência e API:
```bash
python manage.py test
```

---

## 🗺️ Roteiro de Implementação (Roadmap)

- [x] **Passo 1: Dependências, Estrutura Base e Documentação**
  - Padronização do `requirements.txt`.
  - Configuração do `settings.py` com suporte a arquivos de mídia (`media/`) e documentação Swagger (`drf-spectacular`).
  - Criação do `README.md` e `.env.example`.
- [x] **Passo 2: Modelagem de Dados e Persistência (`BovineAnalysis`)**
  - Criação da entidade de histórico no `core/models.py`.
  - Configuração do painel administrativo no `core/admin.py`.
  - Preparação para chaveamento entre SQLite e PostgreSQL via variáveis de ambiente.
  - Testes automatizados do modelo executados com sucesso (`Ran 2 tests ... OK`).
- [ ] **Passo 3: Pipeline de Inferência de Inteligência Artificial**
  - Implementação do Singleton para carregamento dos modelos Keras em memória (`core/services/model_loader.py`).
  - Pipeline de pré-processamento de imagem (`core/services/image_processor.py`).
  - Módulo orquestrador de inferência (`core/services/inference_service.py`).
  - Testes unitários com a imagem real de bovino (`boi1.png`).
- [ ] **Passo 4: Endpoint REST e Documentação Interativa**
  - Criação do endpoint `POST /api/v1/cattle/analyze/`.
  - Retorno em JSON com estimativa de peso, métricas e máscara codificada em Base64.
  - Testes de integração via `APIClient`.
- [ ] **Passo 5: Conclusão, Ajustes Finais e Documentação de Uso**
