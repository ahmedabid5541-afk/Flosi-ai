"""Flosi AI educational assistant. Only fictional, non-sensitive data should be supplied."""
import json
from openai import OpenAI
from finance import summary, budget, savings_plan

MODEL = 'gpt-4.1-mini'

TOOLS = [
    {'type':'function','function':{'name':'financial_summary','description':'Calculate the income, expenses, balance and saving rate from the current dataset.','parameters':{'type':'object','properties':{},'additionalProperties':False}}},
    {'type':'function','function':{'name':'spending_by_category','description':'Calculate expense totals by category from the current dataset.','parameters':{'type':'object','properties':{},'additionalProperties':False}}},
    {'type':'function','function':{'name':'check_budget','description':'Compare current expenses against a proposed budget in QAR.','parameters':{'type':'object','properties':{'monthly_limit':{'type':'number','description':'Budget amount in QAR, non-negative'}},'required':['monthly_limit'],'additionalProperties':False}}},
    {'type':'function','function':{'name':'calculate_savings','description':'Calculate the monthly saving needed for a target in a number of months.','parameters':{'type':'object','properties':{'goal':{'type':'number'},'months':{'type':'integer'},'already_saved':{'type':'number'}},'required':['goal','months','already_saved'],'additionalProperties':False}}}
]

SYSTEM = '''أنت فلوسي AI، وكيل مالي تعليمي لطلاب جامعة قطر. تحدث بالعربية الواضحة وبالريال القطري. لديك أدوات حسابية، ويجب استخدامها قبل ذكر أي رقم من بيانات المستخدم، ولا تخترع بيانات. البيانات افتراضية تعليمية، وليست سجلات مصرفية. لا تطلب كلمات مرور أو أرقام حسابات أو بطاقات. لا تقدم توصيات استثمارية شخصية أو ضمانات. قدم خطوات عملية موجزة ووضح الافتراضات. لا تدعي أنك عدلت البيانات أو الميزانية؛ أنت تقترح فقط، وأي تعديل يحتاج موافقة وتنفيذًا منفصلًا. عند وجود قلق مالي أظهر تفهمًا دون مبالغة. إذا كان الطلب خارج نطاق الإدارة المالية التعليمية، وضح حدودك بلطف.'''

def _run_tool(name, args, df):
    if name == 'financial_summary':
        return summary(df)
    if name == 'spending_by_category':
        expenses = df[df['نوع العملية']=='مصروف']
        totals = expenses.groupby('الفئة')['المبلغ (ر.ق)'].sum().sort_values(ascending=False)
        return {'currency':'QAR','categories':{str(k):round(float(v),2) for k,v in totals.items()}}
    if name == 'check_budget':
        limit=float(args['monthly_limit'])
        if limit < 0 or limit > 1_000_000_000: return {'error':'الميزانية يجب أن تكون رقمًا غير سالب ومعقولًا'}
        return budget(df,limit)
    if name == 'calculate_savings':
        goal=float(args['goal']); months=int(args['months']); saved=float(args['already_saved'])
        if goal < 0 or saved < 0 or months < 1 or months > 600: return {'error':'أدخل هدفًا ومدخرات غير سالبة ومدة من 1 إلى 600 شهر'}
        required=savings_plan(goal,months,saved)
        return {'monthly_required_QAR':round(float(required),2),'current_balance_QAR':round(float(summary(df)['balance']),2),'months':months}
    return {'error':'أداة غير معروفة'}

def ask_agent(question, df, api_key, history=None):
    if not api_key: raise ValueError('مفتاح API غير موجود في Streamlit Secrets')
    if not question.strip(): raise ValueError('اكتب سؤالًا أولًا')
    client=OpenAI(api_key=api_key, timeout=25.0, max_retries=1)
    messages=[{'role':'system','content':SYSTEM}]
    for msg in (history or [])[-8:]:
        if msg.get('role') in ('user','assistant') and isinstance(msg.get('content'),str):
            messages.append({'role':msg['role'],'content':msg['content'][:2000]})
    messages.append({'role':'user','content':question[:2000]})
    for _ in range(4):
        response=client.chat.completions.create(model=MODEL,messages=messages,tools=TOOLS,tool_choice='auto',temperature=0.2,max_tokens=650)
        msg=response.choices[0].message
        if not msg.tool_calls:
            return msg.content or 'لم أتمكن من إنشاء إجابة. حاول مرة أخرى.'
        messages.append(msg.model_dump(exclude_none=True))
        for call in msg.tool_calls:
            try:
                args=json.loads(call.function.arguments or '{}')
                result=_run_tool(call.function.name,args,df)
            except Exception as exc:
                result={'error':str(exc)}
            messages.append({'role':'tool','tool_call_id':call.id,'content':json.dumps(result,ensure_ascii=False,default=str)})
    return 'تعذّر إكمال التحليل في عدد الخطوات المسموح. جرّب سؤالًا أكثر تحديدًا.'
