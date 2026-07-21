import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, ttk

# محاولة استيراد الـ Recommender الخاص بك
try:
    from logic.recommender import CourseRecommender
except ImportError:
    # كلاس وهمي في حال لم يجد الملف لضمان عمل الواجهة
    class CourseRecommender:
        def __init__(self, s, c, r): pass
        def get_recommendations(self, name): return []

# --- [ الإعدادات والمسارات الأصلية ] ---
SYSTEM_ADMIN_EMAIL = "superadmin1234@gmail.com"
SYSTEM_ADMIN_PASSWORD = "superadmin1234"  # الباسورد الافتراضي (Default)
ADMIN_EMAIL = "admin1234@gmail.com"
ADMIN_PASSWORD = "admin1234"            # الباسورد الافتراضي للـ Admin

# --- [ ملفات حفظ البيانات الحساسة ] ---
SUPER_ADMIN_PWD_FILE = "admin_cfg.txt"
ADMIN_PWD_FILE = "admin_cred.txt"

# 1. التحقق من باسوورد السوبر أدمن (Permanent Super Admin Password)
if os.path.exists(SUPER_ADMIN_PWD_FILE):
    try:
        with open(SUPER_ADMIN_PWD_FILE, "r", encoding='utf-8') as f:
            saved_super_pwd = f.read().strip()
            if saved_super_pwd:
                SYSTEM_ADMIN_PASSWORD = saved_super_pwd
    except Exception as e:
        print(f"Error loading Super Admin password: {e}")

# 2. التحقق من باسوورد الأدمن العادي
if os.path.exists(ADMIN_PWD_FILE):
    try:
        with open(ADMIN_PWD_FILE, "r", encoding='utf-8') as f:
            saved_pwd = f.read().strip()
            if saved_pwd:
                ADMIN_PASSWORD = saved_pwd
    except Exception as e:
        print(f"Error loading admin password: {e}")

# --- [ مسارات البيانات ] ---
DATA_PATH = "data/processed/"
STUDENTS_FILE = os.path.join(DATA_PATH, "student_mapping.csv")
COURSES_FILE = os.path.join(DATA_PATH, "courses.csv")
RATINGS_FILE = os.path.join(DATA_PATH, "ratings.csv")
LOG_FILE = "data/activity.log"

class UniversityGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # المتغيرات العالمية من كودك
        self.maintenance_mode = False
        self.current_user_data = None
        self.user_role = None # "SYSTEM_ADMIN", "ADMIN", "STUDENT"
        
        # إعدادات النافذة
        self.title("UNIVERSITY KNOWLEDGE AI SYSTEM - GUI EDITION")
        self.geometry("1000x700")
        ctk.set_appearance_mode("dark")
        
        self.load_initial_data()
        self.show_login_page()

    # ----------------------- [ LOGIC METHODS ] -----------------------
    def log_activity(self, actor, action, details):
        if not os.path.exists('data'): os.makedirs('data')
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] | Actor: {actor:<15} | Action: {action:<18} | Details: {details}\n")

    def load_initial_data(self):
        try:
            if not os.path.exists(DATA_PATH): os.makedirs(DATA_PATH)
            if not os.path.exists(STUDENTS_FILE):
                # إنشاء ملفات تجريبية لو مش موجودة عشان الكود ميقفش
                pd.DataFrame(columns=['Student_ID', 'Student_Name', 'Email', 'Password', 'Faculty', 'Department', 'Academic_Level']).to_csv(STUDENTS_FILE, index=False)
            
            self.students_df = pd.read_csv(STUDENTS_FILE)
            self.courses_df = pd.read_csv(COURSES_FILE) if os.path.exists(COURSES_FILE) else pd.DataFrame(columns=['Course_ID', 'course_title', 'Tags', 'Credit_Hours'])
            self.ratings_df = pd.read_csv(RATINGS_FILE) if os.path.exists(RATINGS_FILE) else pd.DataFrame(columns=['Student_Name', 'Course_ID', 'Rating'])
            
            # تنظيف البيانات عشان تسجيل الدخول يشتغل بدون مشاكل
            for df in [self.students_df, self.courses_df, self.ratings_df]:
                df.columns = df.columns.str.strip()
            
            # تحويل الـ ID والباسورد لـ String عشان ميعملش مشكلة Invalid Credentials
            self.students_df['Student_ID'] = self.students_df['Student_ID'].astype(str).str.strip()
            self.students_df['Email'] = self.students_df['Email'].astype(str).str.strip().str.lower()
            self.students_df['Password'] = self.students_df['Password'].astype(str).str.strip()
        except Exception as e:
            messagebox.showerror("Data Error", f"Error loading CSV files: {e}")

    # ----------------------- [ UI SCREENS ] -----------------------
    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_login_page(self):
        self.clear_screen()
        self.user_role = None
        
        main_frame = ctk.CTkFrame(self, width=400, height=500)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(main_frame, text="UNIVERSITY KNOWLEDGE AI", font=("Arial", 22, "bold")).pack(pady=20)
        if self.maintenance_mode:
            ctk.CTkLabel(main_frame, text="🛠️ SYSTEM UNDER MAINTENANCE", text_color="orange").pack()

        self.email_ent = ctk.CTkEntry(main_frame, placeholder_text="Email or Student ID", width=250)
        self.email_ent.pack(pady=10)
        
        self.pass_ent = ctk.CTkEntry(main_frame, placeholder_text="Password", show="*", width=250)
        self.pass_ent.pack(pady=10)
        
        ctk.CTkButton(main_frame, text="Login", command=self.handle_login).pack(pady=20)

    def handle_login(self):
        # سحب البيانات من حقول الإدخال الخاصة بك
        email = self.email_ent.get().strip()
        pwd = self.pass_ent.get().strip()
        
        # 1. System Admin (صلاحيات السيرفر والإعدادات الكبرى)
        if email.lower() == SYSTEM_ADMIN_EMAIL.lower() and pwd == SYSTEM_ADMIN_PASSWORD:
            self.user_role = "SYSTEM_ADMIN"
            self.log_activity("SYSTEM_ADMIN", "LOGIN", "Success")
            self.show_sys_admin_panel()
            return

        # 2. Admin (هنا التعديل: نستخدم global لضمان قراءة أحدث باسورد)
        global ADMIN_PASSWORD # عشان يقرأ القيمة اللي اتحدثت من الملف
        if email.lower() == ADMIN_EMAIL.lower() and pwd == ADMIN_PASSWORD:
            self.user_role = "ADMIN"
            self.log_activity("ADMIN", "LOGIN", "Success")
            self.show_admin_panel()
            return

        # 3. Student (التحقق من الإيميل أو الـ ID مع الباسورد)
        # الكود هنا تمام مفيش فيه تغيير
        # منطق الدخول الجديد: يشيك على login email ولو فاضي يشيك على الـ ID
        def get_login_id(row):
            val = str(row['login email']).strip().lower()
            # لو الخانة فاضية أو فيها nan (زي ما واضح في صورتك) يرجع الـ ID
            return val if val != 'nan' and val != '' else str(row['Student_ID'])

        # الفلتر الجديد
        student_match = self.students_df[
            (self.students_df.apply(lambda r: get_login_id(r), axis=1) == email.lower()) & 
            (self.students_df['Password'].astype(str) == pwd)
        ]
        
        if not student_match.empty:
            if self.maintenance_mode:
                messagebox.showwarning("Maintenance", "System is currently undergoing maintenance.")
                self.log_activity(f"ID_{email}", "LOGIN_BLOCKED", "Maintenance Mode Active")
                return
            
            self.current_user_data = student_match.iloc[0].to_dict()
            self.user_role = "STUDENT"
            self.log_activity(self.current_user_data['Student_Name'], "STUDENT_LOGIN", f"ID: {self.current_user_data['Student_ID']}")
            self.show_student_portal()
        else:
            self.log_activity(email, "LOGIN_FAIL", "Invalid Credentials")
            messagebox.showerror("Error", "Invalid Login Credentials")

    # ----------------------- [ SYSTEM ADMIN PANEL ] -----------------------
    # ----------------------- [ SYSTEM ADMIN PANEL ] -----------------------
    def show_sys_admin_panel(self):
        """تحديث لوحة التحكم لإضافة خيار تغيير باسورد السوبر أدمن"""
        self.clear_screen()
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.sidebar, text="🛡️ SYSTEM ADMIN", font=("Arial", 18, "bold")).pack(pady=25)
        
        # الأزرار الحالية
        ctk.CTkButton(self.sidebar, text="View Logs", command=self.sys_view_logs).pack(pady=8, padx=15)
        
        ctk.CTkButton(self.sidebar, text="Clear Logs", command=self.sys_clear_logs, 
                     fg_color="#c0392b", hover_color="#a93226").pack(pady=8, padx=15)
        
        m_text = f"Maintenance: {'ON' if self.maintenance_mode else 'OFF'}"
        m_color = "#e67e22" if self.maintenance_mode else "#2ecc71"
        self.m_btn = ctk.CTkButton(self.sidebar, text=m_text, fg_color=m_color, command=self.sys_toggle_maintenance)
        self.m_btn.pack(pady=8, padx=15)
        
        ctk.CTkButton(self.sidebar, text="Manage Students", command=self.show_edit_student_ui).pack(pady=8, padx=15)

        # --- [ الزرار الجديد هنا ] ---
        ctk.CTkButton(self.sidebar, text="Change My Password", fg_color="transparent", 
                     border_width=1, command=self.sys_change_admin_pwd).pack(pady=8, padx=15)
        # ----------------------------
        
        ctk.CTkButton(self.sidebar, text="Reset ALL Passwords", fg_color="transparent", border_width=1, 
                     command=self.sys_reset_all_passwords).pack(pady=8, padx=15)

        ctk.CTkButton(self.sidebar, text="Logout", command=self.show_login_page, 
                     fg_color="gray30").pack(side="bottom", pady=30)

        # المساحة الرئيسية لعرض اللوجات أو الفورم
        self.main_view = ctk.CTkFrame(self)
        self.main_view.pack(side="right", fill="both", expand=True, padx=15, pady=15)
        
        # عرض اللوجات بشكل افتراضي عند الدخول
        self.sys_view_logs()

    def sys_view_logs(self):
        """عرض السجلات في المساحة الرئيسية"""
        for widget in self.main_view.winfo_children(): widget.destroy()
        
        ctk.CTkLabel(self.main_view, text="System Activity Logs", font=("Arial", 20, "bold")).pack(pady=10)
        
        log_display = ctk.CTkTextbox(self.main_view, width=700, height=500, font=("Consolas", 12))
        log_display.pack(fill="both", expand=True, padx=15, pady=10)
        
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                log_display.insert("0.0", "".join(lines[-50:])) # عرض آخر 50 سطر
        else:
            log_display.insert("0.0", "No log file found.")
        
        log_display.configure(state="disabled")

    def sys_clear_logs(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete ALL logs?"):
            with open(LOG_FILE, 'w', encoding='utf-8') as f: f.write("")
            self.log_activity("SYSTEM_ADMIN", "CLEAR_LOGS", "Log file truncated")
            self.sys_view_logs()

    def sys_change_admin_pwd(self):
        """تغيير باسورد السوبر أدمن وحفظه في admin_cfg.txt"""
        dialog = ctk.CTkInputDialog(text="Enter New Super Admin Password:", title="Security Update")
        new_pwd = dialog.get_input()
        
        if new_pwd:
            new_pwd = str(new_pwd).strip()
            if len(new_pwd) < 4:
                messagebox.showerror("Error", "Password too short! (Min 4 chars)")
                return
            
            try:
                # تحديث المتغير العام
                global SYSTEM_ADMIN_PASSWORD
                SYSTEM_ADMIN_PASSWORD = new_pwd
                
                # حفظ في الملف (admin_cfg.txt)
                with open("admin_cfg.txt", "w", encoding="utf-8") as f:
                    f.write(new_pwd)
                
                self.log_activity("SYSTEM_ADMIN", "ADMIN_PWD_CHANGE", "Super Admin password updated via GUI")
                messagebox.showinfo("Success", "Password updated and saved to config file!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save changes: {e}")

    def sys_toggle_maintenance(self):
        self.maintenance_mode = not self.maintenance_mode
        status = "ON" if self.maintenance_mode else "OFF"
        color = "#e67e22" if self.maintenance_mode else "#2ecc71"
        self.m_btn.configure(text=f"Maintenance: {status}", fg_color=color)
        self.log_activity("SYSTEM_ADMIN", "MAINTENANCE", f"Set to {status}")
        messagebox.showinfo("System Status", f"Maintenance Mode is now {status}")

    def show_edit_student_ui(self):
        """واجهة تعديل بيانات الطلاب (بديل الـ Input Dialogs)"""
        for widget in self.main_view.winfo_children(): widget.destroy()
        
        ctk.CTkLabel(self.main_view, text="Manage Student Credentials", font=("Arial", 20, "bold")).pack(pady=20)
        
        form_frame = ctk.CTkFrame(self.main_view, fg_color="transparent")
        form_frame.pack(pady=10)

        # الحقول
        ctk.CTkLabel(form_frame, text="Target Student ID:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        sid_ent = ctk.CTkEntry(form_frame, width=200)
        sid_ent.grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkLabel(form_frame, text="New Email:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        email_ent = ctk.CTkEntry(form_frame, width=200, placeholder_text="Keep current if blank")
        email_ent.grid(row=1, column=1, padx=10, pady=10)

        ctk.CTkLabel(form_frame, text="New Password:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        pass_ent = ctk.CTkEntry(form_frame, width=200, placeholder_text="Keep current if blank")
        pass_ent.grid(row=2, column=1, padx=10, pady=10)

        def perform_update():
            sid = sid_ent.get().strip()
            new_login_val = email_ent.get().strip().lower() 
            new_pass = pass_ent.get().strip()

            if not sid:
                messagebox.showwarning("Input Error", "Please enter a Student ID")
                return

            # التأكد من وجود الطالب في قاعدة البيانات
            if sid not in self.students_df['Student_ID'].astype(str).values:
                messagebox.showerror("Error", f"Student ID {sid} not found!")
                return

            # --- التعديل الجديد: ملء العمود بالقيم الافتراضية (الأكواد) لو كانت فاضية ---
            # أولاً نضمن أن العمود نوعه نصوص (Object)
            self.students_df['login email'] = self.students_df['login email'].astype(object)
            
            # نملأ أي خلية فاضية بقيمة الـ Student_ID المقابل لها
            self.students_df['login email'] = self.students_df['login email'].fillna(self.students_df['Student_ID'].astype(str))

            conflict = False
            
            # التحقق من تكرار إيميل الدخول
            if new_login_val:
                # التأكد من عدم استخدام نفس الإيميل لطالب آخر
                existing_emails = self.students_df['login email'].astype(str)
                email_exists = self.students_df[(existing_emails == new_login_val) & 
                                              (self.students_df['Student_ID'].astype(str) != sid)]
                if not email_exists.empty:
                    messagebox.showerror("Conflict", f"Login Email '{new_login_val}' is already used by another student!")
                    conflict = True

            # التحقق من أمن الباسورد
            if not conflict and new_pass:
                if new_pass in self.students_df['Student_ID'].astype(str).values:
                    owner_rows = self.students_df[self.students_df['Student_ID'].astype(str) == new_pass]['Student_ID'].values
                    if len(owner_rows) > 0 and str(owner_rows[0]) != sid:
                        messagebox.showerror("Conflict", f"Security Risk: Password '{new_pass}' is the ID of student {owner_rows[0]}!")
                        conflict = True

            # تنفيذ التحديث
            if not conflict:
                mask = self.students_df['Student_ID'].astype(str) == sid
                
                if new_login_val: 
                    self.students_df.loc[mask, 'login email'] = new_login_val
                
                if new_pass: 
                    self.students_df.loc[mask, 'Password'] = new_pass
                
                try:
                    self.students_df.to_csv(STUDENTS_FILE, index=False)
                    self.log_activity("SYSTEM_ADMIN", "EDIT_STUDENT", f"Updated credentials for ID: {sid}")
                    
                    messagebox.showinfo("Success", "Credentials updated and defaults assigned!")
                    
                    sid_ent.delete(0, 'end')
                    email_ent.delete(0, 'end')
                    pass_ent.delete(0, 'end')
                except Exception as e:
                    messagebox.showerror("File Error", f"Could not save data: {e}")

        # زر تنفيذ العملية
        ctk.CTkButton(self.main_view, text="Update Records", command=perform_update, 
                      fg_color="#2ecc71", hover_color="#27ae60", width=200).pack(pady=20)
        
    def sys_reset_all_passwords(self):
        """إعادة تعيين كل كلمات المرور وإيميلات الدخول لتصبح هي الـ ID"""
        if messagebox.askyesno("DANGER", "Reset ALL student passwords AND login emails to their default IDs?"):
            try:
                # 1. إعادة تعيين الباسورد لكل الطلاب ليكون هو الكود
                self.students_df['Password'] = self.students_df['Student_ID'].astype(str)
                
                # 2. إعادة تعيين إيميل الدخول لكل الطلاب ليكون هو الكود
                # بنضمن الأول إن العمود موجود ونوعه نصوص
                self.students_df['login email'] = self.students_df['Student_ID'].astype(str)
                
                # 3. حفظ التغييرات في ملف الـ CSV
                self.students_df.to_csv(STUDENTS_FILE, index=False)
                
                # تسجيل العملية في السجل
                self.log_activity("SYSTEM_ADMIN", "FULL_SYSTEM_RESET", "All passwords and login emails reset to default IDs")
                
                messagebox.showinfo("Success", "All student credentials (Passwords & Login Emails) have been reset to default IDs.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Operation failed: {e}")

    # ----------------------- [ ADMIN PANEL ] -----------------------
    # ----------------------- [ ADMIN PORTAL - FULL CODE ] -----------------------
    def show_admin_panel(self):
        """لوحة التحكم الرئيسية للأدمن (Instructor/Manager)"""
        self.clear_screen()
        ctk.CTkLabel(self, text="ADMIN PANEL - DATABASE MANAGEMENT", font=("Arial", 22, "bold"), text_color="#1f6aa5").pack(pady=15)

        # إنشاء التابات لتنظيم المهام (طلاب - كورس - إعدادات)
        self.admin_tabs = ctk.CTkTabview(self, width=950, height=580)
        self.admin_tabs.pack(padx=10, pady=5, fill="both", expand=True)
        
        self.admin_tabs.add("Manage Students")
        self.admin_tabs.add("Manage Courses")
        self.admin_tabs.add("Admin Settings")

        # --- [ Tab 1: Students ] ---
        st_tab = self.admin_tabs.tab("Manage Students")
        
        # فريم علوي للأزرار والسيرش عشان يبقوا جنب بعض
        st_controls = ctk.CTkFrame(st_tab, fg_color="transparent")
        st_controls.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(st_controls, text="[+] Add New Student", fg_color="#2ecc71", hover_color="#27ae60", 
                      command=self.admin_add_student).pack(side="left")

        # --- إضافة السيرش بار البسيط هنا ---
        self.st_search_ent = ctk.CTkEntry(st_controls, placeholder_text="🔍 Search by ID...", width=250)
        self.st_search_ent.pack(side="right")
        # ربط الكتابة بالفلترة التلقائية
        self.st_search_ent.bind("<KeyRelease>", lambda e: self.refresh_admin_data())
        # ----------------------------------

        self.st_list_frame = ctk.CTkScrollableFrame(st_tab, width=900, height=400)
        self.st_list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # --- [ Tab 2: Courses ] ---
        co_tab = self.admin_tabs.tab("Manage Courses")
        ctk.CTkButton(co_tab, text="[+] Add New Course", fg_color="#2ecc71", hover_color="#27ae60", 
                      command=self.admin_add_course).pack(pady=10)
        
        self.co_list_frame = ctk.CTkScrollableFrame(co_tab, width=900, height=400)
        self.co_list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # --- [ Tab 3: Settings ] ---
        set_tab = self.admin_tabs.tab("Admin Settings")
        ctk.CTkLabel(set_tab, text="Security & Session Controls", font=("Arial", 18, "bold")).pack(pady=20)
        
        self.new_admin_pwd_ent = ctk.CTkEntry(set_tab, placeholder_text="Enter New Admin Password", width=300, show="*")
        self.new_admin_pwd_ent.pack(pady=10)
        ctk.CTkButton(set_tab, text="Update Admin Password", command=self.admin_reset_pwd).pack(pady=10)

        # زرار تسجيل الخروج
        ctk.CTkButton(self, text="Logout Admin", fg_color="#8B0000", hover_color="#5c0000", 
                      command=self.show_login_page).pack(pady=20)
        
        # تعبئة البيانات فور فتح اللوحة
        self.refresh_admin_data()

    def refresh_admin_data(self):
        """تحديث قوائم الطلاب والكورسات من ملفات الـ CSV مع دعم البحث"""
        # 1. تنظيف الفريمات
        for w in self.st_list_frame.winfo_children(): w.destroy()
        for w in self.co_list_frame.winfo_children(): w.destroy()

        # 2. الحصول على نص البحث من السيرش بار (لو موجود)
        search_query = ""
        try:
            search_query = self.st_search_ent.get().strip().lower()
        except:
            pass # لو السيرش بار لسه متخلقش (أول مرة) بنكمل عادي

        # 3. عرض الطلاب (مع الفلترة)
        for _, row in self.students_df.iterrows():
            sid = str(row['Student_ID'])
            sname = str(row['Student_Name']).lower()
            
            # منطق الفلترة: لو السيرش فاضي بيعرض الكل، لو فيه كتابة بيقارنها بالـ ID أو الاسم
            if not search_query or (search_query in sid or search_query in sname):
                f = ctk.CTkFrame(self.st_list_frame, fg_color="#2b2b2b")
                f.pack(fill="x", pady=2, padx=5)
                ctk.CTkLabel(f, text=f"ID: {row['Student_ID']} | Name: {row['Student_Name']} | Dept: {row['Department']}", 
                             font=("Arial", 12)).pack(side="left", padx=15, pady=10)
                ctk.CTkButton(f, text="Delete", fg_color="#8B0000", hover_color="#5c0000", width=80,
                              command=lambda s=row['Student_ID']: self.admin_remove_student(s)).pack(side="right", padx=10)

        # 4. عرض الكورسات (زي ما هي بدون فلترة)
        for _, row in self.courses_df.iterrows():
            f = ctk.CTkFrame(self.co_list_frame, fg_color="#2b2b2b")
            f.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(f, text=f"ID: {row['Course_ID']} | {row['course_title']} (Tags: {row['Tags']})", 
                         font=("Arial", 12)).pack(side="left", padx=15, pady=10)
            ctk.CTkButton(f, text="Delete", fg_color="#8B0000", hover_color="#5c0000", width=80,
                          command=lambda c=row['Course_ID']: self.admin_remove_course(c)).pack(side="right", padx=10)

    # ----------------------- [ ACTIONS LOGIC ] -----------------------
    
    def admin_add_student(self):
        """فتح نافذة فورم لإضافة طالب بكل بياناته مع منع تكرار الـ ID"""
        add_win = ctk.CTkToplevel(self)
        add_win.title("Add New Student Form")
        add_win.geometry("450x650") # زودنا الطول شوية عشان الزرار ياخد راحته
        add_win.grab_set() 

        ctk.CTkLabel(add_win, text="Student Details", font=("Arial", 22, "bold")).pack(pady=(20, 10))

        fields = ["Student_ID", "Student_Name", "Email", "Faculty", "Department", "Academic_Level"]
        entries = {}

        for field in fields:
            frame = ctk.CTkFrame(add_win, fg_color="transparent")
            frame.pack(fill="x", padx=40, pady=8) 
            
            ctk.CTkLabel(frame, text=f"{field.replace('_', ' ')}:", width=130, anchor="w", font=("Arial", 12)).pack(side="left")
            entry = ctk.CTkEntry(frame, width=200)
            entry.pack(side="right")
            entries[field] = entry

        def save_student():
            try:
                sid_input = entries["Student_ID"].get().strip()
                sname = entries["Student_Name"].get().strip()
                email = entries["Email"].get().strip()
                faculty = entries["Faculty"].get().strip()
                dept = entries["Department"].get().strip()
                level = entries["Academic_Level"].get().strip()

                if not sid_input or not sname:
                    messagebox.showwarning("تنبيه", "يجب إدخال الـ ID والاسم!")
                    return

                existing_ids = self.students_df['Student_ID'].astype(str).values
                if sid_input in existing_ids:
                    messagebox.showerror("خطأ في الإضافة", f"الـ ID رقم ({sid_input}) موجود بالفعل!")
                    return

                sid = int(sid_input)
                new_row = {
                    'Student_ID': sid,
                    'Student_Name': sname,
                    'Email': email if email else f"{sname.lower().replace(' ','')}@college.edu",
                    'Password': str(sid),
                    'Faculty': faculty if faculty else "Engineering",
                    'Department': dept if dept else "Systems",
                    'Academic_Level': int(level) if level else 1
                }

                new_s = pd.DataFrame([new_row])
                self.students_df = pd.concat([self.students_df, new_s], ignore_index=True)
                self.students_df['Student_ID'] = pd.to_numeric(self.students_df['Student_ID'], errors='coerce').astype('Int64')
                
                self.students_df.to_csv(STUDENTS_FILE, index=False)
                self.log_activity("ADMIN", "ADD_STUDENT", f"Added ID: {sid}")
                messagebox.showinfo("نجاح", f"تم إضافة الطالب {sname} بنجاح.")
                
                self.refresh_admin_data() 
                add_win.destroy() 

            except ValueError:
                messagebox.showerror("خطأ", "يجب أن يكون الـ ID والمستوى الأكاديمي أرقاماً فقط!")
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل الحفظ: {e}")

        # >>> السطر اللي كان ناقصك عشان الزرار يظهر <<<
        ctk.CTkButton(add_win, text="Save Student Data", fg_color="#2ecc71", 
                     command=save_student, font=("Arial", 14, "bold")).pack(pady=25)
                
    def admin_remove_student(self, sid):
        """Action 2: [-] Remove Student"""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to purge records for Student ID {sid}?"):
            self.students_df = self.students_df[self.students_df['Student_ID'] != sid]
            self.students_df.to_csv(STUDENTS_FILE, index=False)
            self.log_activity("ADMIN", "REMOVE_STUDENT", f"ID: {sid}")
            self.refresh_admin_data()

    def admin_add_course(self):
        """فتح نافذة إضافة كورس جديد"""
        add_win = ctk.CTkToplevel(self)
        add_win.title("Add New Course")
        
        # كبرنا الطول لـ 650 عشان الزرار يبان مرتاح
        add_win.geometry("450x650") 
        add_win.grab_set()

        ctk.CTkLabel(add_win, text="Course Details", font=("Arial", 22, "bold")).pack(pady=15)

        fields = ["Course_ID", "course_title", "Tags", "Credit_Hours"]
        entries = {}

        for field in fields:
            frame = ctk.CTkFrame(add_win, fg_color="transparent")
            frame.pack(fill="x", padx=40, pady=5) # قللنا الـ pady هنا لـ 5 عشان نوفر مساحة
            
            ctk.CTkLabel(frame, text=f"{field.replace('_', ' ')}:", width=130, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(frame, width=200)
            entry.pack(side="right")
            entries[field] = entry

        def save_course():
            try:
                cid_input = entries["Course_ID"].get().strip()
                ctitle = entries["course_title"].get().strip()
                tags = entries["Tags"].get().strip()
                chours = entries["Credit_Hours"].get().strip()

                if not cid_input or not ctitle or not chours:
                    messagebox.showwarning("تنبيه", "برجاء ملء البيانات الأساسية!")
                    return

                # منع تكرار كود الكورس
                existing_ids = self.courses_df['Course_ID'].astype(str).values
                if cid_input in existing_ids:
                    messagebox.showerror("خطأ", f"كود الكورس ({cid_input}) موجود بالفعل!")
                    return

                new_row = {
                    'Course_ID': int(cid_input),
                    'course_title': ctitle,
                    'Tags': tags if tags else "General",
                    'Credit_Hours': int(chours)
                }

                self.courses_df = pd.concat([self.courses_df, pd.DataFrame([new_row])], ignore_index=True)
                self.courses_df['Course_ID'] = self.courses_df['Course_ID'].astype('Int64')
                self.courses_df.to_csv(COURSES_FILE, index=False)
                
                messagebox.showinfo("نجاح", f"تم إضافة كورس {ctitle} بنجاح.")
                self.refresh_admin_data()
                add_win.destroy()

            except ValueError:
                messagebox.showerror("خطأ", "الـ ID والساعات المعتمدة يجب أن تكون أرقاماً!")
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل الحفظ: {e}")

        # الزرار اهو .. تأكد إنه داخل دالة admin_add_course بس "خارج" دالة save_course
        self.save_btn = ctk.CTkButton(add_win, text="Save Course Data", 
                                     fg_color="#2ecc71", hover_color="#27ae60",
                                     command=save_course, font=("Arial", 14, "bold"))
        self.save_btn.pack(pady=40) # زودنا المسافة هنا عشان يبعد عن الحقول ويبان
        
        def save_course():
            try:
                cid_input = entries["Course_ID"].get().strip()
                ctitle = entries["course_title"].get().strip()
                tags = entries["Tags"].get().strip()
                chours = entries["Credit_Hours"].get().strip()

                # 1. التأكد من الخانات الأساسية
                if not cid_input or not ctitle or not chours:
                    messagebox.showwarning("تنبيه", "برجاء ملء البيانات الأساسية (ID, Title, Credit Hours)")
                    return

                # 2. --- التعديل الجوهري لمنع تكرار كود الكورس ---
                # سحب كل الأكواد الموجودة حالياً وتحويلها لنصوص للمقارنة الدقيقة
                existing_course_ids = self.courses_df['Course_ID'].astype(str).values
                
                if cid_input in existing_course_ids:
                    messagebox.showerror("خطأ في الإضافة", f"كود الكورس ({cid_input}) موجود بالفعل لكورس آخر!\nبرجاء استخدام كود مميز.")
                    return
                # --------------------------------------------

                # 3. تكملة عملية الحفظ
                new_row = {
                    'Course_ID': int(cid_input),
                    'course_title': ctitle,
                    'Tags': tags if tags else "General",
                    'Credit_Hours': int(chours)
                }

                new_c = pd.DataFrame([new_row])
                self.courses_df = pd.concat([self.courses_df, new_c], ignore_index=True)
                
                # تأكيد نوع البيانات وحفظ الملف
                self.courses_df['Course_ID'] = self.courses_df['Course_ID'].astype('Int64')
                self.courses_df.to_csv(COURSES_FILE, index=False)
                
                self.log_activity("ADMIN", "ADD_COURSE", f"ID: {cid_input} Title: {ctitle}")
                messagebox.showinfo("نجاح", f"تم إضافة كورس {ctitle} بنجاح.")
                
                self.refresh_admin_data()
                add_win.destroy()

            except ValueError:
                messagebox.showerror("خطأ", "الـ ID والساعات المعتمدة يجب أن تكون أرقاماً!")
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل الحفظ: {e}")
            ctk.CTkButton(add_win, text="Save Course", fg_color="#2ecc71", 
                     command=save_course, font=("Arial", 14, "bold")).pack(pady=30)
            
    def admin_remove_course(self, cid):
        """Action 4: [-] Delete Course"""
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to remove Course ID {cid}?"):
            self.courses_df = self.courses_df[self.courses_df['Course_ID'] != cid]
            self.courses_df.to_csv(COURSES_FILE, index=False)
            self.log_activity("ADMIN", "REMOVE_COURSE", f"ID: {cid}")
            self.refresh_admin_data()

    def admin_reset_pwd(self):
        """Action 5: [*] Reset Admin Pwd (Permanent Save)"""
        global ADMIN_PASSWORD
        new_p = self.new_admin_pwd_ent.get().strip()
        
        if new_p:
            try:
                # 1. الحفظ في ملف نصي لضمان الديمومة
                with open("admin_cred.txt", "w") as f:
                    f.write(new_p)
                
                # 2. تحديث المتغير العالمي عشان يشتغل في الـ Session الحالية
                ADMIN_PASSWORD = new_p
                
                self.log_activity("ADMIN", "PWD_RESET", "Password changed permanently")
                messagebox.showinfo("Success", "Admin password updated permanently!")
                self.new_admin_pwd_ent.delete(0, 'end')
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save password: {e}")
        else:
            messagebox.showwarning("Warning", "Password cannot be empty.")

# ----------------------- [ STUDENT PORTAL ] -----------------------
    def show_student_portal(self):
        self.clear_screen()
        s_name = self.current_user_data['Student_Name']
        ctk.CTkLabel(self, text=f"STUDENT PORTAL: {s_name.upper()}", font=("Arial", 20, "bold")).pack(pady=10)
        
        self.main_tab = ctk.CTkTabview(self, width=950, height=580)
        self.main_tab.pack(padx=10, pady=5, fill="both", expand=True)
        self.main_tab.add("Enrollment")
        self.main_tab.add("AI Recommendations")
        self.main_tab.add("Profile")

        # --- Enrollment Tab ---
        enroll_tab = self.main_tab.tab("Enrollment")
        
        # 1. إضافة شريط البحث (Search Bar)
        self.search_var = ctk.StringVar()
        # الدالة دي بتخلي القايمة تتحدث مع كل حرف الطالب بيكتبه
        self.search_var.trace_add("write", lambda *args: self.refresh_enrollment_list())
        
        self.search_ent = ctk.CTkEntry(enroll_tab, textvariable=self.search_var, placeholder_text="🔍 Search available courses by ID or Title...", width=400)
        self.search_ent.pack(pady=(10, 5))

        # 2. الفريم اللي فيه المواد
        self.enroll_frame = ctk.CTkScrollableFrame(enroll_tab, width=900, height=450)
        self.enroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.refresh_enrollment_list()

        # --- AI Recommendations Tab ---
        rec_frame = self.main_tab.tab("AI Recommendations")
        
        # هيدر بسيط
        ctk.CTkLabel(rec_frame, text="Smart Course Suggestions based on your history", 
                     font=("Arial", 14, "italic"), text_color="gray").pack(pady=(10, 5))
        
        ctk.CTkButton(rec_frame, text="✨ Generate My AI Recommendations", 
                      fg_color="#1f538d", hover_color="#14375e",
                      command=self.get_ai_recs).pack(pady=10)
        
        # تحويل الـ Textbox لـ ScrollableFrame لعرض الكروت
        self.rec_scroll_frame = ctk.CTkScrollableFrame(rec_frame, width=800, height=380, 
                                                      fg_color="transparent")
        self.rec_scroll_frame.pack(pady=10, fill="both", expand=True, padx=20)

        # --- Profile Tab ---
        prof_frame = self.main_tab.tab("Profile")
        self.new_email_ent = ctk.CTkEntry(prof_frame, placeholder_text="Enter New Email", width=300)
        self.new_email_ent.pack(pady=20)
        ctk.CTkButton(prof_frame, text="Update Email", command=self.update_student_email).pack()

        ctk.CTkButton(self, text="Logout", command=self.show_login_page, fg_color="red").pack(pady=10)

    def refresh_enrollment_list(self):
        # مسح المحتوى القديم عشان منع التكرار
        for w in self.enroll_frame.winfo_children(): 
            w.destroy()
        
        s_name = self.current_user_data['Student_Name']
        if os.path.exists(RATINGS_FILE):
            self.ratings_df = pd.read_csv(RATINGS_FILE)
        
        # --- [ 1. قسم المواد المسجلة ] ---
        ctk.CTkLabel(self.enroll_frame, text="--- My Registered Courses ---", 
                     text_color="#52abff", font=("Arial", 16, "bold")).pack(pady=(10, 10))
        
        history = self.ratings_df[self.ratings_df['Student_Name'] == s_name]
        taken_ids = history['Course_ID'].unique().tolist()
        
        if history.empty:
            ctk.CTkLabel(self.enroll_frame, text="No courses registered yet.", text_color="gray").pack(pady=5)
        else:
            for _, row in history.iterrows():
                f = ctk.CTkFrame(self.enroll_frame, fg_color="#2b2b2b")
                f.pack(fill="x", pady=3, padx=10)
                
                course_info = self.courses_df[self.courses_df['Course_ID'] == row['Course_ID']]
                title = course_info.iloc[0]['course_title'] if not course_info.empty else "Unknown"
                
                ctk.CTkLabel(f, text=f"ID: {row['Course_ID']} | {title} | Rating: {row['Rating']}", 
                             font=("Arial", 12)).pack(side="left", padx=15, pady=10)
                
                ctk.CTkButton(f, text="Unenroll", width=80, fg_color="#8B0000", hover_color="#5c0000",
                              command=lambda c=row['Course_ID']: self.unenroll_from_course(c)).pack(side="right", padx=10)
                ctk.CTkButton(f, text="Rate", width=80, 
                              command=lambda c=row['Course_ID']: self.rate_course(c)).pack(side="right", padx=5)

        # --- [ 2. قسم المواد المتاحة مع السيرش ] ---
        ctk.CTkLabel(self.enroll_frame, text="--- Available Courses ---", 
                     text_color="#2ecc71", font=("Arial", 16, "bold")).pack(pady=(30, 10))
        
        available = self.courses_df[~self.courses_df['Course_ID'].isin(taken_ids)]
        
        # تطبيق نظام الفلترة (السيرش)
        search_query = self.search_var.get().strip().lower()
        if search_query:
            # بيفلتر سواء كتبت اسم المادة أو الـ ID بتاعها
            available = available[
                available['course_title'].str.lower().str.contains(search_query) | 
                available['Course_ID'].astype(str).str.contains(search_query)
            ]
        
        if available.empty:
            if search_query:
                ctk.CTkLabel(self.enroll_frame, text="No courses match your search.", text_color="gray").pack(pady=5)
            else:
                ctk.CTkLabel(self.enroll_frame, text="All courses are registered!", text_color="gray").pack(pady=5)
        else:
            for _, row in available.iterrows():
                f = ctk.CTkFrame(self.enroll_frame)
                f.pack(fill="x", pady=2, padx=10)
                ctk.CTkLabel(f, text=f"{row['Course_ID']} - {row['course_title']}", 
                             font=("Arial", 12)).pack(side="left", padx=15, pady=8)
                ctk.CTkButton(f, text="Enroll", width=80, 
                              command=lambda cid=row['Course_ID']: self.enroll_in_course(cid)).pack(side="right", padx=10)

    def enroll_in_course(self, cid):
        s_name = self.current_user_data['Student_Name']
        prereq_id = cid - 1
        history = self.ratings_df[self.ratings_df['Student_Name'] == s_name]
        taken_ids = history['Course_ID'].unique().tolist()
        
        if prereq_id in self.courses_df['Course_ID'].values and prereq_id not in taken_ids:
            messagebox.showerror("Prerequisite Error", f"You must finish course {prereq_id} first!")
            return
        
        new_row = {'Student_Name': s_name, 'Course_ID': cid, 'Rating': 0.0}
        self.ratings_df = pd.concat([self.ratings_df, pd.DataFrame([new_row])], ignore_index=True)
        
        # === السر كله هنا: ترتيب الداتا بيز باسم الطالب قبل ما نسيف ===
        # ده هيضمن إن كل مواد الطالب ده تتجمع تحت بعضها في ملف الـ csv
        self.ratings_df.sort_values(by=['Student_Name', 'Course_ID'], inplace=True)
        
        self.ratings_df.to_csv(RATINGS_FILE, index=False)
        messagebox.showinfo("Success", "Enrolled!")
        self.refresh_enrollment_list()

    # --- [ دالة حذف المادة وإلغاء التسجيل ] ---
    # --- [ دالة حذف المادة وإلغاء التسجيل ] ---
    def unenroll_from_course(self, cid):
        s_name = self.current_user_data['Student_Name']
        
        # التأكد من أن المادة لم يتم تقييمها مسبقاً (لو التقييم أكبر من 0 يعني خلصت)
        course_record = self.ratings_df[(self.ratings_df['Student_Name'] == s_name) & (self.ratings_df['Course_ID'] == cid)]
        if not course_record.empty and float(course_record.iloc[0]['Rating']) > 0.0:
            messagebox.showerror("Error", "Cannot unenroll! You have already rated and completed this course.")
            return

        if messagebox.askyesno("Confirm Unenroll", f"Are you sure you want to drop course ID {cid}?"):
            self.ratings_df = self.ratings_df[~((self.ratings_df['Student_Name'] == s_name) & (self.ratings_df['Course_ID'] == cid))]
            self.ratings_df.to_csv(RATINGS_FILE, index=False)
            messagebox.showinfo("Success", "Course Unenrolled Successfully!")
            self.refresh_enrollment_list()

    # --- [ دالة تقييم المادة ] ---
    def rate_course(self, cid):
        s_name = self.current_user_data['Student_Name']
        
        # التأكد من أن المادة لم يتم تقييمها مسبقاً
        course_record = self.ratings_df[(self.ratings_df['Student_Name'] == s_name) & (self.ratings_df['Course_ID'] == cid)]
        if not course_record.empty and float(course_record.iloc[0]['Rating']) > 0.0:
            messagebox.showerror("Error", "You have already rated this course! Ratings cannot be changed.")
            return

        dialog = ctk.CTkInputDialog(text="Enter Rating (from 1.0 to 5.0):", title="Rate Course")
        val = dialog.get_input()
        
        if val is not None:  # لو المستخدم داس Cancel مش هيعمل حاجة
            val = val.strip()
            if not val:
                return
            
            try:
                r = float(val)
                # شرط صارم: التقييم من 1 لـ 5 وممنوع الصفر أو السوالب
                if 1.0 <= r <= 5.0:
                    mask = (self.ratings_df['Student_Name'] == s_name) & (self.ratings_df['Course_ID'] == cid)
                    self.ratings_df.loc[mask, 'Rating'] = r
                    self.ratings_df.to_csv(RATINGS_FILE, index=False)
                    messagebox.showinfo("Success", "Course Rated Successfully!")
                    self.refresh_enrollment_list()
                else:
                    messagebox.showerror("Error", "Invalid Rating! Please enter a number between 1.0 and 5.0 (0 is not allowed).")
            except ValueError:
                messagebox.showerror("Error", "Invalid format! Please enter a valid number.")

    # --- [ دالة تقييم المادة ] ---
    def rate_course(self, cid):
        s_name = self.current_user_data['Student_Name']
        dialog = ctk.CTkInputDialog(text="Enter Rating (from 1.0 to 5.0):", title="Rate Course")
        val = dialog.get_input()
        if val:
            try:
                r = float(val)
                if 1.0 <= r <= 5.0:
                    mask = (self.ratings_df['Student_Name'] == s_name) & (self.ratings_df['Course_ID'] == cid)
                    self.ratings_df.loc[mask, 'Rating'] = r
                    self.ratings_df.to_csv(RATINGS_FILE, index=False)
                    messagebox.showinfo("Success", "Course Rated Successfully!")
                    self.refresh_enrollment_list()
                else:
                    messagebox.showerror("Error", "Rating must be between 1 and 5.")
            except ValueError:
                messagebox.showerror("Error", "Invalid number format!")

    def get_ai_recs(self):
        s_name = self.current_user_data['Student_Name']
        recommender = CourseRecommender(self.students_df, self.courses_df, self.ratings_df)
        recs = recommender.get_recommendations(s_name)
        
        # مسح التوصيات القديمة
        for w in self.rec_scroll_frame.winfo_children():
            w.destroy()
            
        if not recs:
            ctk.CTkLabel(self.rec_scroll_frame, text="No recommendations found yet. Try rating more courses!").pack(pady=20)
            return

        # عرض الكروت
        for i, r in enumerate(recs, 1):
            # إنشاء كارت لكل كورس
            card = ctk.CTkFrame(self.rec_scroll_frame, corner_radius=10)
            card.pack(fill="x", pady=5, padx=5)
            
            # استخراج البيانات (سواء كانت Dictionary أو String)
            if isinstance(r, dict):
                title = r.get('Title', 'Unknown Course')
                conf = r.get('Confidence', 'N/A')
            else:
                # محاولة فصل الاسم عن النسبة لو راجعين كـ String واحد
                title = r
                conf = ""

            # رقم الترتيب
            ctk.CTkLabel(card, text=f"#{i}", font=("Arial", 16, "bold"), text_color="#1f6aa5").pack(side="left", padx=15)
            
            # اسم الكورس
            info_label = ctk.CTkLabel(card, text=title, font=("Arial", 13, "bold"), anchor="w")
            info_label.pack(side="left", fill="x", expand=True, padx=10, pady=12)
            
            # نسبة التأكد (Confidence) بشكل جمالي
            if conf:
                conf_frame = ctk.CTkFrame(card, fg_color="#2d5a27", corner_radius=6)
                conf_frame.pack(side="right", padx=15)
                ctk.CTkLabel(conf_frame, text=f"Confidence: {conf}", font=("Arial", 11), text_color="white").pack(padx=8, pady=2)

    def update_student_email(self):
        new_email = self.new_email_ent.get().strip()
        allowed = ('@gmail.com', '@uni.edu.eg')
        if not new_email.lower().endswith(allowed):
            messagebox.showerror("Error", "Invalid Domain!")
            return
        
        sid = str(self.current_user_data['Student_ID'])
        exists = self.students_df[(self.students_df['Email'] == new_email.lower()) & (self.students_df['Student_ID'].astype(str) != sid)]
        if not exists.empty:
            messagebox.showerror("Error", "Email taken!")
            return
            
        self.students_df.loc[self.students_df['Student_ID'].astype(str) == sid, 'Email'] = new_email.lower()
        self.students_df.to_csv(STUDENTS_FILE, index=False)
        messagebox.showinfo("Success", "Email Updated")

if __name__ == "__main__":
    app = UniversityGUI()
    app.mainloop()