"""Forecasting with fixed-origin recursive evaluation and train-only calibration.

Standard-library ridge regression, no hidden model services or data dependencies.
"""
import math
from datetime import date, timedelta
from statistics import mean

MODELS = ('Sazonal ingênuo (7d)', 'Ridge temporal')
ORIGINS = (84, 112, 140)
HORIZON = 28
CALIBRATION = 14

def features(history, t):
    return [1., t/180, math.sin(2*math.pi*t/7), math.cos(2*math.pi*t/7), history[t-7]/3000, mean(history[t-7:t])/3000]

def solve(matrix, vector):
    """Small dense linear system with partial pivoting (six coefficients)."""
    a = [list(row)+[b] for row,b in zip(matrix,vector)]
    n=len(a)
    for col in range(n):
        pivot=max(range(col,n),key=lambda i:abs(a[i][col]))
        a[col],a[pivot]=a[pivot],a[col]
        if abs(a[col][col])<1e-12: raise ValueError('Singular model matrix')
        scale=a[col][col]; a[col]=[v/scale for v in a[col]]
        for i in range(n):
            if i!=col:
                factor=a[i][col];a[i]=[x-factor*y for x,y in zip(a[i],a[col])]
    return [row[-1] for row in a]

def fit(history, alpha=0.1):
    if len(history)<28: raise ValueError('Need at least 28 training observations')
    x=[features(history,t) for t in range(7,len(history))]
    y=history[7:];n=len(x[0])
    matrix=[[sum(row[i]*row[j] for row in x)+(alpha if i==j and i>0 else 0) for j in range(n)] for i in range(n)]
    vector=[sum(row[i]*v for row,v in zip(x,y)) for i in range(n)]
    return solve(matrix,vector)

def predict(history, horizon, model):
    if len(history)<28 or horizon<1: raise ValueError('Invalid forecast dimensions')
    if model not in MODELS: raise ValueError('Unknown model')
    coefficients=fit(history) if model==MODELS[1] else None
    extended=list(history)
    for _ in range(horizon):
        t=len(extended)
        value=sum(a*b for a,b in zip(coefficients,features(extended,t))) if coefficients else extended[t-7]
        extended.append(max(0.,value))
    return extended[len(history):]

def interval_radius(history, model):
    """90% empirical absolute-error quantile on the preceding 14-day block.

    No future outcomes are consumed. This is not a calibrated coverage guarantee:
    the final fit differs and time-series residuals are dependent.
    """
    calibration=predict(history[:-CALIBRATION],CALIBRATION,model)
    errors=sorted(abs(a-p) for a,p in zip(history[-CALIBRATION:],calibration))
    return errors[math.ceil(.9*len(errors))-1]

def metrics(records):
    errors=[r['prediction']-r['actual'] for r in records]
    denominator=sum(r['actual'] for r in records)
    return dict(n=len(records),mae=mean(abs(e) for e in errors),wape=sum(abs(e) for e in errors)/denominator if denominator else None,bias=mean(errors),coverage=sum(r['lower']<=r['actual']<=r['upper'] for r in records)/len(records))

def series(rows):
    return {cat: sorted([r for r in rows if r['category']==cat],key=lambda r:r['date']) for cat in sorted({r['category'] for r in rows})}

def backtest(rows):
    predictions,scores=[],[]
    for cat,group in series(rows).items():
        values=[r['units'] for r in group]
        for origin in ORIGINS:
            if len(values)<origin+HORIZON: raise ValueError('Insufficient evaluation history')
            for model in MODELS:
                history=values[:origin]
                forecast=predict(history,HORIZON,model)
                radius=interval_radius(history,model)
                block=[]
                for step,value in enumerate(forecast):
                    r=dict(category=cat,model=model,origin=origin,train_end=group[origin-1]['date'],date=group[origin+step]['date'],horizon=step+1,actual=values[origin+step],prediction=value,lower=max(0.,value-radius),upper=value+radius)
                    block.append(r)
                predictions.extend(block)
                scores.append(dict(category=cat,model=model,origin=origin,**metrics(block)))
    return predictions,scores

def future_forecasts(rows,horizon=14):
    result=[]
    for cat,group in series(rows).items():
        values=[r['units'] for r in group]
        for model in MODELS:
            radius=interval_radius(values,model)
            for step,value in enumerate(predict(values,horizon,model),1):
                result.append(dict(category=cat,model=model,date=str(date.fromisoformat(group[-1]['date'])+timedelta(days=step)),horizon=step,prediction=value,lower=max(0.,value-radius),upper=value+radius))
    return result
