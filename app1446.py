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
    # تنظيف أسماء الأعمدة من الفراغات
    data.columns = data.columns.str.strip()

    # حذف الصفوف التي تفتقد بيانات أساسية
    data = data.dropna(subset=['اسم الطالب', 'الصف'])

    # استخراج أعمدة المواد تلقائيًا
    exclude_cols = [
        'الفصل الدراسي', 'اسم المدرسة', 'الجنس', 'اسم الطالب', 'الصف', 
        'السلوك', 'مواظبة', 'المعدل', 'المعدل_المحتسب', 'التقدير العام'
    ]
    grade_columns = [col for col in data.columns if col not in exclude_cols]
    if len(grade_columns) == 0:
        st.error("لم يتم العثور على أعمدة المواد. يرجى التأكد من صحة الملف.")
        st.stop()

    # احتساب المعدل
    data['المعدل_المحتسب'] = data[grade_columns].mean(axis=1, skipna=True)

    # تعريف ترتيب التقديرات
    grade_order = ["ممتاز", "جيد جداً", "جيد", "مقبول"]

    # ---------------------- خيارات التصفية ----------------------
    st.sidebar.header("خيارات التصفية")
    
    # معالجة تسميات الفصول الدراسية
    semester_options = ["كل الفصول"] + sorted(data["الفصل الدراسي"].dropna().unique().tolist())
    semester = st.sidebar.selectbox("اختر الفصل الدراسي", semester_options)
    
    school = st.sidebar.selectbox("اختر المدرسة", ["كل المدارس"] + sorted(data["اسم المدرسة"].dropna().unique()))
    gender = st.sidebar.selectbox("اختر الجنس", ["كل الأجناس"] + sorted(data["الجنس"].dropna().unique()))
    grade = st.sidebar.selectbox("اختر الصف", ["كل الصفوف"] + sorted(data["الصف"].dropna().unique()))
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

    # ---------------------- عرض عدد الطلاب ----------------------
    st.markdown(f"""
        <div style='text-align: center; font-size: 24px; font-weight: bold; color: #007BFF;'>
            عدد الطلاب بعد التصفية: {filtered_data['اسم الطالب'].nunique()}
        </div>
    """, unsafe_allow_html=True)

    if not filtered_data.empty:
        # ---------------------- متوسط النتائج لكل مادة ----------------------
        st.subheader("متوسط نتائج الطلاب لكل مادة")
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
                title="متوسط نتائج الطلاب لكل مادة (مقسمة حسب الفصل)",
                labels={'الدرجة': 'متوسط الدرجة', 'المادة': 'المادة'},
                text='الدرجة',
                template="plotly_white"
            )
            fig.update_traces(texttemplate='%{text:.2f}', textposition='inside')
        else:
            avg_subject_scores = filtered_data[grade_columns].mean().reset_index()
            avg_subject_scores.columns = ['المادة', 'الدرجة']

            fig = px.bar(
                avg_subject_scores,
                x='المادة',
                y='الدرجة',
                title="متوسط نتائج الطلاب لكل مادة",
                labels={'الدرجة': 'متوسط الدرجة', 'المادة': 'المادة'},
                template="plotly_white"
            )
        st.plotly_chart(fig, use_container_width=True)

        # ---------------------- مؤشرات الفصول الدراسية ----------------------
        st.markdown("---")
        st.subheader("المتوسط العام للفصول الدراسية")
        
        # حساب المتوسطات
        semester_avg = filtered_data.groupby('الفصل الدراسي')['المعدل_المحتسب'].mean().reset_index()
        
        # إنشاء أعمدة للمؤشرات
        cols = st.columns(3)
        semesters_in_data = semester_avg['الفصل الدراسي'].tolist()
        
        # عرض المؤشرات حسب التسميات الفعلية
        for idx, sem in enumerate(["إشعار بدرجات الفصل الدراسي الأول", 
                                  "إشعار بدرجات الفصل الدراسي الثاني",
                                  "إشعار بدرجات الفصل الدراسي الثالث"]):
            with cols[idx]:
                if sem in semesters_in_data:
                    avg = semester_avg[semester_avg['الفصل الدراسي'] == sem]['المعدل_المحتسب'].values[0]
                    st.metric(f"متوسط {sem.split('الفصل الدراسي ')[1]}", f"{avg:.2f}%")
                else:
                    st.metric(f"متوسط {sem.split('الفصل الدراسي ')[1]}", "غير متوفر")

        # ---------------------- باقي الأقسام (التوزيعات والمقارنات) ----------------------
        # ... (بقية الكود الخاص بالتوزيعات والمقارنات يبقى كما هو دون تغيير) ...

# ملاحظة: تم اختصار بعض الأجزاء المتكررة للتركيز على التعديلات الأساسية
