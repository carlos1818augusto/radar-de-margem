"""Gera o PDF do projeto. Requer reportlab (e Pillow para a captura opcional)."""
from pathlib import Path
import csv
import json
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
report = json.loads((ROOT/'demo/report.json').read_text(encoding='utf-8'))
predictions = list(csv.DictReader((ROOT/'demo/backtest.csv').open(encoding='utf-8')))
out = ROOT/'docs/radar-margem-carrossel.pdf'
c = canvas.Canvas(str(out), pagesize=(720,900))
c.setTitle('Radar de Margem Financeiro | demonstração sintética')
c.setAuthor('Carlos Augusto Rodrigues Teixeira')

def line(s,y,size=25,color='#E4EDF8',width=600):
    p=Paragraph(s,ParagraphStyle('x',fontName='Helvetica',fontSize=size,leading=size*1.32,textColor=HexColor(color)))
    _,h=p.wrap(width,800);p.drawOn(c,60,y-h);return y-h-25

def page(n,title,tag):
    c.setFillColor(HexColor('#0B1423'));c.rect(0,0,720,900,fill=1,stroke=0)
    c.setFillColor(HexColor('#55DFBF'));c.rect(60,824,64,5,fill=1,stroke=0)
    line(tag.upper(),800,14,'#55DFBF')
    y=line(title,751,43,'#FFFFFF')
    c.setStrokeColor(HexColor('#2D4059'));c.line(60,70,660,70)
    line('CARLOS AUGUSTO RODRIGUES TEIXEIRA  |  DADOS E IA',54,10)
    c.setFont('Helvetica',11);c.setFillColor(HexColor('#55DFBF'));c.drawRightString(660,38,f'{n:02} / 08')
    return y

def finish():c.showPage()

y=page(1,'Radar de Margem Financeiro','Plataforma demonstrativa')
y=line('Inteligência operacional para uma fintech fictícia.',y-25,32)
y=line('Qualidade, previsão temporal, alertas e cenários em um único fluxo reproduzível.',y-12,24,'#55DFBF')
line('100% DADOS SINTÉTICOS. SEM VÍNCULO COM BANCOS REAIS.',175,17,'#FFB768');finish()

y=page(2,'O problema operacional','01 / Contexto')
for s in ['Picos de falha reduzem operações concluídas.','Custos por tentativa podem comprimir a margem.','Uma queda de volume pode exigir investigação antes de qualquer decisão.']:
    y=line(s,y-14,27)
line('O painel torna os desvios visíveis e mostra a referência de cada alerta.',y-12,23,'#55DFBF');finish()

y=page(3,'Dados e contrato primeiro','02 / Base sintética')
for s in ['540 agregados: 180 dias por produto, em três produtos fictícios.','Tentativas, falhas, tarifa e custo em centavos.','Seed 42, calendário fixo e SHA-256 para reproduzir.','12 cenários injetados, com rótulos separados do detector.']:
    y=line(s,y-10,23)
line('Sem dados de clientes, crédito ou fraude real. Resultado operacional é simplificado.',y-8,20,'#FFB768');finish()

y=page(4,'Pipeline verificável','03 / Arquitetura')
for a,b in [('01  Qualidade','Validação de tipos, chaves, datas e domínios.'),('02  SQL e análise','Operações concluídas, receita, custo e margem.'),('03  Detecção','Mediana e MAD das 28 observações anteriores.'),('04  Previsão','Baseline semanal e Ridge em testes temporais.'),('05  Simulação','Hipóteses editáveis de tarifa, falhas, custo e volume.')]:
    y=line(a,y,22,'#55DFBF');y=line(b,y+9,18)
finish()

y=page(5,'Previsão sem olhar o futuro','04 / Avaliação')
y=line('Treino expansivo: 84, 112 e 140 dias. Cada origem prevê os 28 dias seguintes recursivamente.',y,24)
y=line('252 previsões avaliadas por modelo.',y-9,30,'#55DFBF')
y=line('WAPE: 7,79% no baseline sazonal; 6,45% no Ridge temporal.',y-8,25)
y=line('O Ridge perdeu para o baseline em duas janelas de Cartões. A comparação por produto está no painel.',y-8,21)
line('Os intervalos vêm de 14 erros anteriores; não garantem cobertura futura.',y-8,19,'#FFB768');finish()

y=page(6,'Alertas com evidência','05 / Investigação')
y=line(f'{report["true_positives"]} / {report["injected"]} cenários fortes detectados',y,45,'#55DFBF')
y=line(f'{report["false_positives"]} falsos positivos e {report["false_negatives"]} falsos negativos em {report["evaluated_rows"]} agregados após aquecimento.',y-10,24)
y=line('Exemplo fictício: falhas de 25% em Transferências contra mediana anterior próxima de 1%.',y-6,22)
line('Desvio sinaliza investigação; não comprova causa nem detecta fraude validada.',y-6,20,'#FFB768');finish()

y=page(7,'Simulador com premissas','06 / Demonstração')
y=line('A previsão Ridge de 14 dias define o volume de referência.',y,24)
y=line('O usuário altera tarifa, falhas, custo e uma hipótese de variação do volume.',y-7,25)
y=line('A interface recalcula receita, resultado operacional, margem e diferença para a referência.',y-7,24)
line('Não há elasticidade estimada: mudar tarifa não muda automaticamente a demanda.',y-9,20,'#FFB768');finish()

y=page(8,'Explore, reproduza e critique','07 / Limites')
y=line('O painel público usa somente dados fictícios. Não é homologação bancária, produto de crédito ou recomendação de tarifa.',y,23)
y=line('Reproduza: python radar.py<br/>Teste: python -m unittest discover -s tests -v<br/>e node tests/test_scenario.js',y-7,19,'#55DFBF')
y=line('Código, dados, testes e documentação:',y-7,21)
y=line('github.com/carlos1818augusto/<br/>radar-de-margem',y-4,20,'#55DFBF')
line('Vídeo de navegação e PDF no diretório docs/ quando o acesso ao painel estiver liberado.',y-7,18)
c.save()
print(out)
