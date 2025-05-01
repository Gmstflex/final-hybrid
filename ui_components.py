import streamlit as st
import random
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from database import (
    db_session, User, Rating, SavedCourse, 
    SavedCourseActivity, ViewedCourse, func
)
from auth import create_user, authenticate_user, update_password

def forgot_password_flow():
    st.subheader("🔒 Forgot Password")
    if "reset_requested" not in st.session_state:
        with st.form("forgot_password_form"):
            email = st.text_input("Enter your email address:")
            if st.form_submit_button("Send Reset Code"):
                user = db_session.query(User).filter_by(email=email).first()
                if user:
                    reset_code = str(random.randint(100000, 999999))
                    st.session_state.reset_requested = True
                    st.session_state.reset_code = reset_code
                    st.session_state.reset_email = email
                    st.success(f"📧 Simulated reset code sent: {reset_code}")
                else:
                    st.error("❌ Email not found")

    if "reset_requested" in st.session_state:
        with st.form("reset_password_form"):
            code = st.text_input("Reset Code")
            new_pass = st.text_input("New Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Reset Password"):
                if new_pass != confirm_pass:
                    st.error("🔒 Passwords don't match")
                elif code != st.session_state.reset_code:
                    st.error("❌ Invalid code")
                else:
                    update_password(st.session_state.reset_email, new_pass)
                    st.success("✅ Password updated!")
                    del st.session_state.reset_requested

def show_login_signup():
    if 'failed_attempts' not in st.session_state:
        st.session_state.failed_attempts = 0
    
    if st.session_state.failed_attempts >= 5:
        st.error("""
        🚫 Too many failed attempts! 
        Please try again later or contact support.
        """)
        st.stop()

    with st.container():
        col1, col2, col3 = st.columns([1,3,1])
        with col2:
            st.markdown("<h1 style='text-align: center; color: #2b5876;'>🎓 Smart Course Recommender</h1>", unsafe_allow_html=True)
            st.markdown("<div style='text-align: center; margin-bottom: 30px; color: #4e4376;'>Your Personalized Learning Journey Starts Here</div>", unsafe_allow_html=True)
            
            mode = st.selectbox("Choose Action", ["Login", "Sign Up"], key="auth_mode")

            if mode == "Login":
                with st.form("Login"):
                    user = st.text_input("Username", key="login_user")
                    pwd = st.text_input("Password", type="password", key="login_pwd")
                    if st.form_submit_button("🔑 Login"):
                        # Validate required fields
                        if not user.strip() or not pwd.strip():
                            st.error("❌ Both username and password are required!")
                            st.session_state.failed_attempts += 1
                        else:
                            auth_user = authenticate_user(user, pwd)
                            if auth_user:
                                st.session_state.failed_attempts = 0
                                st.session_state.update({
                                    "logged_in": True,
                                    "user_id": auth_user.id,
                                    "username": auth_user.username,
                                    "role": auth_user.role
                                })
                                st.rerun()
                            else:
                                st.session_state.failed_attempts += 1
                                remaining = 5 - st.session_state.failed_attempts
                                st.error(f"❌ Invalid credentials | Remaining attempts: {remaining}")
                
                st.button("🔓 Forgot Password?", on_click=lambda: st.session_state.update({"show_forgot": True}))
            
            else:  # Sign Up mode
                with st.form("Sign Up"):
                    new_user = st.text_input("New Username", key="signup_user")
                    email = st.text_input("Email", key="signup_email")
                    new_pwd = st.text_input("New Password", type="password", key="signup_pwd")
                    if st.form_submit_button("📝 Create Account"):
                        # Validate all required fields
                        if not new_user.strip() or not email.strip() or not new_pwd.strip():
                            st.error("❌ All fields are required!")
                            st.session_state.failed_attempts += 1
                            remaining = 5 - st.session_state.failed_attempts
                            st.error(f"Remaining attempts: {remaining}")
                        else:
                            if create_user(new_user, email, new_pwd):
                                st.session_state.failed_attempts = 0
                                st.success("✅ Account created! Please login")
                            else:
                                st.session_state.failed_attempts += 1
                                remaining = 5 - st.session_state.failed_attempts
                                st.error(f"❌ Username/email exists | Remaining attempts: {remaining}")

