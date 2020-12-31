# Created on Nov 10 2019
# @author: 임일
# DL 추천 3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.utils import shuffle

from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Embedding, Flatten, Dense, Concatenate
from tensorflow.keras.layers import Dropout, Activation
from tensorflow.keras.regularizers import l2
from tensorflow.keras.optimizers import SGD, Adam, Adamax

# csv 파일에서 불러오기
u_cols = ['user_id', 'age', 'sex', 'occupation', 'zip_code']
users = pd.read_csv('C:/RecoSys/Data/u.user', sep='|', names=u_cols, encoding='latin-1')
users = users[['user_id', 'age']]

i_cols = ['movie_id', 'title', 'release date', 'video release date', 'IMDB URL', 
          'unknown', 'Action', 'Adventure', 'Animation', 'Children\'s', 'Comedy', 
          'Crime', 'Documentary', 'Drama', 'Fantasy', 'Film-Noir', 'Horror', 
          'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']
movies = pd.read_csv('C:/RecoSys/Data/u.item', sep='|', names=i_cols, encoding='latin-1')
movies = movies[['movie_id', 'release date']]
movies = movies.set_index('movie_id')

r_cols = ['user_id', 'movie_id', 'rating', 'timestamp']
ratings = pd.read_csv('C:/RecoSys/Data/u.data', names=r_cols,  sep='\t',encoding='latin-1')
ratings = ratings.drop('timestamp', axis=1)

N = ratings.user_id.max() + 1       # Number of users
M = ratings.movie_id.max() + 1      # Number of movies
TRAIN_SIZE = 0.75

# train test 분리
ratings = shuffle(ratings)
cutoff = int(TRAIN_SIZE * len(ratings))
ratings_train = ratings.iloc[:cutoff]
ratings_test = ratings.iloc[cutoff:]
train_age = pd.merge(ratings_train, users, on='user_id')
train_age = train_age['age']
test_age = pd.merge(ratings_test, users, on='user_id')
test_age = test_age['age']

# Variable 초기화 
K = 100                             # Latent factor 수 
mu = ratings_train.rating.mean()    # 전체 평균 
reg = 0.0001                        # Regularization penalty
epochs = 50

import keras.backend as KB
def RMSE(y_true, y_pred):
    return KB.sqrt(KB.mean((y_true - y_pred)**2))

# Keras model
user = Input(shape=(1,))                                                # User input
item = Input(shape=(1,))                                                # Item input
age = Input(shape=(1,))
P_embedding = Embedding(N, K, embeddings_regularizer=l2(reg))(user)     # (N, 1, K)
Q_embedding = Embedding(M, K, embeddings_regularizer=l2(reg))(item)     # (N, 1, K)
user_bias = Embedding(N, 1, embeddings_regularizer=l2(reg))(user)       # User bias term (N, 1, 1)
item_bias = Embedding(M, 1, embeddings_regularizer=l2(reg))(item)       # Item bias term (N, 1, 1)
user_layer = Dense(4)(age)                                              # (N, 1, K)
user_layer = Activation('softmax')(user_layer)
P_embedding = Flatten()(P_embedding)                                    # (N, K)
Q_embedding = Flatten()(Q_embedding)                                    # (N, K)
user_bias = Flatten()(user_bias)                                        # (N, K)
item_bias = Flatten()(item_bias)                                        # (N, K)

R = Concatenate()([P_embedding, Q_embedding, 
               user_bias, item_bias, user_layer])                       # (N, 2K + 2 + 4)

# Neural network
R = Dense(1024)(R)
R = Activation('relu')(R)
R = Dropout(0.001)(R)

# Adding more layers
R = Dense(512)(R)
R = Activation('relu')(R)
#R = Dropout(0.001)(R)

R = Dense(1)(R)

model = Model(inputs=[user, item, age], outputs=R)  # 나이추가
model.compile(
  loss=RMSE,
  optimizer=Adam(lr=0.004),
  #optimizer=SGD(lr=0.08, momentum=0.85),
  metrics=['mean_squared_error', RMSE],
)
model.summary()

result = model.fit(
  x=[ratings_train.user_id.values, ratings_train.movie_id.values, 
     ratings_train.user_id.values, ratings_train.movie_id.values, train_age],
  y=ratings_train.rating.values - mu,
  epochs=epochs,
  batch_size=128,
  validation_data=(
    [ratings_test.user_id.values, ratings_test.movie_id.values,
     ratings_test.user_id.values, ratings_test.movie_id.values, test_age],
    ratings_test.rating.values - mu
  )
)

# Plot RMSE
plt.plot(result.history['RMSE'], label="Train RMSE")
plt.plot(result.history['val_RMSE'], label="Test RMSE")
plt.legend()
plt.show()

# Prediction
submodel = Model([user, item], R)
user_ids = ratings_train.user_id.values[0:5]
movie_ids = ratings_train.movie_id.values[0:5]
predictions = submodel.predict([user_ids, movie_ids]) + mu
print("Predictions:", predictions)
