# Documentação técnica

## Contrato de dados

`sales.csv`: uma linha por categoria/dia, 01/01/2026 a 29/06/2026 (180 dias). Todas as quantias são fictícias.

| Campo | Tipo / unidade | Regra |
|---|---|---|
| id | texto | chave única; índice do dia + categoria |
| date | ISO YYYY-MM-DD | data válida |
| category | enum | Casa, Tecnologia, Esporte |
| units | inteiro | > 0 |
| price_cents | inteiro / centavos por unidade | > 0 |
| discount_pct | inteiro / percentual | 0 a 99 |
| unit_cost_cents | inteiro / centavos por unidade | >= 0 |

`validate` rejeita base vazia, duplicidade por id ou categoria/data, tipo numérico incorreto, categoria desconhecida, data inválida e valores fora de domínio. Ausência de coluna obrigatória aborta com KeyError; não há tratamento de CSV externo nesta versão. Completude temporal é garantida pelo gerador, não por validação de calendário.

## Transformação SQL

Uma tabela SQLite em memória recebe os registros validados. A consulta ordena por data e categoria e calcula:

```
revenue_cents = ROUND(units * price_cents * (100 - discount_pct) / 100)
cost_cents = units * unit_cost_cents
profit_cents = revenue_cents - cost_cents
margin = profit_cents / revenue_cents
```

A base atual não tem receita zero. Arredondamento no agregado diário é uma convenção simplificada; um sistema contábil real deve preservar a regra por item/documento fiscal.

## Detecção temporal

Para cada categoria, depois de 28 observações:

1. Mediana `m` das 28 margens anteriores.
2. MAD = mediana de `abs(margem - m)` na mesma janela.
3. Limite de queda = `max(0.08, 4 * 1.4826 * MAD)`.
4. Alertar quando `m - margem_atual > limite` OU `volume_atual < 0.45 * mediana_volume`.

O fator 1.4826 transforma MAD numa escala comparável ao desvio-padrão sob normalidade; não implica distribuição normal nem intervalo de confiança. Piso de 8 p.p. evita alertas por ruído pequeno e MAD zero. Os limiares não são aprendidos. A janela inclui anomalias passadas; mediana reduz sua influência, mas mudanças persistentes podem contaminar a referência. Não há detecção durante aquecimento nem tratamento de lacunas.

`alerts.csv` inclui os campos calculados, `reasons`, `baseline_margin` e `baseline_units`. A coluna reasons é a representação textual de uma lista Python; o CSV baixado pelo painel oferece uma evidência textual simples.

## Cenários e avaliação

Desconto de 32% em Casa nos índices 65, 95, 125 e 155; custo aumentado em 40% em Tecnologia nos índices 75, 105, 135 e 165; volume de 3 unidades em Esporte nos índices 85, 115, 145 e 175. Índice inicial zero. Nos demais dias, unidades entre 18 e 38, desconto entre 2% e 8%, custo base com ruído de até 200 centavos.

`ground_truth.csv` contém id e cenário. O detector recebe apenas linhas calculadas; a função de avaliação compara conjuntos de ids após aquecimento. TP = interseção; FP = detectados sem rótulo; FN = rótulos não detectados. Precisão = TP/(TP+FP); recall = TP/(TP+FN). Denominador zero retorna null.

O avaliador é específico do gerador: identifica aquecimento pelo índice no id. Não deve ser reaproveitado diretamente para bases externas. A execução padrão mediu 12 TP, 0 FP e 0 FN; o conjunto foi desenhado com anomalias fáceis e não é holdout.

## Verificação

Seis testes cobrem repetibilidade e mudança de seed, rejeição de entradas inválidas, cálculo financeiro com resultado manual, invariância dos alertas do passado ao modificar o futuro, aquecimento e detecção das injeções, e ausência de alertas em uma série constante.

Verificação de interface: painel real aberto no Chrome; filtro Casa retornou quatro alertas; filtros de data e exportação CSV revisados na entrega. Sem auditoria WCAG formal. Controles nativos, tabela semântica, foco de teclado e layout responsivo são usados.

## Artefatos e segurança

Nenhuma credencial, dado operacional, cliente real ou API paga é necessária. HTML embute apenas dados sintéticos gerados. Não abrir a arquitetura para entrada arbitrária sem sanitização e revisão da renderização HTML. O banco em memória não é persistido. Saídas são sobrescritas por execução; use `--output` para preservar uma versão.

## Licença

Código e materiais sob MIT; nomes e referências profissionais não implicam endosso empresarial.
