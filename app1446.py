import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import numpy as np
import plotly.express as px

# ---------------------- إعدادات الصفحة ----------------------
st.set_page_config(
    page_title="لوحة تحليل أداء الطلاب",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- أنماط CSS ----------------------
st.markdown("""
<style>
    .stMetric {text-align: center;}
    .st-b7 {font-size: 16px !important;}
    .reportview-container .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    @media screen and (max-width: 768px) {
        .stSelectbox, .stRadio, .stSlider {width: 100% !important;}
    }
    .reportview-container {
        background-color: #FFFFFF;
        color: #000000;
    }
    .sidebar .sidebar-content {
        background-color: #F5F5F5;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #007BFF;
    }
    .stButton > button {
        background-color: #007BFF;
        color: white;
    }
    .stSelectbox > div > div {
        background-color: #E9ECEF;
        color: black;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------- تحميل البيانات ----------------------
@st.cache_data(ttl=86400)
def load_data():
    """تحميل البيانات من Google Sheets"""
    try:
        SHEET_ID = "1oEMEBkpqFQth_D4skuBY2lAHznSLeim6"
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return pd.read_excel(BytesIO(response.content))
    except Exception as e:
        st.error(f"حدث خطأ أثناء تحميل البيانات: {e}")
        return None

# ---------------------- واجهة المستخدم ----------------------
st.markdown("""
    <div style='text-align: center; font-size: 36px; font-weight: bold; color: darkgreen;'>
        لوحة تحليل أداء الطلاب
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div style='text-align: center; font-size: 20px; color: #333333;'>
        تحليل بيانات نتائج اختبارات الطلاب للعام الدراسي 1445هـ / 1446هـ للمرحلتين الابتدائية والمتوسطة
    </div>
""", unsafe_allow_html=True)

# رفع ملف Excel
uploaded_file = st.file_uploader("رفع ملف إكسل", type=["xlsx"])
data = None

if uploaded_file is not None:
    try:
        data = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"خطأ في قراءة الملف: {e}")
        st.stop()
else:
    data = load_data()

if data is not None:
    # تنظيف أسماء الأعمدة
    data.columns = data.columns.str.strip()
    
    # حذف البيانات الناقصة
    data = data.dropna(subset=['اسم الطالب', 'الصف'])
    
    # تحديد أعمدة المواد
    exclude_cols = [
        'الفصل الدراسي', 'اسم المدرسة', 'الجنس', 'اسم الطالب', 'الصف', 
        'السلوك', 'المواظبة', 'المعدل', 'المعدل_المحتسب', 'التقدير العام'
    ]
    grade_columns = [col for col in data.columns if col not in exclude_cols]
    
    if len(grade_columns) == 0:
        st.error("لم يتم العثور على أعمدة المواد!")
        st.stop()
    
    # حساب المعدل المحتسب
    data['المعدل_المحتسب'] = data[grade_columns].mean(axis=1, skipna=True)
    
    # ترتيب التقديرات
    grade_order = ["ممتاز", "جيد جداً", "جيد", "مقبول"]
    
    # ---------------------- الفلاتر الجانبية ----------------------
    st.sidebar.header("خيارات التصفية")
    
    # معالجة أسماء الفصول
    semester_list = ["كل الفصول"] + sorted(data['الفصل الدراسي'].unique().tolist())
    semester = st.sidebar.selectbox("الفصل الدراسي", semester_list)
    
    school_list = ["كل المدارس"] + sorted(data['اسم المدرسة'].unique().tolist())
    school = st.sidebar.selectbox("المدرسة", school_list)
    
    gender_list = ["كل الأجناس"] + sorted(data['الجنس'].unique().tolist())
    gender = st.sidebar.selectbox("الجنس", gender_list)
    
    grade_list = ["كل الصفوف"] + sorted(data['الصف'].unique().tolist())
    grade = st.sidebar.selectbox("الصف", grade_list)
    
    subject_list = ["كل المواد"] + grade_columns
    subject = st.sidebar.selectbox("المادة", subject_list)
    
    # ---------------------- تطبيق الفلاتر ----------------------
    filtered_data = data.copy()
    if semester != "كل الفصول":
        filtered_data = filtered_data[filtered_data['الفصل الدراسي'] == semester]
    if school != "كل المدارس":
        filtered_data = filtered_data[filtered_data['اسم المدرسة'] == school]
    if gender != "كل الأجناس":
        filtered_data = filtered_data[filtered_data['الجنس'] == gender]
    if grade != "كل الصفوف":
        filtered_data = filtered_data[filtered_data['الصف'] == grade]
    if subject != "كل المواد":
        filtered_data = filtered_data[filtered_data[subject].notna()]
    
    # ---------------------- عرض عدد الطلاب ----------------------
    st.markdown(f"""
        <div style='text-align: center; font-size: 24px; font-weight: bold; color: #007BFF;'>
            عدد الطلاب المصفى: {filtered_data['اسم الطالب'].nunique()}
        </div>
    """, unsafe_allow_html=True)
    
    if not filtered_data.empty:
        # ---------------------- متوسط المواد ----------------------
        st.subheader("📈 متوسط الدرجات حسب المادة")
        if semester == "كل الفصول":
            melted_data = filtered_data.melt(
                id_vars=['الفصل الدراسي'],
                value_vars=grade_columns,
                var_name='المادة',
                value_name='الدرجة'
            )
            avg_scores = melted_data.groupby(['الفصل الدراسي', 'المادة'])['الدرجة'].mean().reset_index()
            
            fig = px.bar(
                avg_scores,
                x='المادة',
                y='الدرجة',
                color='الفصل الدراسي',
                barmode='group',
                title="متوسط الدرجات لكل مادة (حسب الفصل)",
                labels={'الدرجة': 'المتوسط', 'المادة': ''},
                text_auto='.2f'
            )
        else:
            avg_scores = filtered_data[grade_columns].mean().reset_index()
            avg_scores.columns = ['المادة', 'الدرجة']
            
            fig = px.bar(
                avg_scores,
                x='المادة',
                y='الدرجة',
                title="متوسط الدرجات لكل مادة",
                labels={'الدرجة': 'المتوسط', 'المادة': ''},
                text_auto='.2f'
            )
        st.plotly_chart(fig, use_container_width=True)
        
        # ---------------------- مؤشرات الفصول ----------------------
        st.markdown("---")
        st.subheader("📊 المؤشرات العامة للفصول")
        
        # حساب المتوسطات
        semester_avg = filtered_data.groupby('الفصل الدراسي')['المعدل_المحتسب'].mean().reset_index()
        
        # إنشاء أعمدة
        col1, col2, col3 = st.columns(3)
        
        # الفصول المتاحة
        semesters_in_data = semester_avg['الفصل الدراسي'].tolist()
        
        # عرض المؤشرات
        semester_names = {
            'الفصل الأول': 'إشعار بدرجات الفصل الدراسي الأول',
            'الفصل الثاني': 'إشعار بدرجات الفصل الدراسي الثاني',
            'الفصل الثالث': 'إشعار بدرجات الفصل الدراسي الثالث'
        }
        
        for sem_key, sem_full in semester_names.items():
            if sem_full in semesters_in_data:
                avg_value = semester_avg[semester_avg['الفصل الدراسي'] == sem_full]['المعدل_المحتسب'].values[0]
            else:
                avg_value = None
        
        with col1:
            if sem_names['الفصل الأول'] in semesters_in_data:
                st.metric("متوسط الفصل الأول", f"{avg_value:.2f}%")
            else:
                st.metric("متوسط الفصل الأول", "N/A")
        
        with col2:
            if sem_names['الفصل الثاني'] in semesters_in_data:
                st.metric("متوسط الفصل الثاني", f"{avg_value:.2f}%")
            else:
                st.metric("متوسط الفصل الثاني", "N/A")
        
        with col3:
            if sem_names['الفصل الثالث'] in semesters_in_data:
                st.metric("متوسط الفصل الثالث", f"{avg_value:.2f}%")
            else:
                st.metric("متوسط الفصل الثالث", "N/A")

        # ---------------------- باقي الأجزاء ----------------------
        # ... (أضف هنا الأكواد الخاصة بالرسوم البيانية الأخرى كالمخططات الدائرية والمقارنات) ...
        
else:
    st.warning("لم يتم تحميل أي بيانات!")

        # توزيع الطلاب حسب التقديرات لكل فصل دراسي
   st.subheader("توزيع الطلاب حسب التقديرات لكل فصل دراسي")
        semesters = filtered_data["الفصل الدراسي"].dropna().unique()
        for sem in semesters:
            semester_data = filtered_data[filtered_data["الفصل الدراسي"] == sem]
            grade_distribution = semester_data['التقدير العام'].value_counts().reindex(grade_order, fill_value=0).reset_index()
            grade_distribution.columns = ['التقدير', 'عدد الطلاب']

            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(
                    grade_distribution,
                    values='عدد الطلاب',
                    names='التقدير',
                    title=f"توزيع الطلاب حسب التقديرات في {sem}",
                    hole=0.3
                )
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.bar(
                    grade_distribution,
                    x='التقدير',
                    y='عدد الطلاب',
                    labels={'التقدير': 'التقدير', 'عدد الطلاب': 'عدد الطلاب'},
                    title=f"توزيع الطلاب حسب التقديرات في {sem}"
                )
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        # مقارنة بين الفصول الدراسية
        st.subheader("مقارنة بين الفصول الدراسية")
        overall_grade_distribution = filtered_data.groupby('الفصل الدراسي')['التقدير العام'].value_counts().unstack(fill_value=0)
        overall_grade_distribution = overall_grade_distribution.reindex(columns=grade_order, fill_value=0)
        melted_data = overall_grade_distribution.reset_index().melt(id_vars='الفصل الدراسي', var_name='التقدير', value_name='عدد الطلاب')

        fig = px.bar(
            melted_data,
            x='الفصل الدراسي',
            y='عدد الطلاب',
            color='التقدير',
            barmode='group',
            title="مقارنة توزيع التقديرات بين الفصول الدراسية",
            labels={'عدد الطلاب': 'عدد الطلاب', 'التقدير': 'التقدير'}
        )
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # تحليل أداء مادة محددة
        if subject != "كل المواد":
            st.subheader(f"تحليل أداء الطلاب في {subject}")
            subject_performance = filtered_data[[subject, 'التقدير العام']].dropna()
            fig = px.histogram(
                subject_performance,
                x=subject,
                nbins=20,
                title=f"توزيع درجات الطلاب في {subject}",
                labels={subject: 'الدرجة', 'count': 'عدد الطلاب'}
            )
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        # مؤشر متوسط المعدل للمدارس - نسخة مطورة
        st.subheader("تحليل أداء المدارس حسب متوسط المعدل")
        avg_school_rates = filtered_data.groupby('اسم المدرسة')['المعدل_المحتسب'].agg(['mean', 'count']).reset_index()
        avg_school_rates.columns = ['اسم المدرسة', 'متوسط المعدل', 'عدد الطلاب']
        avg_school_rates = avg_school_rates[avg_school_rates['عدد الطلاب'] >= 5]

        tab1, tab2 = st.tabs(["أفضل 20 مدرسة", "أقل 20 مدرسة"])
        with tab1:
            top_schools = avg_school_rates.sort_values(by='متوسط المعدل', ascending=False).head(20)
            top_schools['الترتيب'] = range(1, len(top_schools)+1)
            st.markdown("### أفضل 20 مدرسة حسب متوسط المعدل (تنازلياً)")
            st.dataframe(
                top_schools[['الترتيب', 'اسم المدرسة', 'متوسط المعدل', 'عدد الطلاب']].style
                    .format({'متوسط المعدل': '{:.2f}'})
                    .background_gradient(cmap='Blues', subset=['متوسط المعدل'])
                    .set_properties(**{'text-align': 'right', 'direction': 'rtl'}),
                height=600
            )
            fig_top = px.bar(
                top_schools,
                x='متوسط المعدل',
                y='اسم المدرسة',
                orientation='h',
                title="أفضل 20 مدرسة حسب متوسط المعدل",
                labels={'متوسط المعدل': 'متوسط المعدل', 'اسم المدرسة': ''},
                color='متوسط المعدل',
                color_continuous_scale='Blues',
                text='متوسط المعدل',
                hover_data=['عدد الطلاب']
            )
            fig_top.update_traces(texttemplate='%{text:.2f}', textposition='inside')
            fig_top.update_layout(yaxis={'categoryorder': 'total ascending'}, template="plotly_white")
            st.plotly_chart(fig_top, use_container_width=True)
            
        with tab2:
            bottom_schools = avg_school_rates.sort_values(by='متوسط المعدل', ascending=True).head(20)
            bottom_schools['الترتيب'] = range(1, len(bottom_schools)+1)
            st.markdown("### أقل 20 مدرسة حسب متوسط المعدل (تصاعدياً)")
            st.dataframe(
                bottom_schools[['الترتيب', 'اسم المدرسة', 'متوسط المعدل', 'عدد الطلاب']].style
                    .format({'متوسط المعدل': '{:.2f}'})
                    .background_gradient(cmap='Reds_r', subset=['متوسط المعدل'])
                    .set_properties(**{'text-align': 'right', 'direction': 'rtl'}),
                height=600
            )
            fig_bottom = px.bar(
                bottom_schools,
                x='متوسط المعدل',
                y='اسم المدرسة',
                orientation='h',
                title="أقل 20 مدرسة حسب متوسط المعدل",
                labels={'متوسط المعدل': 'متوسط المعدل', 'اسم المدرسة': ''},
                color='متوسط المعدل',
                color_continuous_scale='Reds',
                text='متوسط المعدل',
                hover_data=['عدد الطلاب']
            )
            fig_bottom.update_traces(texttemplate='%{text:.2f}', textposition='inside')
            fig_bottom.update_layout(yaxis={'categoryorder': 'total descending'}, template="plotly_white")
            st.plotly_chart(fig_bottom, use_container_width=True)

        # المؤشرات العامة (تم نقلها إلى هنا لتصبح مستقلة عن التبويبات)
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
                
        with col1:
            st.metric("أعلى معدل مدرسة", f"{top_schools.iloc[0]['متوسط المعدل']:.2f}%", 
                      delta=f"فرق {top_schools.iloc[0]['متوسط المعدل'] - avg_school_rates['متوسط المعدل'].mean():.2f}% عن المتوسط العام")
            
        with col2:
            st.metric("أدنى معدل مدرسة", f"{bottom_schools.iloc[0]['متوسط المعدل']:.2f}%", 
                      delta=f"فرق {bottom_schools.iloc[0]['متوسط المعدل'] - avg_school_rates['متوسط المعدل'].mean():.2f}% عن المتوسط العام",
                      delta_color="inverse")
            
        with col3:
            st.metric("المتوسط العام للمدارس", f"{avg_school_rates['متوسط المعدل'].mean():.2f}%")
        else:
            st.warning("⚠️ لم يتم تحميل أي بيانات! الرجاء رفع ملف Excel أو التحقق من اتصال الإنترنت")
