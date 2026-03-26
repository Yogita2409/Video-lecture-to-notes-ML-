from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Improved training data (more realistic)
texts = [
    "machine learning models training dataset neural networks deep learning",
    "sql database queries joins tables indexing data storage",
    "python programming loops functions variables coding development",
    "mean median variance probability statistics data analysis",
    "classification regression supervised learning algorithms model",
    "data visualization charts graphs dashboard power bi matplotlib",
    "html css javascript frontend web development website design",
    "big data hadoop spark distributed data processing engineering"
]

labels = [
    "Machine Learning",
    "Database",
    "Programming",
    "Statistics",
    "Machine Learning",
    "Data Visualization",
    "Web Development",
    "Big Data"
]

# Vectorization
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

# Model
model = LogisticRegression()
model.fit(X, labels)

# Prediction function
def predict_topic(text):
    X_test = vectorizer.transform([text])
    return model.predict(X_test)[0]