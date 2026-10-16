# Método e dicionário de dados

## Escopo

Agregados diários fictícios de 01/01 a 29/06/2026, 180 dias × 3 produtos = 540 registros. Uma linha é um produto/dia, não uma transação individual. Transferências, Cobranças e Cartões são nomes genéricos; os valores não refletem tarifas, custos ou taxas reais. O projeto não processa dados pessoais nem modela crédito ou fraude.

## Contrato (`demo/transactions.csv`)

| Campo | Tipo | Significado / validação |
|---|---|---|
| `id` | texto | índice do dia e produto, único |
| `date` | ISO YYYY-MM-DD | data válida |
| `category` | enum | Transferências, Cobranças ou Cartões |
| `units` | inteiro > 0 | tentativas agregadas |
| `fee_cents` | inteiro > 0 | receita fictícia em centavos por operação concluída |
| `failure_pct` | inteiro 0–99 | percentual agregado de tentativas sem conclusão |
| `unit_cost_cents` | inteiro >= 0 | custo fictício em centavos por tentativa |

`validate` rejeita base vazia, id ou produto/data duplicado, tipo inteiro errado, categoria desconhecida, data inválida e domínio numérico incorreto. O gerador produz calendário completo; o contrato atual não verifica lacunas numa fonte externa. `quality.json` relata 540 chaves únicas, zero nulos e SHA-256 dos registros canônicos.

## Transformação contábil simplificada

SQLite em memória recebe os agregados validados. Para cada produto/dia, `successful = ROUND(units × (100 - failure_pct) / 100)`; `revenue_cents = successful × fee_cents`; `cost_cents = units × unit_cost_cents`; `profit_cents = revenue_cents - cost_cents`; `margin = profit_cents / revenue_cents`. O painel agrega somando numeradores e denominadores, sem média simples das margens. O arredondamento de conclusões é convenção da simulação. `profit_cents` é nome de coluna legado da implementação e representa apenas o resultado operacional simplificado.

Não inclui impostos, provisões, risco, capital, custos fixos, chargebacks ou conciliação. Não reproduz demonstrações financeiras de bancos.

## Anomalias operacionais

Após 28 observações do produto, usa somente as 28 anteriores. Calcula mediana e MAD da margem; limite = máximo entre 8 pontos percentuais e 4 × 1,4826 × MAD. Alerta se a margem cair além do limite, se o percentual de falhas ultrapassar a mediana anterior em mais de 5 p.p. ou se o volume ficar abaixo de 45% da mediana anterior. A evidência numérica acompanha cada alerta. MAD é medida robusta; o fator de escala não cria intervalo de confiança.

O gerador injeta falhas de 25% em Transferências nos dias de índice 65/95/125/155; custo 80% maior em Cobranças nos índices 75/105/135/165; volume de 300 em Cartões nos índices 85/115/145/175. Nos demais dias, volume possui ciclo semanal, tendência e ruído; falhas 0–3%; custo oscila até 2 centavos em relação ao fictício base. `ground_truth.csv` contém as 12 injeções e é acessado apenas pela avaliação. TP = interseção entre ids alertados e rotulados; FP e FN são diferenças de conjuntos. O avaliador identifica aquecimento pelo índice no id e é específico desta base.

## Previsão e avaliação temporal

Alvo: tentativas diárias (`units`) por produto. Baseline sazonal: repetir os últimos 7 dias, incluindo os próprios valores previstos em horizontes subsequentes. Modelo alternativo: Ridge com intercepto, tempo normalizado, seno/cosseno de período 7, defasagem 7 e média dos 7 anteriores. Regularização 0,1, fixa, sem seleção por teste; solução numérica 6×6 com pivoteamento parcial. Previsão recursiva de 28 passos, sem alimentar observações do teste. Valores negativos são truncados em zero.

Três origens por produto: treino expansivo de 84, 112 e 140 dias; testes seguintes de 28 dias. A janela anterior de 14 dias calibra uma faixa simétrica usando o percentil empírico 90% dos erros absolutos. Essa calibração usa modelo ajustado antes do bloco; o modelo de teste é reajustado em todo o histórico anterior à origem. Como são poucos resíduos dependentes, a faixa não garante cobertura de 90%. `backtest.csv` contém cada valor, previsão e limite; `forecast_metrics.csv` contém MAE, WAPE, viés e cobertura por produto/janela/modelo. `future_forecast.csv` traz 14 dias posteriores à base sem observações para aferir desempenho.

Na execução de referência, entre 252 previsões por modelo, WAPE do baseline = 7,7885%, Ridge = 6,4460%; MAE = 240,14 e 198,75 transações/dia. O Ridge perde nas origens 112 e 140 de Cartões, razão para manter comparação por janela no painel. Os intervalos empíricos cobriram 86,90% e 90,48%, respectivamente. Esse resultado é próprio do gerador, que inclui ciclo semanal e tendência próximos das features do Ridge. Não é evidência de generalização a bancos reais.

## Simulador

Volume inicial é a soma arredondada das previsões Ridge dos 14 dias futuros. Tarifa, custo por tentativa e percentual de falhas de referência vêm do último dia fictício do produto. Usuário altera tarifa, custo, falhas e variação percentual do volume. Conclusões são arredondadas ao inteiro antes de calcular receita; custo considera todas as tentativas. A tarifa de equilíbrio exibida é aproximação `custo/(1 - falhas/100)` e pode diferir alguns centavos no agregado por arredondamento. Não há elasticidade inferida, causalidade, otimização ou recomendação.

## Verificação e segurança

12 testes Python cobrem repetibilidade, contrato, cálculo manual, ausência de informação futura em alertas e previsões, baseline sazonal, solução linear, métricas manuais, contagem de janelas e série constante. Sete verificações JS cobrem cálculo e entradas do simulador. A CI regenera artefatos e compara com os versionados. O HTML incorpora somente a base sintética; o código não recebe CSV arbitrário no navegador. Não há autenticação, controle de acesso ou isolamento para dados reais.
