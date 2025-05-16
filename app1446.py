import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import numpy as np
import plotly.express as px
from PIL import Image
import urllib.request
import gdown

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
    .logo-container {
        text-align: center;
        padding: 15px 0;
        border-bottom: 1px solid #eee;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------- تحميل اللوجو من Google Drive ----------------------
@st.cache_data
def load_logo():
    try:
        # رابط Google Drive
        file_id = "1R0a1QTX-foStGKqWuX-NtX2FkgVQaFio"
        url = f"https://drive.google.com/uc?id={file_id}"
        
        # تحميل الصورة باستخدام gdown
        output = "logo_from_drive.png"
        gdown.download(url, output, quiet=False)
        
        logo = Image.open(output)
        return logo
    except Exception as e:
        st.sidebar.error(f"حدث خطأ أثناء تحميل اللوجو: {e}")
        return None

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
        لوحة تحليل أداء الطلبة
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div style='text-align: center; font-size: 20px; color: #333333;'>
        تحليل بيانات نتائج اختبارات الطلبة للعام الدراسي 1445هـ / 1446هـ للمرحلتين الابتدائية والمتوسطة
    </div>
""", unsafe_allow_html=True)

# تحميل اللوجو وعرضه في الجانب الأيسر
logo = load_logo()
if logo is not None:
    st.sidebar.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.sidebar.image(logo, width=200, use_container_width=True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

# تحميل البيانات
data = load_data()

if data is not None:
    # تنظيف أسماء الأعمدة من الفراغات
    data.columns = data.columns.str.strip()

    # فقط حذف الصفوف التي تفتقد اسم الطالب أو الصف
    data = data.dropna(subset=['اسم الطالب', 'الصف'])

    # استخراج أعمدة المواد تلقائيًا (كل الأعمدة ما عدا الأساسية)
    exclude_cols = [
        'الفصل الدراسي', 'اسم المدرسة', 'الجنس', 'اسم الطالب', 'الصف', 
        'السلوك', 'المواظبة', 'المعدل', 'المعدل_المحتسب', 'التقدير العام'
    ]
    grade_columns = [col for col in data.columns if col not in exclude_cols]
    if len(grade_columns) == 0:
        st.error("لم يتم العثور على أعمدة المواد. يرجى التأكد من صحة الملف.")
        st.stop()

    # احتساب المعدل بتجاهل القيم الفارغة
    data['المعدل_المحتسب'] = data[grade_columns].mean(axis=1, skipna=True)

    # تعريف الترتيب المخصص للتقديرات
    grade_order = ["ممتاز", "جيد جداً", "جيد", "مقبول"]

    # ---------------------- خيارات التصفية ----------------------
    st.sidebar.header("خيارات التصفية")
    semester = st.sidebar.selectbox("اختر الفصل الدراسي", ["كل الفصول"] + sorted(list(data["الفصل الدراسي"].dropna().unique())))
    school = st.sidebar.selectbox("اختر المدرسة", ["كل المدارس"] + sorted(list(data["اسم المدرسة"].dropna().unique())))
    gender = st.sidebar.selectbox("اختر الجنس", ["كل الأجناس"] + sorted(list(data["الجنس"].dropna().unique())))
    grade = st.sidebar.selectbox("اختر الصف", ["كل الصفوف"] + sorted(list(data["الصف"].dropna().unique())))
    subject = st.sidebar.selectbox("اختر المادة", ["كل المواد"] + grade_columns)

    # ---------------------- تطبيق التصفية ----------------------
    filtered_data = data.copy()
    if semester != "كل الفصول":
        filtered_data = filtered_data[filtered_data["الفصل الدراسي"] == semester]
    if school != "كل المدارس":
        filtered_data = filtered_data[filtered_data["اسم المدرسة"] == school]
    if gender != "كل الأجناس":
        filtered_data = filtered_data[filtered_data["الجنس"] == gender]
    if grade != "كل الصفوف":
        filtered_data = filtered_data[filtered_data["الصف"] == grade]
    if subject != "كل المواد":
        filtered_data = filtered_data[filtered_data[subject].notna()]

    # ---------------------- عرض عدد الطلبة بعد التصفية ----------------------
    st.markdown(f"""
        <div style='text-align: center; font-size: 24px; font-weight: bold; color: #007BFF;'>
            عدد الطلبة بعد التصفية: {filtered_data['اسم الطالب'].nunique()}
        </div>
    """, unsafe_allow_html=True)

    if not filtered_data.empty:
        # متوسط نتائج الطلبة لكل مادة (مقسمة حسب الفصل إذا تم اختيار كل الفصول)
        st.subheader("متوسط نتائج الطلبة لكل مادة")
        if semester == "كل الفصول":
            avg_subject_scores = filtered_data.melt(
                id_vars=['الفصل الدراسي'],
                value_vars=grade_columns,
                var_name='المادة',
                value_name='الدرجة'
            ).groupby(['الفصل الدراسي', 'المادة'])['الدرجة'].mean().reset_index()

            fig = px.bar(
                avg_subject_scores,
                x='المادة',
                y='الدرجة',
                color='الفصل الدراسي',
                barmode='group',
                title="متوسط نتائج الطلبة لكل مادة (مقسمة حسب الفصل)",
                labels={'الدرجة': 'متوسط الدرجة', 'المادة': 'المادة'},
                text='الدرجة',
                template="plotly_white"
            )
            fig.update_traces(texttemplate='%{text:.2f}', textposition='inside', marker=dict(line=dict(color='white', width=1)))
        else:
            avg_subject_scores = filtered_data[grade_columns].mean().reset_index()
            avg_subject_scores.columns = ['المادة', 'الدرجة']

            fig = px.bar(
                avg_subject_scores,
                x='المادة',
                y='الدرجة',
                title="متوسط نتائج الطلبة لكل مادة",
                labels={'الدرجة': 'متوسط الدرجة', 'المادة': 'المادة'},
                template="plotly_white"
            )

        st.plotly_chart(fig, use_container_width=True)

        # توزيع الطلبة حسب التقديرات لكل فصل دراسي
        st.subheader("توزيع الطلبة حسب التقديرات لكل فصل دراسي")
        semesters = filtered_data["الفصل الدراسي"].dropna().unique()
        for sem in semesters:
            semester_data = filtered_data[filtered_data["الفصل الدراسي"] == sem]
            grade_distribution = semester_data['التقدير العام'].value_counts().reindex(grade_order, fill_value=0).reset_index()
            grade_distribution.columns = ['التقدير', 'عدد الطلبة']

            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(
                    grade_distribution,
                    values='عدد الطلبة',
                    names='التقدير',
                    title=f"توزيع الطلبة حسب التقديرات في {sem}",
                    hole=0.3
                )
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.bar(
                    grade_distribution,
                    x='التقدير',
                    y='عدد الطلبة',
                    labels={'التقدير': 'التقدير', 'عدد الطلبة': 'عدد الطلبة'},
                    title=f"توزيع الطلبة حسب التقديرات في {sem}"
                )
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        # مقارنة بين الفصول الدراسية
        st.subheader("مقارنة بين الفصول الدراسية")
        overall_grade_distribution = filtered_data.groupby('الفصل الدراسي')['التقدير العام'].value_counts().unstack(fill_value=0)
        overall_grade_distribution = overall_grade_distribution.reindex(columns=grade_order, fill_value=0)
        melted_data = overall_grade_distribution.reset_index().melt(id_vars='الفصل الدراسي', var_name='التقدير', value_name='عدد الطلبة')

        fig = px.bar(
            melted_data,
            x='الفصل الدراسي',
            y='عدد الطلبة',
            color='التقدير',
            barmode='group',
            title="مقارنة توزيع التقديرات بين الفصول الدراسية",
            labels={'عدد الطلبة': 'عدد الطلبة', 'التقدير': 'التقدير'}
        )
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

        # تحليل أداء مادة محددة
        if subject != "كل المواد":
            st.subheader(f"تحليل أداء الطلبة في {subject}")
            subject_performance = filtered_data[[subject, 'التقدير العام']].dropna()
            fig = px.histogram(
                subject_performance,
                x=subject,
                nbins=20,
                title=f"توزيع درجات الطلبة في {subject}",
                labels={subject: 'الدرجة', 'count': 'عدد الطلبة'}
            )
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        # مؤشر متوسط المعدل للمدارس - نسخة مطورة
        st.subheader("تحليل أداء المدارس حسب متوسط المعدل")
        avg_school_rates = filtered_data.groupby('اسم المدرسة')['المعدل_المحتسب'].agg(['mean', 'count']).reset_index()
        avg_school_rates.columns = ['اسم المدرسة', 'متوسط المعدل', 'عدد الطلبة']
        avg_school_rates = avg_school_rates[avg_school_rates['عدد الطلبة'] >= 5]

        tab1, tab2 = st.tabs(["أفضل 20 مدرسة", "أقل 20 مدرسة"])
        with tab1:
            top_schools = avg_school_rates.sort_values(by='متوسط المعدل', ascending=False).head(20)
            top_schools['الترتيب'] = range(1, len(top_schools)+1)
            st.markdown("### أفضل 20 مدرسة حسب متوسط المعدل (تنازلياً)")
            st.dataframe(
                top_schools[['الترتيب', 'اسم المدرسة', 'متوسط المعدل', 'عدد الطلبة']].style
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
                hover_data=['عدد الطلبة']
            )
            fig_top.update_traces(texttemplate='%{text:.2f}', textposition='inside')
            fig_top.update_layout(yaxis={'categoryorder': 'total ascending'}, template="plotly_white")
            st.plotly_chart(fig_top, use_container_width=True)
            
        with tab2:
            bottom_schools = avg_school_rates.sort_values(by='متوسط المعدل', ascending=True).head(20)
            bottom_schools['الترتيب'] = range(1, len(bottom_schools)+1)
            st.markdown("### أقل 20 مدرسة حسب متوسط المعدل (تصاعدياً)")
            st.dataframe(
                bottom_schools[['الترتيب', 'اسم المدرسة', 'متوسط المعدل', 'عدد الطلبة']].style
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
                hover_data=['عدد الطلبة']
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
