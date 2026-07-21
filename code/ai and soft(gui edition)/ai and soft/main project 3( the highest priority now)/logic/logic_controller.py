import re
import datetime
import pickle
import pandas as pd
import os
from data_access.data_manager import DataManager

class SystemLogic:
    def __init__(self):
        # تحديد المسار المطلق للموديل لضمان الوصول إليه
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(base_dir, 'models', 'course_topic_model.pkl')
        self.db = DataManager() # إنشاء نسخة من مدير البيانات الجديد

    @staticmethod
    def log_event(action, entity, record_id, status="SUCCESS"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} | {action:<8} | {entity:<10} | ID: {record_id:<5} | {status}\n"
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_path = os.path.join(base_dir, "data", "system_operations.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)

    def get_recommendations(self, student_name, top_n=3):
        """
        الوظيفة الأهم: استدعاء الموديل وحساب الترشيحات بدقة
        """
        try:
            if not os.path.exists(self.model_path):
                return "❌ Model file not found. Please train the model first."

            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
            
            cosine_sim = model_data['cosine_sim']
            course_ids = list(model_data['ids'])
            course_titles = model_data['titles']
            raw_df = model_data['raw_df']

            # 1. جلب تاريخ الطالب من الداتا الأساسية
            student_history = raw_df[raw_df['Student_Name'] == student_name]['Course_ID'].unique().tolist()
            
            if not student_history:
                return f"No history found for {student_name}."

            # 2. تحديد آخر مادة الطالب أخدها (أو أهم مادة في مساره)
            # للـ Student_144 هتكون 502 (Modern Control)
            last_course_id = student_history[-1]
            
            if last_course_id not in course_ids:
                return "Course ID in history is missing from the trained model."

            idx = course_ids.index(last_course_id)
            
            # 3. حساب المواد المشابهة بناءً على الـ Cosine Similarity
            sim_scores = list(enumerate(cosine_sim[idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            
            # 4. الفلترة: استبعاد المواد اللي أخدها قبل كدة واختيار الأقرب
            recommendations = []
            for i, score in sim_scores:
                c_id = course_ids[i]
                c_title = course_titles[i]
                
                # تخطي المادة نفسها والمواد اللي الطالب أخدها
                if c_id not in student_history and c_title not in recommendations:
                    recommendations.append(c_title)
                
                if len(recommendations) >= top_n:
                    break
            
            return recommendations

        except Exception as e:
            return f"Error in Recommendation Logic: {str(e)}"

    def delete_course_cascade(self, course_id):
        """الحذف المتتالي باستخدام الـ DataManager الموحد"""
        students, courses, ratings = self.db.load_all_data()
        
        new_courses = courses[courses['Course_ID'] != course_id]
        new_ratings = ratings[ratings['Course_ID'] != course_id]
        
        self.db.save_record(new_courses, self.db.COURSES_FILE)
        self.db.save_record(new_ratings, self.db.RATINGS_FILE)
        
        self.log_event("DELETE", "Course", course_id)
        return True