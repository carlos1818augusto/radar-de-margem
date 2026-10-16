"""Opcional: pip install reportlab pillow; executar na raiz do projeto."""
from pathlib import Path
import json
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
m = json.loads((ROOT/'demo/report.json').read_text())
out = ROOT/'docs/radar-margem-carrossel.pdf'
c = canvas.Canvas(str(out), pagesize=(720,900))
c.setTitle('Radar de Margem | Carlos Augusto Rodrigues Teixeira')
c.setAuthor('Carlos Augusto Rodrigues Teixeira')
def text(s,y,size=26,color='#DDE9F7',width=600):
    style=ParagraphStyle('p',fontName='Helvetica',fontSize=size,leading=size*1.35,textColor=HexColor(color))
    p=Paragraph(s,style); w,h=p.wrap(width,800); p.drawOn(c,60,y-h); return y-h-24
def page(n,title,kicker):
    c.setFillColor(HexColor('#0B1423')); c.rect(0,0,720,900,fill=1,stroke=0)
    c.setFillColor(HexColor('#55DFBF'));c.rect(60,825,60,5,fill=1,stroke=0)
    text(kicker.upper(),800,14,'#55DFBF')
    y=text(title,750,44,'#FFFFFF')
    c.setStrokeColor(HexColor('#2D4059'));c.line(60,70,660,70)
    text('CARLOS AUGUSTO RODRIGUES TEIXEIRA  /  DADOS E IA',54,10)
    c.setFont('Helvetica',11);c.drawRightString(660,38,f'{n:02} / 08')
    return y

y=page(1,'Radar de Margem','Projeto de portfólio')
y=text('Do dado sintético ao alerta que pode ser investigado.',y-25,32)
y=text('Python + SQL + estatística robusta + painel interativo',y-25,23,'#55DFBF')
text('Uma demonstração reproduzível de engenharia, análise e automação de dados. Sem APIs pagas.',y-30,23)
text('100% SINTÉTICO • SEM DADOS EMPRESARIAIS',155,15,'#FFB768');c.showPage()
y=page(2,'Faturamento sozinho não conta tudo','01 / Problema')
for s in ['Um desconto pode sustentar vendas e comprimir margem.','Um custo maior pode transformar uma venda em prejuízo bruto.','Uma queda de volume pode passar despercebida no total.']:
    y=text(s,y-12,26)
text('Objetivo: priorizar investigação com evidências, sem automatizar decisões comerciais.',y-5,22,'#55DFBF');c.showPage()
y=page(3,'Dados que permitem conferir a resposta','02 / Simulação')
for s in ['540 registros: 180 dias × 3 categorias.','Seed 42, datas fixas e hash SHA-256 da base.','12 cenários conhecidos: desconto, custo e volume.','Rótulos separados: o detector não recebe a resposta.']:
    y=text(s,y-8,25)
text('Não são dados da NEOOH nem de outra empresa. Não há impacto de negócio real medido.',y-10,21,'#FFB768');c.showPage()
y=page(4,'Uma arquitetura pequena e verificável','03 / Implementação')
for title,desc in [('01  Gerar e validar','Chaves, tipos, datas e limites de domínio.'),('02  Calcular em SQL','Receita após desconto, custo e lucro bruto.'),('03  Detectar e explicar','Mediana e MAD das 28 observações anteriores.'),('04  Entregar e avaliar','Painel offline, CSV e relatório reproduzível.')]:
    y=text(title,y,23,'#55DFBF'); y=text(desc,y+12,19)
c.showPage()
y=page(5,'O produto em execução','04 / Captura real do painel')
im=Image.open(ROOT/'docs/painel.png')
# Crop only the actual product area from its real browser screenshot.
crop=im.crop((max(0,int(im.width*.20)),0,min(im.width,int(im.width*.55)),min(im.height,960))) if im.width>2500 else im
# Derive content bounds from known screenshot dimensions, preserving screenshot pixels.
if im.width>2500:
    crop=im.crop((690,20,1870,min(im.height,930)))
iw,ih=crop.size
height=min(440,600*ih/iw)
c.drawImage(ImageReader(crop),60,y-height-10,width=600,height=height)
text('Filtros por categoria e período. Margem ponderada, alertas com referência e exportação CSV.',y-height-45,22)
c.showPage()
y=page(6,'Cada alerta mostra a comparação','05 / Explicabilidade')
y=text('Exemplo sintético: Casa, 07/03/2026',y,24,'#55DFBF')
y=text('13,1% de margem<br/>39,1% de mediana anterior',y-12,34)
y=text('Queda acima do limite de 8 pontos percentuais: investigar.',y-12,25)
y=text('Regra de margem: queda &gt; max(8 p.p., 4 × 1,4826 × MAD). Volume: abaixo de 45% da mediana anterior.',y-8,21)
text('Desvio é evidência para análise. Não é prova automática da causa.',y,20,'#FFB768');c.showPage()
y=page(7,'Resultado medido, escopo explícito','06 / Validação')
y=text(f'{m["true_positives"]} / {m["injected"]}',y-10,78,'#55DFBF')
y=text(f'anomalias detectadas em {m["evaluated_rows"]} observações avaliadas.',y,25)
y=text(f'{m["false_positives"]} falsos positivos • {m["false_negatives"]} falsos negativos',y,25)
y=text('6 testes aprovados: cálculo, contratos, repetibilidade, histórico sem futuro, aquecimento e série normal.',y,23)
text('Cenários fortes e planejados. Resultado de sanidade da simulação, não benchmark de produção.',y,21,'#FFB768');c.showPage()
y=page(8,'O próximo passo é validar fora da simulação','07 / Limitações e reprodução')
y=text('Sem sazonalidade, impostos, devoluções ou ingestão real. Limiares demonstrativos; sem holdout independente.',y,24)
y=text('Execute: python radar.py<br/>Teste: python -m unittest discover -s tests -v',y,20,'#55DFBF')
y=text('Código, dados sintéticos, documentação e painel no repositório Radar de Margem.',y,23)
y=text('github.com/carlos1818augusto/<br/>radar-de-margem',y,20,'#55DFBF')
text('Construído com assistência de IA. Resultados verificados pela execução do código.',y,19)
c.save()
print(out)
