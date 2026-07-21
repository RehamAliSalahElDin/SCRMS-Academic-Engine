import pandas as pd
import random
import os

# 1. الخريطة الأكاديمية (10 تراكات كاملة - 4 مواد لكل تراك)
curriculum_chains = {
    'Math': [101, 102, 103, 104],
    'Software': [201, 202, 203, 204],
    'Physics': [301, 302, 303, 304],
    'Embedded': [401, 402, 403, 404],
    'Control': [501, 502, 503, 504],
    'AI': [601, 602, 603, 604],
    'Telecom': [701, 702, 703, 704],
    'Networks': [801, 802, 803, 804],
    'Data_Eng': [901, 902, 903, 904],
    'Electrical': [111, 112, 113, 114]
}

# 2. قاموس المواد (نفس بياناتك بالظبط)
course_info = {
    101: ("Linear Algebra", "track_100 level_1"), 102: ("Numerical Analysis", "track_100 level_2"),
    103: ("Probability & Statistics", "track_100 level_3"), 104: ("Optimization Techniques", "track_100 level_4"),
    201: ("Object-Oriented Programming", "track_200 level_1"), 202: ("Data Structures & Algorithms", "track_200 level_2"),
    203: ("Software Architecture", "track_200 level_3"), 204: ("Cloud-Native Development", "track_200 level_4"),
    301: ("Electricity and Magnetism", "track_300 level_1"), 302: ("Semiconductor Physics", "track_300 level_2"),
    303: ("Optoelectronics", "track_300 level_3"), 304: ("Quantum Computing Basics", "track_300 level_4"),
    401: ("Microprocessor Architecture", "track_400 level_1"), 402: ("Real-Time Systems (RTOS)", "track_400 level_2"),
    403: ("Hardware Description Languages (HDL)", "track_400 level_3"), 404: ("System on Chip (SoC) Design", "track_400 level_4"),
    501: ("Classical Control Theory", "track_500 level_1"), 502: ("Modern Digital Control", "track_500 level_2"),
    503: ("Robotics & Kinematics", "track_500 level_3"), 504: ("Adaptive Control Systems", "track_500 level_4"),
    601: ("Pattern Recognition", "track_600 level_1"), 602: ("Neural Networks & Deep Learning", "track_600 level_2"),
    603: ("Computer Vision", "track_600 level_3"), 604: ("Natural Language Processing", "track_600 level_4"),
    701: ("Communication Theory", "track_700 level_1"), 702: ("Digital Signal Processing (DSP)", "track_700 level_2"),
    703: ("Wireless Communication", "track_700 level_3"), 704: ("Information Theory & Coding", "track_700 level_4"),
    801: ("Networking Fundamentals", "track_800 level_1"), 802: ("Routing & Switching", "track_800 level_2"),
    803: ("Network Security", "track_800 level_3"), 804: ("Software Defined Networking (SDN)", "track_800 level_4"),
    901: ("Database Management Systems", "track_900 level_1"), 902: ("Big Data Technologies", "track_900 level_2"),
    903: ("Data Warehousing", "track_900 level_3"), 904: ("ETL Pipeline Design", "track_900 level_4"),
    111: ("Electric Circuits Analysis", "track_110 level_1"), 112: ("Electronic Devices", "track_110 level_2"),
    113: ("Power Systems Engineering", "track_110 level_3"), 114: ("Renewable Energy Systems", "track_110 level_4")
}

def generate_1000_ratings():
    data = []
    student_id = 1
    
    while len(data) < 1000:
        student_name = f"Student_{student_id}"
        num_tracks = random.randint(3, 6)
        chosen_tracks = random.sample(list(curriculum_chains.keys()), num_tracks)
        student_history = set()
        
        for track in chosen_tracks:
            chain = curriculum_chains[track]
            
            # --- التعديل الجوهري هنا ---
            # لو إحنا في أول 800 سجل، هنلتزم بالقانون القديم (مادة أو مادتين)
            # لو عدينا الـ 800، هنخلي الطلاب "دحيحة" ياخدوا التراك كله (3 أو 4 مواد)
            if len(data) < 800:
                student_progress = random.randint(1, 2)
            else:
                student_progress = random.randint(3, 4) 
            
            for i in range(student_progress):
                course_id = chain[i]
                if course_id not in student_history:
                    if len(data) < 1000:
                        rating = random.randint(3, 5)
                        title, tags = course_info[course_id]
                        data.append({
                            "Student_Name": student_name,
                            "Course_ID": course_id,
                            "Rating": rating,
                            "course_title": title,
                            "Tags": tags,
                            "sort_key": i 
                        })
                        student_history.add(course_id)
                if len(data) >= 1000: break
            if len(data) >= 1000: break
        student_id += 1
        
    return pd.DataFrame(data)

# التنفيذ
df = generate_1000_ratings()

# الترتيب النهائي (حسب الطالب ثم التراك ثم الليفل)
# ده اللي بيخليك تشوف تكرار الطالب ورا بعضه بمواده المختلفة
df = df.sort_values(by=['Student_Name', 'Course_ID', 'sort_key'])
df = df.drop(columns=['sort_key'])

# الحفظ
target_folder = r"C:\Users\GHOST\Downloads\main project 3( the highest priority now)\data"
target_file = os.path.join(target_folder, "ordered_course_data_1000.csv")

try:
    if not os.path.exists(target_folder): os.makedirs(target_folder)
    df.to_csv(target_file, index=False)
    print(f"✅ مبروك! تم توليد الداتا سيت.")
    print(f"📊 الطلاب في آخر الملف دلوقتى 'دحيحة' ومخلصين التراكات لآخرها.")
except Exception as e:
    print(f"❌ خطأ: {e}")