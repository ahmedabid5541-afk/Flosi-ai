import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from datetime import date
from finance import validate,summary,budget,savings_plan,guidance

st.set_page_config(page_title='فلوسي AI',page_icon='💰',layout='wide')
st.markdown('''<style>html,body,[class*="css"]{font-family:Tahoma,Arial,sans-serif} .block-container{direction:rtl;text-align:right} h1,h2,h3,p{direction:rtl;text-align:right}</style>''',unsafe_allow_html=True)
st.title('💰 فلوسي AI | Flosi AI')
st.caption('مشروع أحمد طه | جامعة قطر | تخصص المالية — نموذج تعليمي ببيانات افتراضية')
base=Path(__file__).parent
if 'df' not in st.session_state:
    st.session_state.df=pd.read_csv(base/'Flosi_AI_Clean_Data.csv',encoding='utf-8-sig')

with st.sidebar:
    st.header('الإعدادات')
    uploaded=st.file_uploader('استيراد بيانات CSV',type=['csv'])
    if uploaded is not None:
        try:
            incoming=validate(pd.read_csv(uploaded,encoding='utf-8-sig'))
            st.session_state.df=incoming
            st.success('تم تحميل البيانات')
        except Exception as e: st.error(str(e))
    if st.button('إعادة تعيين البيانات التجريبية'):
        st.session_state.df=pd.read_csv(base/'Flosi_AI_Clean_Data.csv',encoding='utf-8-sig')
        st.rerun()

df=st.session_state.df
try: s=summary(df)
except Exception as e:
    st.error(str(e)); st.stop()

tabs=st.tabs(['📊 لوحة التحكم','➕ إضافة عملية','📋 الميزانية','🎯 الادخار','💬 المساعد المالي','📁 البيانات'])
with tabs[0]:
    a,b,c,d=st.columns(4)
    a.metric('الدخل',f"{s['income']:,.0f} ر.ق")
    b.metric('المصروفات',f"{s['expense']:,.0f} ر.ق")
    c.metric('المتبقي',f"{s['balance']:,.0f} ر.ق")
    d.metric('نسبة الفائض',f"{s['saving_rate']}%")
    costs=df[df['نوع العملية']=='مصروف'].groupby('الفئة',as_index=False)['المبلغ (ر.ق)'].sum()
    if not costs.empty:
        st.plotly_chart(px.pie(costs,names='الفئة',values='المبلغ (ر.ق)',title='توزيع المصروفات'),use_container_width=True)
        st.plotly_chart(px.bar(costs,x='الفئة',y='المبلغ (ر.ق)',title='المصروفات حسب الفئة'),use_container_width=True)
with tabs[1]:
    with st.form('new_entry'):
        dt=st.date_input('التاريخ',date.today())
        kind=st.selectbox('نوع العملية',['مصروف','دخل'])
        category=st.selectbox('الفئة',['طعام','مواصلات','دراسة','ترفيه','تسوق','اتصالات','مكافأة جامعية','عمل جزئي','أخرى'])
        amount=st.number_input('المبلغ بالريال القطري',min_value=0.01,step=1.0)
        note=st.text_input('الوصف')
        submitted=st.form_submit_button('إضافة العملية')
    if submitted:
        entry=pd.DataFrame([{'التاريخ':dt.isoformat(),'نوع العملية':kind,'الفئة':category,'المبلغ (ر.ق)':amount,'الوصف':note}])
        st.session_state.df=pd.concat([df,entry],ignore_index=True)
        st.success('تمت إضافة العملية'); st.rerun()
with tabs[2]:
    limit=st.number_input('حدد ميزانيتك الشهرية (ر.ق)',min_value=0.0,value=1500.0,step=100.0)
    b=budget(df,limit)
    st.metric('المتبقي من الميزانية',f"{b['remaining']:,.2f} ر.ق")
    st.progress(min(1.0,b['spent']/limit) if limit>0 else 0.0)
    st.info(guidance(df,limit))
with tabs[3]:
    goal=st.number_input('هدف الادخار (ر.ق)',min_value=0.0,value=3000.0,step=100.0)
    saved=st.number_input('المدخر حالياً (ر.ق)',min_value=0.0,value=0.0,step=100.0)
    months=st.number_input('عدد الأشهر',min_value=1,value=6,step=1)
    monthly=savings_plan(goal,months,saved)
    st.metric('المطلوب ادخاره شهرياً',f'{monthly:,.2f} ر.ق')
    if monthly>max(0,s['balance']): st.warning('المبلغ المطلوب يتجاوز الفائض الحالي. جرّب تمديد المدة أو خفض الهدف.')
with tabs[4]:
    st.write('مساعد إرشادي قائم على بياناتك وقواعد واضحة؛ لا يستخدم نموذج محادثة خارجي في هذه النسخة.')
    q=st.selectbox('اختر سؤالك',['كيف أتحكم بمصروفاتي؟','هل أنا ضمن الميزانية؟','كيف أبدأ الادخار؟'])
    limit2=st.number_input('الميزانية للمساعد',min_value=0.0,value=1500.0,key='assistant_budget')
    if q=='كيف أبدأ الادخار?': st.write('حدد هدفاً ومهلة في تبويب الادخار.')
    elif q=='كيف أبدأ الادخار؟': st.write('حدد هدفاً ومهلة في تبويب الادخار، وراجع فائض دخلك أولاً.')
    else: st.write(guidance(df,limit2))
with tabs[5]:
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.download_button('تنزيل البيانات الحالية CSV',df.to_csv(index=False).encode('utf-8-sig'),'Flosi_AI_Export.csv','text/csv')
st.caption('لأغراض تعليمية فقط، وليس نصيحة استثمارية أو مالية شخصية. لا تُدخل معلومات بنكية حساسة.')
