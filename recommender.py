import pandas as pd
from surprise import Dataset, Reader, SVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class HybridRecommender:
    def __init__(self, data, user_ratings):
        self.data = data
        self.user_ratings = user_ratings
        self.cf_model = None
        self.tfidf_vectorizer = None
        self.cosine_sim = None
        self.indices = None

    def train_collaborative_filtering(self):
        if not self.user_ratings.empty:
            reader = Reader(rating_scale=(1, 5))
            data = Dataset.load_from_df(self.user_ratings, reader)
            trainset = data.build_full_trainset()
            self.cf_model = SVD(n_factors=20, n_epochs=25, lr_all=0.007, reg_all=0.1)
            self.cf_model.fit(trainset)

    def train_content_based(self):
        self.data['content'] = self.data['title'] + ' ' + self.data['description'] + ' ' + self.data['level']
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_features=5000
        )
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.data['content'])
        self.cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        self.indices = pd.Series(self.data.index, index=self.data['course_id']).drop_duplicates()

    def get_content_based_recommendations(self, course_id, top_n=10):
        try:
            idx = self.indices[course_id]
        except KeyError:
            return pd.DataFrame()

        sim_scores = list(enumerate(self.cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:top_n+1]
        course_indices = [i[0] for i in sim_scores]
        similarities = [i[1] for i in sim_scores]
        recommendations = self.data.iloc[course_indices].copy()
        recommendations['similarity'] = similarities
        return recommendations

    def get_hybrid_recommendations(self, user_id, course_id, top_n=10, alpha=0.5):
        content_recs = self.get_content_based_recommendations(course_id, top_n*3)
        if content_recs.empty:
            return pd.DataFrame()

        cf_available = not self.user_ratings.empty and (user_id in self.user_ratings['user_id'].values)
        recommendations = []
        for _, row in content_recs.iterrows():
            hybrid_score = 0
            content_score = row['similarity']
            cf_score = 0
            if cf_available:
                try:
                    pred = self.cf_model.predict(user_id, row['course_id'])
                    cf_score = pred.est / 5
                except Exception:
                    pass

            if cf_available and cf_score > 0:
                hybrid_score = (alpha * cf_score) + ((1 - alpha) * content_score)
            else:
                hybrid_score = content_score

            recommendations.append({
                'course_id': row['course_id'],
                'title': row['title'],
                'description': row.get('description', ''),  # ✅ Add the course description
                'hybrid_score': hybrid_score,
                'content_score': content_score,
                'cf_score': cf_score * 5 if cf_available else 'N/A',
                'rating': row['rating'],
                'url': row['url'],
                'type': 'Coursera' if row['course_id'].startswith('C') else 'Udemy'
            })

        return pd.DataFrame(recommendations).sort_values('hybrid_score', ascending=False).head(top_n)