# -------------------------
# ADMIN DASHBOARD FUNCTIONS
# -------------------------
def show_admin_dashboard(data, db_session):
    # Admin-specific CSS
    st.markdown("""
    <style>
        .metric-box {
            padding: 20px;
            border-radius: 10px;
            background: #f8f9fa;
            margin: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .metric-box:hover {
            transform: translateY(-2px);
        }
        .admin-table {
            padding: 15px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 10px 0;
        }
        .viewed-course {
            padding: 12px;
            margin: 8px 0;
            border-left: 4px solid #4CAF50;
            background: #f8fff9;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("🎓 Admin Dashboard")
    
    # Real-time Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_users = db_session.query(User).count()
        st.markdown(f'<div class="metric-box"><h3>👥 Total Users</h3><h2>{total_users}</h2></div>', 
                    unsafe_allow_html=True)
    with col2:
        total_courses = len(data)
        st.markdown(f'<div class="metric-box"><h3>📚 Total Courses</h3><h2>{total_courses}</h2></div>', 
                    unsafe_allow_html=True)
    with col3:
        total_ratings = db_session.query(Rating).count()
        st.markdown(f'<div class="metric-box"><h3>⭐ Total Ratings</h3><h2>{total_ratings}</h2></div>', 
                    unsafe_allow_html=True)
    with col4:
        active_users = db_session.query(ViewedCourse.user_id).filter(
            ViewedCourse.viewed_at >= datetime.now() - timedelta(days=30)
        ).distinct().count()
        st.markdown(f'<div class="metric-box"><h3>👤 Active Users</h3><h2>{active_users}</h2></div>', 
                    unsafe_allow_html=True)

    # Dashboard Tabs
    tab1, tab2, tab3 = st.tabs(["👥 User Management", "📊 Course Analytics", "🕒 Recent Activity"])

    with tab1:
        st.subheader("User Management")
        users = db_session.query(User).order_by(User.created_at.desc()).all()
        
        for user in users:
            with st.container():
                st.markdown('<div class="admin-table">', unsafe_allow_html=True)
                cols = st.columns([2, 2, 2, 1.5, 1])
                
                with cols[0]:
                    st.markdown(f"**{user.username}**")
                    st.caption(f"Joined: {user.created_at.strftime('%Y-%m-%d')}")
                
                with cols[1]:
                    st.text_input("Email", value=user.email, key=f"email_{user.id}", disabled=True)
                
                with cols[2]:
                    new_role = st.selectbox(
                        "Role",
                        ["user", "admin"],
                        index=0 if user.role == "user" else 1,
                        key=f"role_{user.id}"
                    )
                
                with cols[3]:
                    if st.button("🔄 Update Role", key=f"update_{user.id}"):
                        user.role = new_role
                        db_session.commit()
                        st.success("Role updated!")
                
                with cols[4]:
                    if st.button("🗑️ Delete", key=f"delete_{user.id}", 
                               disabled=user.id == st.session_state.user_id):
                        db_session.query(Rating).filter_by(user_id=user.id).delete()
                        db_session.query(SavedCourse).filter_by(user_id=user.id).delete()
                        db_session.query(ViewedCourse).filter_by(user_id=user.id).delete()
                        db_session.delete(user)
                        db_session.commit()
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.subheader("Course Analytics")
        
        # Course Ratings Distribution
        st.markdown("### 📈 Rating Distribution")
        rating_dist = data['rating'].value_counts().sort_index()
        st.bar_chart(rating_dist)
        
        # Course Levels Pie Chart
        st.markdown("### 🎚️ Difficulty Levels")
        level_dist = data['level'].value_counts()
        fig = px.pie(level_dist, 
                    names=level_dist.index, 
                    values=level_dist.values,
                    hole=0.3,
                    color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig, use_container_width=True)
        
        # Most Viewed Courses
        st.markdown("### 👀 Top Viewed Courses")
        viewed_courses = db_session.query(
        ViewedCourse.course_id,
        func.count(ViewedCourse.id).label('views')  # Count all view instances
        ).group_by(ViewedCourse.course_id).order_by(func.count(ViewedCourse.id).desc()).limit(10).all()
        
        if viewed_courses:
            viewed_df = pd.DataFrame(viewed_courses, columns=['course_id', 'views'])
            viewed_df = viewed_df.merge(data, on='course_id')
            viewed_df = viewed_df[['title', 'views', 'rating', 'level']]
            st.dataframe(
                viewed_df.style.format({'rating': '{:.1f}'})
                          .background_gradient(subset=['views'], cmap='Blues'),
                use_container_width=True
            )
        else:
            st.info("No course views recorded yet")

    with tab3:
        st.subheader("Recent Activity")
        # Get combined activity
        recent_views = db_session.query(ViewedCourse).order_by(ViewedCourse.viewed_at.desc()).limit(15).all()
        recent_saves = db_session.query(SavedCourseActivity).order_by(SavedCourseActivity.timestamp.desc()).limit(15).all()
        
        # Create combined timeline
        combined = []
        for v in recent_views:
            combined.append(('viewed', v.user_id, v.course_id, v.viewed_at))
        for s in recent_saves:
            combined.append((s.action, s.user_id, s.course_id, s.timestamp))
        
        # Sort by timestamp
        combined.sort(key=lambda x: x[3], reverse=True)
        
        # Display items
        for item in combined[:15]:  # Show last 15 items
            action_type, user_id, course_id, timestamp = item
            user = db_session.query(User).get(user_id)
            course = data[data['course_id'] == course_id].iloc[0]
            
            if action_type == 'viewed':
                icon = '👀 Viewed'
                action_text = f" {course['title']}"
            elif action_type == 'saved':
                icon = '⭐ Saved'
                action_text = f" {course['title']}"
            else:
                icon = '❌ Removed'
                action_text = f" {course['title']} from saved"
            
            st.markdown(f"""
                <div class="admin-table">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 500; color: #2b5876;">{user.username}</div>
                            <div style="font-size: 0.9em;">
                                {icon} <a href="{course['url']}" target="_blank">{action_text}</a>
                            </div>
                        </div>
                        <div style="font-size: 0.8em; color: #666;">
                            {timestamp.strftime('%Y-%m-%d %H:%M')}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Admin Tools Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("🛠️ Admin Tools")
    if st.sidebar.button("📊 Export User Data"):
        users = db_session.query(User).all()
        users_data = [{
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "join_date": u.created_at
        } for u in users]
        pd.DataFrame(users_data).to_csv("users_export.csv")
        st.sidebar.success("Data exported to users_export.csv")

    if st.sidebar.button("🧹 Reset Data"):
        # Delete ratings
        db_session.query(Rating).delete()
        
        # Clear activity-related tables
        db_session.query(SavedCourseActivity).delete()
        db_session.query(ViewedCourse).delete()
        
        # Optional: Clear saved courses if desired
        # db_session.query(SavedCourse).delete()
        
        db_session.commit()
        st.sidebar.success("All ratings and activity data cleared")

    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()