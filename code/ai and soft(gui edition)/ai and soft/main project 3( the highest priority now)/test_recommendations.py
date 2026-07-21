import os
import sys

# إعداد المسارات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

try:
    from data_access.data_manager import DataManager
    from logic.recommender import CourseRecommender
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit()

def run_test():
    db = DataManager()
    students, courses, ratings = db.load_all_data()
    recommender = CourseRecommender(students, courses, ratings)
    
    # --- [ التعديل هنا لتجربة الطالب 11 ] ---
    target = "Student_11" 
    
    user_history = ratings[ratings['Student_Name'] == target]
    
    print("\n" + "="*55)
    print(f"👤 PROFILE: {target}")
    print("="*55)
    
    print("📚 Completed Courses & Ratings:")
    if not user_history.empty:
        for _, row in user_history.sort_values('Course_ID').iterrows():
            print(f"   [ID: {row['Course_ID']}] Grade: {row['Rating']}/5")
    else:
        print("   ⚠️ No history found for this student.")
    
    print("-" * 55)

    # تشغيل الترشيح الديناميكي
    recommendations = recommender.get_recommendations(target)

    print(f"✨ Dynamic AI Recommendations for {target}:")
    print(f"(Showing filtered results above 20% confidence)")
    print("-" * 55)

    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            course_id = rec['Course_ID']
            title = rec['Title']
            score = rec['Confidence']
            # استخدام ljust لضبط المسافات في العرض
            print(f"{i}. [ID: {course_id}] {title.ljust(35)} -> Score: {score}")
    else:
        print("⚠️ No courses met the minimum 20% confidence threshold.")

    print("="*55 + "\n")

if __name__ == "__main__":
    run_test()