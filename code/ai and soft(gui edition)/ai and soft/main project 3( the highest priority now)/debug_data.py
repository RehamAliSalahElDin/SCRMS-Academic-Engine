import pandas as pd
import pickle

# تحميل البيانات
courses = pd.read_csv('data/courses.csv')
ratings = pd.read_csv('data/ratings.csv')
with open('models/course_topic_model.pkl', 'rb') as f:
    model_data = pickle.load(f)

student_id = "Student_144"
user_ratings = ratings[ratings['Student_Name'] == student_id]

print(f"--- تقرير تشخيص الطالب {student_id} ---")
print(f"المواد اللي خلصها في تراك 500: \n{user_ratings[user_ratings['Course_ID'].astype(str).str.startswith('5')]}")

# البحث عن المادة المفقودة
print(f"\n--- حالة مادة تراك 500 في قاعدة البيانات ---")
target_track_courses = courses[courses['Course_ID'].astype(str).str.startswith('5')]
for _, row in target_track_courses.iterrows():
    c_id = int(row['Course_ID'])
    in_history = c_id in user_ratings['Course_ID'].values
    in_model = c_id in model_data['ids']
    print(f"ID: {c_id} | Title: {row['Course_Title']} | خلصها؟: {in_history} | موجودة في الـ PKL؟: {in_model}")

print(f"\n--- استنتاج المشكلة ---")
missing_in_model = target_track_courses[~target_track_courses['Course_ID'].isin(model_data['ids'])]
if not missing_in_model.empty:
    print(f"⚠️ كارثة: الموديل (PKL) مش شايف المواد دي: {missing_in_model['Course_Title'].tolist()}")
    print("الحل: لازم تعيد تدريب الموديل (Train) بعد ما ضفت المواد الجديدة في الـ CSV.")