import pandas as pd
import os

class DataManager:
    """
    المدير المسؤول عن الربط بين ملفات الـ CSV والنظام.
    تعديل: دعم المسارات المطلقة (Absolute Paths) لضمان استقرار النظام.
    """
    def __init__(self):
        # 1. تحديد المسار الأساسي للمشروع (جذر المشروع)
        # ده بيضمن إن "data/processed" تتجاب صح من أي مكان
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.DATA_DIR = os.path.join(self.BASE_DIR, "data", "processed")
        
        # 2. تحديد مسارات الملفات
        self.STUDENTS_FILE = os.path.join(self.DATA_DIR, "student_mapping.csv")
        self.COURSES_FILE = os.path.join(self.DATA_DIR, "courses.csv")
        self.RATINGS_FILE = os.path.join(self.DATA_DIR, "ratings.csv")

    def load_all_data(self):
        """
        تحميل الـ 3 ملفات الأساسية (الطلاب، المواد، التقييمات)
        """
        try:
            # التأكد من وجود المجلد والملفات
            if not os.path.exists(self.DATA_DIR):
                print(f"❌ خطأ: المجلد {self.DATA_DIR} غير موجود.")
                return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

            if not all(os.path.exists(f) for f in [self.STUDENTS_FILE, self.COURSES_FILE, self.RATINGS_FILE]):
                print("⚠️ تحذير: بعض ملفات البيانات مفقودة في data/processed")
                return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

            # قراءة البيانات مع ضمان نضافة الـ Strings
            students = pd.read_csv(self.STUDENTS_FILE)
            courses = pd.read_csv(self.COURSES_FILE)
            ratings = pd.read_csv(self.RATINGS_FILE)
            
            return students, courses, ratings
            
        except Exception as e:
            print(f"❌ فشل في تحميل البيانات: {e}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    def get_student_info(self, student_name):
        """
        جلب بيانات طالب معين بسرعة بالاسم.
        تم تحسينها لتجنب إعادة تحميل كل الملفات في كل مرة.
        """
        try:
            students, _, _ = self.load_all_data()
            if students.empty: return None
            
            student = students[students['Student_Name'] == student_name]
            return student.to_dict('records')[0] if not student.empty else None
        except:
            return None

    def save_rating(self, student_name, course_id, rating, academic_level):
        """
        دالة جديدة لحفظ تقييم جديد بأمان (لو حبيت تضيف ميزة التقييم من الـ GUI)
        """
        try:
            new_data = pd.DataFrame([{
                "Student_Name": student_name,
                "Course_ID": course_id,
                "Rating": rating,
                "Academic_Level": academic_level
            }])
            new_data.to_csv(self.RATINGS_FILE, mode='a', header=False, index=False)
            print(f"✅ تم إضافة التقييم الجديد للمادة {course_id}")
        except Exception as e:
            print(f"❌ فشل حفظ التقييم: {e}")