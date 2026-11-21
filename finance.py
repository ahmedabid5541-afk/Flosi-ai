import pandas as pd

REQUIRED = ['التاريخ','نوع العملية','الفئة','المبلغ (ر.ق)','الوصف']

def validate(df):
    missing = set(REQUIRED)-set(df.columns)
    if missing: raise ValueError('أعمدة ناقصة: '+', '.join(sorted(missing)))
    out=df.copy()
    out['المبلغ (ر.ق)']=pd.to_numeric(out['المبلغ (ر.ق)'],errors='coerce')
    if out['المبلغ (ر.ق)'].isna().any() or (out['المبلغ (ر.ق)']<0).any():
        raise ValueError('يجب أن تكون المبالغ أرقاماً غير سالبة')
    if not out['نوع العملية'].isin(['دخل','مصروف']).all():
        raise ValueError('نوع العملية يجب أن يكون دخل أو مصروف')
    dates=pd.to_datetime(out['التاريخ'],format='%Y-%m-%d',errors='coerce')
    if dates.isna().any(): raise ValueError('صيغة التاريخ المطلوبة YYYY-MM-DD')
    return out

def summary(df):
    df=validate(df)
    inc=float(df.loc[df['نوع العملية']=='دخل','المبلغ (ر.ق)'].sum())
    exp=float(df.loc[df['نوع العملية']=='مصروف','المبلغ (ر.ق)'].sum())
    return {'income':inc,'expense':exp,'balance':inc-exp,'saving_rate':round((inc-exp)/inc*100,1) if inc else 0}

def budget(df,limit):
    s=summary(df)
    return {'limit':float(limit),'spent':s['expense'],'remaining':float(limit)-s['expense']}

def savings_plan(goal,months,current=0):
    if months<=0 or goal<0 or current<0: raise ValueError('تحقق من الهدف والمدة والادخار الحالي')
    return round(max(0,goal-current)/months,2)

def guidance(df,monthly_budget):
    s=summary(df); b=budget(df,monthly_budget)
    if s['income']==0: return 'أدخل دخلاً شهرياً لتقييم قدرتك على الادخار.'
    if s['balance']<0: return 'مصروفاتك تتجاوز دخلك. راجع البنود غير الأساسية وحدد سقفاً لها.'
    if b['remaining']<0: return 'تجاوزت الميزانية المحددة. راجع أعلى فئات الإنفاق وخفّض المصروفات الاختيارية.'
    return 'أنت ضمن الميزانية الحالية. خصص جزءاً من الفائض لهدف ادخار واضح.'
