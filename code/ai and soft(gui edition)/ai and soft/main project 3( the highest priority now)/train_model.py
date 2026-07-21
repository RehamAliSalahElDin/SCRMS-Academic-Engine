import pandas as pd
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def train_academic_model():
    # 1. تحديد المسارات بشكل ديناميكي لضمان الوصول للملف الجديد
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, 'data', 'ordered_course_data_1000.csv')
    
    if not os.path.exists(file_path):
        print(f"❌ خطأ: لم يتم العثور على ملف البيانات في {file_path}")
        print("تأكد من تشغيل ملف data_generator.py أولاً!")
        return

    df = pd.read_csv(file_path)

    # 2. تجهيز الميزات (Features) بدقة عالية
    # بنجمع العنوان مع التاجز عشان الـ AI يفهم إن Robotics (503) 
    # هي "الخطوة التالية" منطقياً بعد Modern Digital Control (502) لأن ليهم نفس الـ Track Tag
    df['combined_features'] = df['course_title'] + " " + df['Tags']
    
    # الحصول على قائمة المواد الـ 40 الفريدة لبناء مصفوفة التشابه
    unique_courses = df.drop_duplicates(subset=['Course_ID']).sort_values('Course_ID').copy()
    
    # 3. تحويل النصوص لأرقام باستخدام TF-IDF
    # الـ Vectorizer ده هو اللي بيحلل الكلمات وبيفهم إن track_500 مكرر في مادتين
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(unique_courses['combined_features'])
    
    # 4. حساب مصفوفة التشابه الجيبي (Cosine Similarity)
    # هنا بقى "سحر" الـ Robotics؛ الموديل هيحسب إن 503 تشبه 502 بنسبة عالية جداً
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    # 5. تجهيز البيانات المراد حفظها بنفس التنسيق الاحترافي بتاعك
    model_data = {
        'cosine_sim': cosine_sim,
        'titles': unique_courses['course_title'].values,
        'ids': unique_courses['Course_ID'].values,
        'tags': unique_courses['Tags'].values,
        'raw_df': df # بنحفظ الـ df الأصلي عشان الموديل يرجع لتقييمات الطالب 144
    }
    
    # 6. حفظ الموديل المحدث في فولدر models
    models_dir = os.path.join(base_dir, 'models')
    if not os.path.exists(models_dir): 
        os.makedirs(models_dir)
        
    model_output_path = os.path.join(models_dir, 'course_topic_model.pkl')
    with open(model_output_path, 'wb') as f:
        pickle.dump(model_data, f)
        
    print("---" * 10)
    print("✅ Step 2: AI Model Trained on Robotics-Ready Curriculum.")
    print(f"📊 Total Courses in Knowledge Base: {len(unique_courses)}/40")
    print(f"📍 New Model saved at: {model_output_path}")
    print("---" * 10)

if __name__ == "__main__":
    train_academic_model()