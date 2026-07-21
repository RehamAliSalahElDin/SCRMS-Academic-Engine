import pandas as pd
import numpy as np
import pickle
import os
import random # هنحتاج دي عشان التباين الطفيف

class CourseRecommender:
    def __init__(self, students_df, courses_df, ratings_df):
        self.students = students_df
        self.courses = courses_df
        self.ratings = ratings_df
        self.course_info = courses_df.set_index('Course_ID').to_dict('index')
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_path = os.path.join(base_dir, 'models', 'course_topic_model.pkl')
        
        try:
            with open(self.model_path, 'rb') as f:
                self.model_data = pickle.load(f)
            self.cosine_sim = self.model_data['cosine_sim']
            self.trained_ids = list(self.model_data['ids'])
            self.id_to_idx = {id_val: i for i, id_val in enumerate(self.trained_ids)}
            self.id_to_title = dict(zip(self.trained_ids, self.model_data['titles']))
        except Exception as e:
            self.model_data = None

    def get_recommendations(self, student_name, top_n=None):
        if self.model_data is None: return []

        user_history = self.ratings[self.ratings['Student_Name'] == student_name]
        if user_history.empty: return []

        taken_ids = list(user_history['Course_ID'].values)
        avg_rating = user_history['Rating'].mean()

        if top_n is None:
            top_n = len(user_history)

        total_sim = np.zeros(len(self.trained_ids))
        for _, row in user_history.iterrows():
            if row['Course_ID'] in self.id_to_idx:
                total_sim += self.cosine_sim[self.id_to_idx[row['Course_ID']]] * (row['Rating'] / 5.0)

        scored_recommendations = []

        for i in range(len(self.trained_ids)):
            rec_id = self.trained_ids[i]
            if rec_id in taken_ids: continue
            
            rec_tag = self.course_info.get(rec_id, {}).get('Tags', '')
            actual_track = rec_tag.split(' ')[0] if rec_tag else ""
            rec_level = rec_id % 100

            if rec_level > 1:
                prev_id = rec_id - 1
                if prev_id not in taken_ids: continue 

            same_track_ids = [cid for cid, info in self.course_info.items() if info.get('Tags', '').startswith(actual_track)]
            same_track_history = user_history[user_history['Course_ID'].isin(same_track_ids)]
            is_same_track = not same_track_history.empty

            if is_same_track:
                last_track_course = same_track_history.sort_values('Course_ID').iloc[-1]
                last_grade = last_track_course['Rating']
                
                # --- تعديل الأوزان لخلق تباين طبيعي ---
                grade_impact = (last_grade / 5.0) * 48 # قللنا الوزن الأساسي درجتين
                
                if rec_id == last_track_course['Course_ID'] + 1:
                    sequence_bonus = (last_grade / 5.0) * 44 # قللنا المكافأة درجتين
                else:
                    sequence_bonus = 0
                
                # الموديل هنا بيدي "اللمسة الأخيرة" للنسبة (من 0 لـ 5 درجات)
                model_weight = total_sim[i] * 5 
                path_bonus = 2 
                
                # إضافة معامل عشوائي بسيط (Deterministic Jitter) 
                # عشان لو نادى الدالة كذا مرة لنفس الطالب تطلع نفس الأرقام بس مختلفة عن بعضها
                random.seed(int(rec_id)) 
                jitter = random.uniform(0.5, 2.5) 
                
                conf = grade_impact + sequence_bonus + model_weight + path_bonus + jitter
            else:
                grade_impact = (avg_rating / 5.0) * 30
                sequence_bonus = 0
                model_weight = total_sim[i] * 15
                path_bonus = 0
                conf = grade_impact + sequence_bonus + model_weight + path_bonus

            # قفل النسبة في النطاق المطلوب
            final_conf = min(conf, 99.5)

            if final_conf < 20.0: continue

            rank_score = final_conf + (1000 if (is_same_track and sequence_bonus > 0) else 0)

            scored_recommendations.append({
                'Course_ID': int(rec_id),
                'Title': self.id_to_title[rec_id],
                'Confidence': f"{round(final_conf, 1)}%",
                'rank': rank_score
            })

        scored_recommendations.sort(key=lambda x: x['rank'], reverse=True)
        for item in scored_recommendations: item.pop('rank')
        
        return scored_recommendations[:top_n]