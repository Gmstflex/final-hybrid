import streamlit as st
import streamlit.components.v1 as components
from database import (
    db_session, User, Rating, save_course, unsave_course,
    get_saved_courses, add_viewed_course, get_viewed_courses
)
from auth import create_user, authenticate_user, update_password
from data_loader import load_and_preprocess
from recommender import HybridRecommender
from ui_components import show_login_signup, show_admin_dashboard, forgot_password_flow

def main():
    st.set_page_config(page_title="Course Recommender", layout="wide", page_icon="🎓")
    
    # Custom CSS
    st.markdown("""
    <style>
        .course-card {
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            margin: 15px 0;
            transition: transform 0.2s;
            background: white;
        }
        .course-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .badge {
            padding: 4px 8px;
            border-radius: 15px;
            font-size: 0.8em;
            display: inline-block;
            margin: 5px 5px 5px 0;
        }
        .header-accent {
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 8px;
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: #4CAF50;
        }
        .stSlider div[data-baseweb="slider"] {
            margin: 10px 0;
        }
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

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        show_login_signup()
        return
    
    # Load data ONCE
    data, user_ratings = load_and_preprocess()
    
    # Check admin status IMMEDIATELY after login
    if st.session_state.role == "admin":
        show_admin_dashboard(data, db_session)
        return  # Proper exit for admin
    
    recommender = HybridRecommender(data, user_ratings)
    recommender.train_content_based()
    recommender.train_collaborative_filtering()

    # Session state initialization
    if 'show_recommendations' not in st.session_state:
        st.session_state.show_recommendations = False
    if 'current_recommendations' not in st.session_state:
        st.session_state.current_recommendations = None
    if 'current_search' not in st.session_state:
        st.session_state.current_search = {'search_term': '', 'selected_course': ''}

    # Sidebar
    st.sidebar.header("🔍 Course Search")
    if st.session_state.role == "admin":
        users = db_session.query(User).all()
        selected_user = st.sidebar.selectbox("👥 Select User", [u.username for u in users])
        user_id = [u.id for u in users if u.username == selected_user][0]
    else:
        user_id = st.session_state.user_id
        st.sidebar.markdown(f"**👤 User:** {st.session_state.username}")
    
    search_term = st.sidebar.text_input("🔎 Search Courses", help="Search by course title or keywords")
    filtered = data[data['title'].str.contains(search_term, case=False)] if search_term else data.sample(10)
    selected_course = st.sidebar.selectbox("📚 Select Course", filtered['title'])
    course_id = filtered[filtered['title'] == selected_course]['course_id'].values[0]

    # Search state management
    if (search_term != st.session_state.current_search['search_term'] or
        selected_course != st.session_state.current_search['selected_course']):
        st.session_state.show_recommendations = False
        st.session_state.current_recommendations = None
        st.session_state.current_search = {'search_term': search_term, 'selected_course': selected_course}

    # Main interface
    if st.session_state.show_recommendations:
        st.markdown(f"<h2 class='header-accent'>🚀 Recommendations for: {selected_course}</h2>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='color: #2b5876;'>🎓 Smart Course Recommender</h1>", unsafe_allow_html=True)
        st.markdown("### Welcome to your personalized learning companion! 🌟")

    # Generate recommendations
    if st.sidebar.button("✨ Generate Recommendations", use_container_width=True):
        add_viewed_course(user_id, course_id)
        st.session_state.show_recommendations = True
        st.session_state.current_recommendations = recommender.get_hybrid_recommendations(user_id, course_id)
        st.session_state.current_search = {'search_term': search_term, 'selected_course': selected_course}

    # Display recommendations
    if (st.session_state.show_recommendations and 
        st.session_state.current_recommendations is not None and
        search_term == st.session_state.current_search['search_term'] and
        selected_course == st.session_state.current_search['selected_course']):
        
        cols = st.columns(2)
        recs = st.session_state.current_recommendations
        
        for idx, row in recs.iterrows():
            with cols[idx%2]:
                course_id = f"desc_{idx}"  # Unique ID for each course

                components.html(f"""
                    <div style="border: 1px solid #e0e0e0; border-radius: 12px; padding: 20px; margin-bottom: 20px; 
                                box-shadow: 0 4px 10px rgba(0,0,0,0.08); background: #fff; transition: transform 0.3s;" 
                        onmouseover="this.style.transform='scale(1.02)'" 
                        onmouseout="this.style.transform='scale(1)'">
                        
                        <h3 style='margin-top:0; color: #2b5876; font-size: 20px;'>{row['title']}</h3>
                        
                        <div style='margin-bottom:10px;'>
                            <span class='badge' style='background: {'#0056d2' if row['type'] == 'Coursera' else '#a435f0'}; color: white; padding:5px 10px; border-radius: 8px; font-size:12px;'>
                                {row['type']} {'📚' if row['type'] == 'Coursera' else '🎥'}
                            </span>
                            <span class='badge' style='background: #4CAF50; color: white; padding:5px 10px; border-radius: 8px; font-size:12px;'>
                                ⭐ {row['rating']:.1f}/5.0
                            </span>
                        </div>

                        <div style='margin-bottom:15px;'>
                            <div class='progress-bar' style='background:#f0f0f0; border-radius:8px; height:8px;'>
                                <div class='progress-fill' style='background:linear-gradient(to right, #4CAF50, #81C784); height:8px; border-radius:8px; width: {row['hybrid_score']*100}%'></div>
                            </div>
                            <small style='color:#666;'>Recommendation Strength: {row['hybrid_score']:.2f}/1.0</small>
                        </div>

                        <div style='margin-bottom:15px; font-size: 13px; color: #555;'>
                            <span id="{course_id}_short">{row['description'][:200]}...</span>
                            <span id="{course_id}_full" style="display:none;">{row['description']}</span>
                            <br>
                            <a href="javascript:void(0);" id="{course_id}_toggle" onclick="toggleDescription('{course_id}');" style="color:#4CAF50; text-decoration:none; font-size:13px;">Read more</a>
                        </div>

                        <div style='text-align:center;'>
                            <a href='{row['url']}' target='_blank' 
                            style='display:inline-block; padding:10px 20px; background:#4CAF50; color:white; 
                                    border-radius:8px; text-decoration:none; font-weight:bold; font-size:14px; 
                                    transition: background 0.3s;'>
                                🚀 View Course
                            </a>
                        </div>

                        <script>
                            function toggleDescription(id) {{
                                var shortDesc = document.getElementById(id + "_short");
                                var fullDesc = document.getElementById(id + "_full");
                                var toggleLink = document.getElementById(id + "_toggle");

                                if (shortDesc.style.display === "none") {{
                                    shortDesc.style.display = "inline";
                                    fullDesc.style.display = "none";
                                    toggleLink.innerHTML = "Read more";
                                }} else {{
                                    shortDesc.style.display = "none";
                                    fullDesc.style.display = "inline";
                                    toggleLink.innerHTML = "Show less";
                                }}
                            }}
                        </script>

                    </div>
                """, height=300)

            # Add save/unsave button
                course_id = row['course_id']
                is_saved = course_id in get_saved_courses(user_id)
                btn_text = "💾 Save for Later" if not is_saved else "❌ Remove from Saved"
                if st.button(btn_text, key=f"save_{user_id}_{course_id}"):
                    if is_saved:
                        unsave_course(user_id, course_id)
                    else:
                        save_course(user_id, course_id)
                    st.rerun()


                # Rating slider
                course_id = row['course_id']
                unique_key = f"rating_{user_id}_{course_id}"
                state_key = f"prev_rating_{user_id}_{course_id}"
                
                # Check existing rating
                existing_rating = db_session.query(Rating).filter_by(
                    user_id=user_id,
                    course_id=course_id
                ).first()
                
                # Initialize session state
                if state_key not in st.session_state:
                    st.session_state[state_key] = existing_rating.rating if existing_rating else 0
                
                # Create slider with persistent state
                current_rating = st.slider(
                    "Rate this course (0 = not rated)",
                    0, 5,
                    value=st.session_state[state_key],
                    key=unique_key,
                    format="%d ⭐"
                )
                
                # Handle rating changes
                if current_rating != st.session_state[state_key]:
                    try:
                        if current_rating == 0:
                            if existing_rating:
                                db_session.delete(existing_rating)
                        else:
                            if existing_rating:
                                existing_rating.rating = current_rating
                            else:
                                db_session.add(Rating(
                                    user_id=user_id,
                                    course_id=course_id,
                                    rating=current_rating
                                ))
                        db_session.commit()
                        st.session_state[state_key] = current_rating
                        st.success("✅ Rating saved successfully!")
                    except Exception as e:
                        st.error(f"❌ Error saving rating: {str(e)}")
                        db_session.rollback()

                # Admin debug info
                if st.session_state.role == "admin":
                    with st.expander("📊 Recommendation Details"):
                        col1, col2 = st.columns(2)
                        col1.metric("Content Similarity", f"{row['content_score']:.2f}")
                        col2.metric("CF Prediction", 
                                  f"{row['cf_score'] if isinstance(row['cf_score'], str) else row['cf_score']:.1f}/5.0",
                                  help="Collaborative Filtering Score")
    # Add spacing
    st.sidebar.markdown("---")
    st.sidebar.subheader("📚 Your Learning Hub")

    # Saved Courses Section
    with st.sidebar.expander("⭐ Saved Courses", expanded=True):
        saved_course_ids = get_saved_courses(user_id)
        saved_courses = data[data['course_id'].isin(saved_course_ids)]
        if not saved_courses.empty:
            for _, row in saved_courses.iterrows():
                course_id = row['course_id']
                platform = 'Coursera' if course_id.startswith('C') else 'Udemy'
                
                # Create columns for course info and remove button
                col1, col2 = st.columns([0.85, 0.15])
                
                with col1:
                    # Course info with link
                    st.markdown(f"""
                        <div style="padding: 10px; border-radius: 8px; background: #f8f9fa; margin: 5px 0;
                                    transition: all 0.2s ease;">
                            <a href="{row['url']}" target="_blank" 
                            style="text-decoration: none; color: #2b5876;
                                    display: block; height: 100%; width: 100%;">
                                <div style="font-weight: 500;">{row['title']}</div>
                                <small style="color: #666;">
                                    {platform}
                                    <span style="float: right;">⭐ {row['rating']:.1f}</span>
                                </small>
                            </a>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Remove button with 'x' symbol
                    if st.button("×", 
                                key=f"unsave_{user_id}_{course_id}",
                                help="Remove from saved courses"):
                        unsave_course(user_id, course_id)
                        st.rerun()  # Force immediate update of the list
        else:
            st.info("No saved courses yet")

    # Viewed History Section
    with st.sidebar.expander("👀 Recently Viewed", expanded=True):
        viewed_course_ids = get_viewed_courses(user_id)
        viewed_courses = data[data['course_id'].isin(viewed_course_ids)]
        if not viewed_courses.empty:
            for _, row in viewed_courses.iterrows():
                st.markdown(f"""
                    <div style="padding: 10px; border-radius: 8px; background: #f8f9fa; margin: 5px 0;">
                        <div style="font-weight: 500;">{row['title']}</div>
                        <small>{'Coursera' if row['course_id'].startswith('C') else 'Udemy'}</small>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No viewing history yet")

    # Logout handling
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

if __name__ == "__main__":
    main()