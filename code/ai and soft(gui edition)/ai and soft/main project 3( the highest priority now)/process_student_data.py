import pandas as pd
import random
import os

# 1. إعداد المسارات
base_dir = os.path.dirname(os.path.abspath(__file__))
source_path = os.path.join(base_dir, "data", "ordered_course_data_1000.csv")

if not os.path.exists(source_path):
    print(f"❌ خطأ: الملف غير موجود في {source_path}")
    exit()

df = pd.read_csv(source_path)

# 2. إعداد اللوجيك الخاص بالليفل
def calculate_student_level(group, student_name):
    # استخراج رقم الليفل من الـ Tags
    max_course_level = group['Tags'].str.extract(r'level_(\d)').astype(int).max()[0]
    
    # قانون الطالب 144: لازم يكون ليفل عالي عشان مادة الـ Robotics
    if student_name == 'Student_144':
        return "Level 3" 
    
    # بقية الطلاب: ليفل عشوائي بشرط ميكنش أقل من أصعب مادة خلصها
    academic_level = random.randint(max_course_level, 4)
    return f"Level {academic_level}"

# 3. تجميع الطلاب (Profile Generation)
# استخدمنا group_keys=False لتجنب مشاكل الـ Index في النسخ الجديدة
student_groups = df.groupby('Student_Name')
student_meta = student_groups.apply(lambda x: pd.Series({
    'Faculty': 'Engineering',
    'Department': 'Intelligent Systems',
    'Academic_Level': calculate_student_level(x, x.name), # x.name هو اسم الطالب في الجروب
    'Email': f"{str(x.name).lower()}@uni.edu.eg"
}), include_groups=False).reset_index() 

# دمج البيانات الوصفية مع الجدول الأساسي
df = df.merge(student_meta, on='Student_Name')

# 4. إنشاء الملفات في فولدر processed
output_folder = os.path.join(base_dir, "data", "processed")
if not os.path.exists(output_folder): 
    os.makedirs(output_folder)

# --- 1. ratings.csv ---
ratings = df[['Student_Name', 'Course_ID', 'Rating', 'Academic_Level']]
ratings.to_csv(os.path.join(output_folder, "ratings.csv"), index=False)

# --- 2. courses.csv ---
courses = df[['Course_ID', 'course_title', 'Tags']].drop_duplicates().sort_values('Course_ID')
courses.to_csv(os.path.join(output_folder, "courses.csv"), index=False)

# --- 3. student_mapping.csv ---
students = student_meta.copy()
students['Student_ID'] = range(1000, 1000 + len(students))
students = students[['Student_ID', 'Student_Name', 'Email', 'Faculty', 'Department', 'Academic_Level']]
students.to_csv(os.path.join(output_folder, "student_mapping.csv"), index=False)

print("---")
print(f"✅ مبروك يا هندسة! الكود اتصلح واشتغل تمام.")
print(f"📊 تم معالجة {len(student_meta)} طالب بنجاح.")
print(f"📍 الملفات موجودة هنا: {output_folder}")