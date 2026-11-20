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
   - **Dimensões de Entrada:** 
     - Entrada Visual: `224 x 224 x 3` (RGB)
     - Entrada de Metadados: vetor `[None, 3]` (contendo a fração da área da máscara calculada)
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
│   │   ├── image_processor.py   # Utilitários de imagem, redimensionamento e Base64
│   │   ├── inference_service.py # Orquestrador da inferência ponta a ponta
│   │   └── model_loader.py      # Gerenciador Singleton de modelos Keras em memória
│   ├── static/core/         # Arquivos estáticos (mockup visual)
│   ├── templates/core/      # Templates HTML (interface gráfica)
│   ├── admin.py             # Configuração do Django Admin (com visualização de miniaturas)
│   ├── api_views.py         # Endpoints da API REST
│   ├── models.py            # Entidade de persistência (BovineAnalysis)
│   ├── serializers.py       # Serializadores do Django REST Framework (Swagger Binary)
│   ├── tests.py             # Suíte completa de testes automatizados (9 testes)
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

## 📖 Documentação da API REST

A API do BoviScan permite submeter imagens de perfil lateral de bovinos e receber a estimativa biométrica completa.

### Endpoint Principal
`POST /api/v1/cattle/analyze/`

- **Tipo de Requisição:** `multipart/form-data`
- **Parâmetros:**
  - `image` *(obrigatório)*: Arquivo de imagem do bovino (formatos: JPEG, PNG, WebP).

### Exemplo de Requisição via cURL
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/cattle/analyze/" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "image=@boi1.png"
```

### Exemplo de Resposta (HTTP 201 Created)
```json
{
  "id": 1,
  "uuid": "7a3e819b-21d4-4a25-97fc-7d63259ce361",
  "estimated_weight": "208.81",
  "mask_area_percentage": 36.16,
  "confidence_score": 94.0,
  "inference_time_ms": 348,
  "original_image": "/media/bovines/original/2026/11/20/boi1.png",
  "mask_image": "/media/bovines/masks/2026/11/20/mask_boi1.png",
  "mask_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA...",
  "overlay_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...",
  "device_used": "CPU (Sem GPU dedicada detectada - executando via processador)",
  "created_at": "2026-11-20T10:45:00.123456Z"
}
```

---

## 🖥️ Testando via Swagger UI e Painel Administrativo

### 1. Documentação Interativa (Swagger)
Acesse pelo navegador:
👉 **[http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)**
- Expanda a rota `POST /api/v1/cattle/analyze/`.
- Clique em **"Try it out"**.
- O campo `image` possui um botão para anexar o arquivo diretamente da galeria/computador.
- Clique em **"Execute"** para inspecionar os retornos numéricos e as imagens.

### 2. Painel Administrativo Django
Acesse pelo navegador:
👉 **[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)**
- Todas as análises realizadas ficam salvas na tabela **Análises Bovinas**.
- Exibe miniaturas lado a lado da foto original e da máscara calculada.
- Para criar novos administradores via linha de comando:
  ```bash
  python manage.py createsuperuser
  ```

---

## 🧪 Execução dos Testes Automatizados

O projeto conta com uma suíte de 9 testes automatizados cobrindo persistência no banco, pré-processamento de imagem, inferência de IA com modelo real e integração da API REST:
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
- [x] **Passo 3: Pipeline de Inferência de Inteligência Artificial**
  - Implementação do Singleton para carregamento dos modelos Keras em memória ([core/services/model_loader.py](file:///c:/Users/lucas/Documents/GitHub/IC-Bovi-Scan/core/services/model_loader.py)).
  - Pipeline de pré/pós-processamento e overlay de imagem ([core/services/image_processor.py](file:///c:/Users/lucas/Documents/GitHub/IC-Bovi-Scan/core/services/image_processor.py)).
  - Módulo orquestrador de inferência biométrica ([core/services/inference_service.py](file:///c:/Users/lucas/Documents/GitHub/IC-Bovi-Scan/core/services/inference_service.py)).
  - Testes unitários com a imagem real de bovino (`boi1.png`) aprovados com 100% de sucesso.
- [x] **Passo 4: Endpoint REST e Documentação Interativa (Swagger)**
  - Criação do endpoint `POST /api/v1/cattle/analyze/` ([core/api_views.py](file:///c:/Users/lucas/Documents/GitHub/IC-Bovi-Scan/core/api_views.py)).
  - Serialização completa com suporte a upload multipart (`format: binary`), persistência no banco e retorno com imagens em Base64 e URLs de mídia.
  - Testes de integração via `APIClient` e validação do esquema OpenAPI 3.0.3 (9 testes executados com status `OK`).
- [x] **Passo 5: Conclusão, Ajustes Finais e Documentação de Uso**
  - Documentação completa da API com exemplos práticos (cURL e JSON).
  - Guia de utilização do Swagger UI e visualização de miniaturas no Django Admin.
  - Higienização e revisão de conformidade PEP 8 em todos os módulos.
  - Quality Gate final com 100% dos testes unitários e de integração aprovados.
