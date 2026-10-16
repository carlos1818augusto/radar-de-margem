# Texto de publicação - Radar de Margem Financeiro

Em uma operação financeira, aumento de falhas, custo por tentativa e queda de volume podem mudar o resultado mesmo quando a receita total parece estável. Quis demonstrar como eu investigaria esse problema de ponta a ponta.

Construí o **Radar de Margem Financeiro**, uma plataforma demonstrativa para uma fintech fictícia. O projeto reúne:

• pipeline em Python e SQLite com validação de tipos, chaves e indicadores;
• alertas explicáveis de falhas, margem e volume, sempre comparados ao histórico anterior do mesmo produto;
• previsão recursiva de transações com baseline sazonal e regressão Ridge, avaliada em três janelas temporais sem usar o futuro;
• simulador de tarifa, falhas, custo e volume, com as premissas expostas na tela.

Os dados são **100% sintéticos**. Na simulação, os 12 cenários anômalos planejados foram detectados. Em 252 previsões avaliadas por modelo, o WAPE foi 7,79% no baseline e 6,45% no Ridge. O Ridge, porém, perdeu em duas janelas de Cartões; por isso mantive a comparação por produto no painel. Esses números não representam desempenho em banco real nem ganho financeiro de uma empresa.

O vídeo mostra a navegação pelo produto. O PDF documenta arquitetura, avaliação, resultados e limites. Código, dados e instruções para reproduzir: https://github.com/carlos1818augusto/radar-de-margem

Se você trabalha com Dados e IA em operações financeiras, o que consideraria indispensável antes de transformar uma demonstração assim em piloto? Fico feliz em trocar ideias sobre validação temporal, qualidade de dados e explicabilidade.

#EngenhariaDeDados #AnaliseDeDados #InteligenciaArtificial #Fintech #Python

## Antes de postar

Este texto menciona vídeo. Usar apenas depois que `docs/demo-plataforma.mp4` existir, estiver verificado e publicado. Em post com vídeo nativo, inserir no texto o link específico do PDF no GitHub para manter os dois acessíveis. Não associar o projeto a marcas de bancos reais.
