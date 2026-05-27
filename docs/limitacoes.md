# Limitacoes da pre-release

- Home Assistant e HACS validam compatibilidade tecnica, nao exatidao regulatoria.
- Sem consumo horario por posto, a comparacao de tarifa branca por periodo e estimativa.
- Extracao web de tributos pode quebrar por mudanca de layout sem aviso.
- Historico de creditos SCEE ainda esta em modo operacional inicial.
- Concessionarias com extracao parcial de tributos ficam fora do fluxo.
- Em caso de falha de fonte externa, a integracao conserva ultimo valor valido.
- O servidor da ANEEL (`dadosabertos.aneel.gov.br`) envia apenas o certificado leaf no handshake TLS, sem o intermediario Sectigo. A integracao empacota a cadeia completa em `custom_components/tarifas_energia_brasil/certs/aneel-trust-chain.pem` para que clientes com trust store recente (HA OS 17.3+, Python 3.14+) consigam verificar a conexao sem falhar com `unable to get local issuer certificate`.
