import tensorflow as tf
from tensorflow import keras
from numpy import loadtxt
from keras.models import Sequential
from keras.layers import Dense
import os
from data.match import matching_Bert_Graph, read_ratings, read_bert_embedding, read_graph_embeddings
from models.model3_conf2_strategy_att import run_model
import logging
import sys

if __name__ == "__main__":
  logging.basicConfig(format="%(message)s", level=logging.INFO)
  logger = logging.getLogger(__name__)
  if len(sys.argv) != 6:
    logger.error("Invalid number of parameters.")
    exit(-1)
  
bert_user_source = sys.argv[1]
bert_item_source = sys.argv[2]
graph_source = sys.argv[3]
dest = sys.argv[4]
prediction_dest = sys.argv[5]

print(bert_user_source)
print(bert_item_source)
print(graph_source)
print(dest)
print(prediction_dest)

user, item, rating = read_ratings('datasets/movielens/train2id.tsv')

graph_embeddings = read_graph_embeddings(graph_source)
user_bert_embeddings = read_bert_embedding(bert_user_source)
item_bert_embeddings = read_bert_embedding(bert_item_source)

X_graph,X_bert,dim_graph,dim_bert,y = matching_Bert_Graph(user,item,rating,graph_embeddings,user_bert_embeddings,item_bert_embeddings)

model = run_model(X_graph,X_bert,dim_graph,dim_bert,y,epochs=25,batch_size=1536)

# creates a HDF5 file 'model.h5'
model.save(dest + 'model.h5')