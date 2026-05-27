# Adicao da concessionaria LIGHT-RJ

Data: 2026-05-27
Autor: brainstorming colaborativo (Patrick + assistente)
Escopo: registrar LIGHT-RJ como concessionaria suportada no fluxo, com fallback de tributos, faixas oficiais de ICMS-RJ e janela padrao de Tarifa Branca. Sem parser HTML novo nesta entrega.

## Objetivo

Permitir que usuarios cariocas selecionem `LIGHT-RJ` no fluxo de configuracao da integracao `tarifas_energia_brasil` e tenham:

- ANEEL coletada normalmente (TE/TUSD/Fio B/bandeira ja funcionam por filtro `SigAgente`/`SigNomeAgente`).
- Tributos (PIS, COFINS, ICMS) estimados via fallback inicial + faixas oficiais de ICMS-RJ ate que um parser HTML dedicado seja criado.
- Tarifa Branca classificada com janela padrao tipica da LIGHT.

## Decisoes de produto

- Nivel de suporte: **suportada** no fluxo de configuracao (com fallback). Sem parser HTML novo nesta entrega.
- ICMS-RJ: modelado como **faixas oficiais** em `icms_rules.py`, seguindo o padrao residencial RJ (FECP incluso).
- Tarifa Branca: janela **especifica LIGHT** cadastrada em `JANELAS_TARIFA_BRANCA_PADRAO`.
- Tributos PIS/COFINS: fallback padrao Brasil (1.10% / 5.02%) ate parser real.

## Identidade

- Chave do registry (constante interna e filtro ANEEL): `LIGHT-RJ`
- Slug HA: `light_rj`
- Identificador de extrator: `light_rj` (sem parser dedicado nesta entrega; o fluxo de `_fetch_and_parse_tributos` cai no retorno default de fallback ao nao bater nenhum `if` de roteamento)
- Confianca inicial: `ATTR_CONFIANCA_MEDIA` (sem parser validado ainda)
- Observacao no registry: "MVP LIGHT-RJ: fallback aplicado ate parser oficial."

## Pontos de mudanca no codigo

### 1. `custom_components/tarifas_energia_brasil/const.py`

Adicionar entrada em `CONCESSIONARIAS_SUPORTADAS`:

```python
"LIGHT-RJ": ConcessionariaInfo(
    slug="light_rj",
    nome="LIGHT-RJ",
    suportada=True,
    extrator_tributos="light_rj",
    confianca=ATTR_CONFIANCA_MEDIA,
    observacao="MVP LIGHT-RJ: fallback aplicado ate parser oficial.",
),
```

`obter_concessionarias_suportadas_para_fluxo()` ja ordena lexicograficamente, entao LIGHT-RJ vai aparecer entre CELESC e CPFL-PAULISTA sem mudanca extra.

### 2. `custom_components/tarifas_energia_brasil/tributos/__init__.py`

Adicionar entrada em `_TRIBUTOS_FALLBACK`:

```python
"LIGHT-RJ": TributosFallback(
    pis=1.10,
    cofins=5.02,
    icms=20.00,
    fonte="https://www.light.com.br/para-residencias/Sua-Conta/composicao-da-tarifa.aspx",
    confianca=ATTR_CONFIANCA_MEDIA,
    pendencias=(
        "Parser HTML LIGHT-RJ pendente; ICMS resolvido por faixa em icms_rules.py.",
    ),
),
```

Nao precisa novo `if` em `_fetch_and_parse_tributos`: na ausencia de parser especifico, a funcao retorna `(fallback.pis, fallback.cofins, fallback.icms)` no final. O `icms` da `TributosFallback` so e usado quando `resolve_icms_percent` nao consegue casar uma faixa (consumo invalido, sem historico, etc.).

### 3. `custom_components/tarifas_energia_brasil/icms_rules.py`

Adicionar entrada em `ICMS_RULES_BY_CONCESSIONARIA`:

```python
# LIGHT-RJ residencial (RJ baixa tensao): 0-50 isento; 51-300 20% (ICMS 18% + FECP 2%);
# acima de 300 32% (ICMS 29% + FECP 3%). Valores podem ser refinados quando o parser
# oficial entrar; faixa cheia segue padrao residencial RJ.
"LIGHT-RJ": [
    IcmsRangeRule(0, 50, 0.0),
    IcmsRangeRule(50.000001, 300, 20.0),
    IcmsRangeRule(300.000001, None, 32.0),
],
```

### 4. `custom_components/tarifas_energia_brasil/tarifa_branca_time.py`

Adicionar entrada em `JANELAS_TARIFA_BRANCA_PADRAO`:

```python
"LIGHT-RJ": {
    CONF_TB_PONTA_INICIO: "18:00",
    CONF_TB_PONTA_FIM: "21:00",
    CONF_TB_INTERMEDIARIO1_INICIO: "17:00",
    CONF_TB_INTERMEDIARIO1_FIM: "18:00",
    CONF_TB_INTERMEDIARIO2_INICIO: "21:00",
    CONF_TB_INTERMEDIARIO2_FIM: "22:00",
},
```

### 5. Documentacao

- `README.md` (secao "Concessionarias"): adicionar `LIGHT-RJ` em "Suportadas no fluxo de configuracao".
- `README.md` (secao "Fontes oficiais"): adicionar link `Light - Composicao da tarifa` apontando para a URL da fonte.
- `docs/concessionarias.md`: adicionar LIGHT-RJ em "Suportadas na pre-release" e citar pendencia de parser oficial.

## Testes

- `tests/test_icms_rules.py` — novo teste `test_icms_light_rj_by_range`:
  - 30 kWh → 0% (faixa isenta)
  - 150 kWh → 20% (faixa media)
  - 400 kWh → 32% (faixa cheia)
- `tests/test_tarifa_branca_time.py` — novo teste `test_resolve_tarifa_branca_schedule_defaults_light_rj`:
  - Verifica que `ponta_inicio=18:00`, `ponta_fim=21:00`, `intermediario_1=17:00-18:00`, `intermediario_2=21:00-22:00`.
  - Confirma que `source="default_concessionaria"`.

Se houver assercoes no codigo/testes sobre o conjunto exato de concessionarias suportadas (ex.: `set` literal em `test_config_flow.py`), atualizar para incluir `LIGHT-RJ`. A verificar durante a implementacao.

## Fora de escopo

- Parser HTML dedicado para `https://www.light.com.br/...` (entra em entrega futura, mesma estrategia de CEMIG-D/RGE SUL: parser + fixture + teste + elevar confianca para `ATTR_CONFIANCA_ALTA`).
- Bump de versao no `const.py` / entrada no `CHANGELOG.md`. Sera decidido junto da implementacao.
- Marca/icone proprio da LIGHT em `custom_components/tarifas_energia_brasil/brand/` (reutiliza icone padrao da integracao).

## Riscos

- Faixas de ICMS-RJ podem variar por decreto estadual (FECP especialmente). Mantemos comentario explicando origem das faixas para reavaliacao facil quando o parser real entrar.
- Confianca inicial `MEDIA` sinaliza ao usuario, via atributos das entidades, que o valor e fallback e nao coleta oficial.

## Criterio de pronto

- LIGHT-RJ aparece em `obter_concessionarias_suportadas_para_fluxo()`.
- Fluxo de config nao quebra ao selecionar LIGHT-RJ; entidades coletam ANEEL normalmente.
- ICMS varia por faixa quando o consumo apurado existe.
- Tarifa Branca classifica corretamente intervalos de exemplo (18:30 → ponta, 17:30 → intermediario, 22:30 → fora_ponta).
- Testes novos e existentes passam.
