# Tribunal IA Portugal V7

**Apoio cognitivo à decisão judicial** com 7 agentes LLM, RAG jurídico híbrido, 
conformidade RGPD, auditoria encadeada e arquitectura preparada para implantação `.gov`.

> ⚠️ **Apoio cognitivo — não substitui magistrado.** Nenhum output deste sistema 
> tem efeitos jurídicos vinculativos.

---

## Melhorias de Segurança V7.1 (vs V7.0)

| # | Problema | Correcção |
|---|----------|-----------|
| 1 | JWT com fallback `demo_*` inseguro | Falha hard se `python-jose` ausente |
| 2 | CORS aberto para `*` | Restrito a origens explícitas; `*` bloqueia em produção |
| 3 | Rate limiting opcional/silencioso | Obrigatório em `GOV_MODE`/`ENV=production` |
| 4 | OpenRouter envia dados para fora da UE | Bloqueado em `GOV_MODE=true`; aviso em dev |
| 5 | Pseudónimos determinísticos (correlação entre casos) | Salt aleatório por sessão |
| 6 | Anonimização sem padrões PT governamentais | Adicionados: SNS, matrículas, refs MB, processos reais |
| 7 | Dados de auditoria em texto plano | Encriptação Fernet (AES-128-CBC) em repouso |
| 8 | Docker como root | Utilizador `tribunal:tribunal` (non-root) |
| 9 | Race condition em `os.environ["MODELO"]` | Substituição de modelo bloqueada em `GOV_MODE` |
| 10 | `API_SECRET_KEY` padrão aceite em produção | Validação hard em `ENV=production`/`GOV_MODE` |
| 11 | Sem reverse proxy TLS | Nginx com TLS 1.3, HSTS, CSP, rate limiting |
| 12 | Rede Docker exposta | Rede interna isolada (`internal: true`) |

---

## Arranque Rápido (Desenvolvimento)

### 1. Pré-requisitos

```bash
python 3.11+   ollama   docker (opcional)
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar

```bash
cp .env.example .env
# Edita .env — no mínimo define BACKEND e OLLAMA_MODELO
```

### 4. Arrancar Ollama

```bash
ollama serve
ollama pull llama3.3:70b   # ou outro modelo
```

### 5. Interface

```bash
# Windows
iniciar_interface.bat

# Linux/macOS
chmod +x iniciar_interface.sh && ./iniciar_interface.sh

# Directo
streamlit run app.py
```

### 6. API REST (opcional)

```bash
python api_server.py
# → http://localhost:8000/docs
```

---

## Implantação em Produção / GOV_MODE

### Gerar chaves seguras

```bash
python gerar_chaves.py
# Copia os valores para o .env
```

### Gerar certificados TLS (desenvolvimento/teste)

```bash
chmod +x gerar_certificados.sh && ./gerar_certificados.sh
```

Em produção usa certificados da **SCEE** (https://www.scee.gov.pt) ou Let's Encrypt.

### Docker Compose

```bash
# Definir variáveis obrigatórias no .env do host:
# API_SECRET_KEY=<chave gerada>
# AUDIT_ENCRYPTION_KEY=<chave fernet>
# GOV_MODE=true
# BACKEND=ollama

cd src/docker
docker compose up -d
```

### Variáveis obrigatórias em produção

| Variável | Descrição |
|----------|-----------|
| `API_SECRET_KEY` | ≥32 chars, gerada com `secrets.token_hex(32)` |
| `AUDIT_ENCRYPTION_KEY` | Chave Fernet gerada com `Fernet.generate_key()` |
| `BACKEND=ollama` | Obrigatório em `GOV_MODE=true` |
| `API_CORS_ORIGINS` | Domínios explícitos (sem `*`) |
| `GOV_MODE=true` | Activa todas as validações de segurança |

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                     Nginx (TLS 1.3)                      │
│              Rate limiting + Security headers             │
└─────────────┬───────────────────────┬───────────────────┘
              │                       │
     ┌────────▼────────┐    ┌─────────▼────────┐
     │  Streamlit UI   │    │    API REST V7    │
     │   app.py        │    │  src/api/         │
     └────────┬────────┘    └─────────┬────────┘
              └─────────┬─────────────┘
                        │
              ┌─────────▼─────────┐
              │  CaseProcessor    │
              │  src/pipeline/    │
              │                   │
              │  7 Agentes LLM    │
              │  (LangGraph/Imp.) │
              └──┬────────────┬───┘
                 │            │
      ┌──────────▼──┐   ┌─────▼──────────┐
      │  RAG Híbrido│   │  TribunalBrain │
      │  BM25+Embed │   │  Ollama/OR     │
      │  + Reranking│   │  mTLS + CB     │
      └─────────────┘   └────────────────┘
```

### Módulos principais

| Módulo | Descrição |
|--------|-----------|
| `src/pipeline/` | Orquestração dos 7 agentes (LangGraph ou imperativo) |
| `src/agents/` | Detetive, Acusação, Defesa, 3× Sentenças, Consistência |
| `src/rag/` | Motor RAG híbrido (BM25 + embeddings PT + reranking) |
| `src/auditoria/` | Cadeia de hash, provenance, voto de vencido, validação input |
| `src/api/` | FastAPI com JWT, rate limiting, CORS restrito |
| `src/utils/` | Config, Brain (LLM), Logger, Anonimizador RGPD |
| `src/cache/` | Cache semântico de respostas LLM |
| `src/historico/` | Persistência e pesquisa de casos |
| `src/observability/` | Prometheus + OpenTelemetry |
| `src/export/` | Export PDF/TXT de atas |
| `src/contraditorio/` | Gestor de intervenções do utilizador |

---

## Conformidade .gov — Checklist

- [x] Autenticação JWT sem fallback inseguro
- [x] CORS restrito a origens explícitas
- [x] Rate limiting obrigatório em produção
- [x] Bloqueio OpenRouter em GOV_MODE (soberania de dados)
- [x] Anonimização RGPD com padrões PT (NIF, CC, SNS, matrículas, etc.)
- [x] Pseudónimos não-determinísticos (sem correlação entre casos)
- [x] Encriptação em repouso (Fernet AES-128-CBC)
- [x] Execução Docker como utilizador não-root
- [x] Rede Docker interna isolada
- [x] Reverse proxy Nginx com TLS 1.3 e HSTS
- [x] Headers de segurança (CSP, X-Frame-Options, etc.)
- [x] Validação e sanitização de inputs (anti-prompt-injection)
- [x] Cadeia de auditoria imutável (hash encadeado)
- [x] Disclaimer de separação de papéis
- [ ] DPIA (Data Protection Impact Assessment) — RGPD Art. 35 — _a fazer_
- [ ] Autenticação com Cartão de Cidadão (autenticacao.gov.pt) — _integração futura_
- [ ] Certificados SCEE em produção — _requer acesso a infra.gov.pt_
- [ ] SBOM (Software Bill of Materials) + assinatura de imagens — _CI/CD_

---

## Licença

Projecto de investigação e desenvolvimento. 
Não aprovado para uso com dados reais de cidadãos sem DPIA e homologação.
