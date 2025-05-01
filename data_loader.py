import pandas as pd
import streamlit as st
from database import db_session, Rating

@st.cache_data
def load_and_preprocess():
    # Load course data
    coursera = pd.read_csv('courserafin.csv')
    udemy = pd.read_csv('udemyfin.csv')

    # Standardize Coursera data
    coursera = coursera.rename(columns={
        'Course Name': 'title',
        'Course Rating': 'rating',
        'Course Description': 'description',
        'Difficulty Level': 'level',
        'Course URL': 'url',
        'Skills': 'skills'
    })

    # Standardize Udemy data
    udemy = udemy.rename(columns={
        'course_name': 'title',
        'reviews_avg': 'rating',
        'course_description': 'description',
        'course_url': 'url',
        'course_duration': 'duration',
        'students_count': 'enrollments'
    })

    # Create unique course IDs
    coursera['course_id'] = ['C' + str(i) for i in range(1000, 1000 + len(coursera))]
    udemy['course_id'] = ['U' + str(i) for i in range(2000, 2000 + len(udemy))]

    # Combine datasets
    combined = pd.concat([
        coursera[['course_id', 'title', 'description', 'level', 'rating', 'url', 'skills']],
        udemy[['course_id', 'title', 'description', 'level', 'rating', 'url', 'duration']]
    ], ignore_index=True)

    # Clean data
    combined = combined.dropna(subset=['title'])
    combined['description'] = combined['description'].fillna('').str.lower()
    combined['rating'] = pd.to_numeric(combined['rating'], errors='coerce').fillna(3.5)
    combined['level'] = combined['level'].fillna('Intermediate').str.title()

    # Load ratings from database
    ratings_query = db_session.query(Rating).all()
    user_ratings = pd.DataFrame([(r.user_id, r.course_id, r.rating) for r in ratings_query],
                               columns=['user_id', 'course_id', 'rating'])

    return combined, user_ratings