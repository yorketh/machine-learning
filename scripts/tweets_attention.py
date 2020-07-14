# -*- coding: utf-8 -*-
"""tweets_attention.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1r0adB-c3mKShqtUZy2UxmxZi55jI3F8T

# Extracting text sentiment via attention mechanism (to be completed)

This notebook is an unfinished version of Kaggle [Tweet Sentiment Extraction](https://www.kaggle.com/c/tweet-sentiment-extraction) project. The goal of this project is to correctly predict what parts of sentence are the most responsible for assigning sentiment label. 

This notebook utilizes the attention mechanism proposed by Zhouhan Lin, et. al in the paper ["A Structured Self-attentive Sentence Embedding"](https://arxiv.org/abs/1703.03130) (2017).

# Text cleaning
"""

from spellchecker import SpellChecker
import pandas as pd
import numpy as np
import torch
from torch import nn
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn import preprocessing
from torch.utils.data import TensorDataset, DataLoader
from string import punctuation
import preprocessor as p
import re
import torch.nn.functional as F
import math
import nltk
import torchtext
#nltk.download('stopwords')
#from nltk.corpus import stopwords


train = pd.read_csv('train_tw.csv')
train.drop_duplicates(subset='text', keep='first', inplace=True)
train1 = train.copy()
train1.dropna(inplace=True)

test = pd.read_csv('test_tw.csv')


def clean(tweet): 
    
    tweet = re.sub(r"ShoesShoesShoes.YayYayYay.lol.IWouldPostATwitPic.ButIdntKnoHow2", 
                   "shoes shoes shoes yay yay yay lol i would post a twit pic but i do not know how to", tweet)
    
    tweet = tweet.replace("`", "'")
     # ... and ..
    tweet = tweet.replace('...', ' ... ')
    if '...' not in tweet:
        tweet = tweet.replace('..', ' .. ') 

    tweet = re.sub(r"Sooo", "so", tweet)
    tweet = re.sub(r"youstinkatrespondingtotexts ", "you stink at responding to texts", tweet)
    tweet = re.sub(r" tho ", " though ", tweet)
    tweet = re.sub(r"gr8", "great", tweet)
    tweet = re.sub(r"_21Thanks", "thanks", tweet)
    tweet = re.sub(r"<33333333333", "love", tweet)
    tweet = tweet.replace("****", "heck")
    tweet = re.sub(r"no0o0o0o", "no", tweet)
    
    # Urls
    tweet = re.sub(r"https?:\/\/t.co\/[A-Za-z0-9]+", "", tweet)
    tweet = re.sub('\w*\d\w*', '', tweet)
    tweet = re.sub('https?://\S+|www\.\S+', '', tweet)
    
    # Contractions
    #tweet = re.sub(r"****", "fuck", tweet)
    tweet = tweet.lower()


    tweet = re.sub(r"im", "i am", tweet)
    tweet = re.sub(r" ww", "", tweet)
    tweet = re.sub(r"wasnt", "was not", tweet)
    tweet = re.sub(r"soo", "so", tweet)
    tweet = re.sub(r"nm", "never mind", tweet)
    tweet = re.sub(r"yer", "your", tweet)
    tweet = re.sub(r"gorjuz", "gorgeous", tweet)
    tweet = re.sub(r" u ", " you ", tweet)
    tweet = re.sub(r"boo0o0o0o00oring", "boring", tweet)
    tweet = re.sub(r"btw", "by the way", tweet)
    tweet = re.sub(r"sooo", "so", tweet)
    tweet = re.sub(r"hes", "he is", tweet)
    tweet = re.sub(r"he's", "he is", tweet)
    tweet = re.sub(r"there's", "there is", tweet)
    tweet = re.sub(r"won't", "will not", tweet)
    tweet = re.sub(r"they're", "they are", tweet)
    tweet = re.sub(r"can't", "cannot", tweet)
    tweet = re.sub(r"wasn't", "was not", tweet)
    tweet = re.sub(r"don\x89Ûªt", "do not", tweet)
    tweet = re.sub(r"aren't", "are not", tweet)
    tweet = re.sub(r"isn't", "is not", tweet)
    tweet = re.sub(r"havent", "have not", tweet)
    tweet = re.sub(r"haven't", "have not", tweet)
    tweet = re.sub(r"hasn't", "has not", tweet)
    tweet = re.sub(r"it's", "it is", tweet)
    tweet = re.sub(r"shouldn't", "should not", tweet)
    tweet = re.sub(r"wouldn't", "would not", tweet)
    tweet = re.sub(r"i'm", "i am", tweet)
    tweet = re.sub(r"i\x89Ûªm", "i am", tweet)
    tweet = re.sub(r"here's", "here is", tweet)
    tweet = re.sub(r"you've", "you have", tweet)
    tweet = re.sub(r"you\x89Ûªve", "you have", tweet)
    tweet = re.sub(r"we're", "we are", tweet)
    tweet = re.sub(r"what's", "what is", tweet)
    tweet = re.sub(r"couldn't", "could not", tweet)
    tweet = re.sub(r"we've", "we have", tweet)
    tweet = re.sub(r"it\x89Ûªs", "it is", tweet)
    tweet = re.sub(r"doesn\x89Ûªt", "does not", tweet)
    tweet = re.sub(r"here\x89Ûªs", "here is", tweet)
    tweet = re.sub(r"who's", "who is", tweet)
    tweet = re.sub(r"i\x89Ûªve", "i have", tweet)
    tweet = re.sub(r"y'all", "you all", tweet)
    tweet = re.sub(r"can\x89Ûªt", "cannot", tweet)
    tweet = re.sub(r"would've", "would have", tweet)
    tweet = re.sub(r"it'll", "it will", tweet)
    tweet = re.sub(r"we'll", "we will", tweet)
    tweet = re.sub(r"wouldn\x89Ûªt", "would not", tweet)
    tweet = re.sub(r"he'll", "he will", tweet)
    tweet = re.sub(r"they'll", "they will", tweet)
    tweet = re.sub(r"they'd", "they would", tweet)
    tweet = re.sub(r"that\x89Ûªs", "that is", tweet)
    tweet = re.sub(r"they've", "they have", tweet)
    tweet = re.sub(r"i'd", "i would", tweet)
    tweet = re.sub(r"should've", "should have", tweet)
    tweet = re.sub(r"you\x89Ûªre", "you are", tweet)
    tweet = re.sub(r"where's", "where is", tweet)
    tweet = re.sub(r"don\x89Ûªt", "do not", tweet)
    tweet = re.sub(r"we'd", "we would", tweet)
    tweet = re.sub(r"i'll", "i will", tweet)
    tweet = re.sub(r"weren't", "were not", tweet)
    tweet = re.sub(r"can\x89Ûªt", "can not", tweet)
    tweet = re.sub(r"you\x89Ûªll", "you will", tweet)
    tweet = re.sub(r"i\x89Ûªd", "i would", tweet)
    tweet = re.sub(r"let's", "let us", tweet)
    tweet = re.sub(r"it's", "it is", tweet)
    tweet = re.sub(r"can't", "can not", tweet)
    tweet = re.sub(r"don't", "do not", tweet)
    tweet = re.sub(r"you're", "you are", tweet)
    tweet = re.sub(r"i've", "I have", tweet)
    tweet = re.sub(r"that's", "that is", tweet)
    tweet = re.sub(r"doesn't", "does not", tweet)
    tweet = re.sub(r"didn't", "did not", tweet)
    tweet = re.sub(r"ain't", "am not", tweet)
    tweet = re.sub(r"you'll", "you will", tweet)
    tweet = re.sub(r"you'd", "you would", tweet)
    tweet = re.sub(r"haven't", "have not", tweet)
    tweet = re.sub(r"could've", "could have", tweet)
    tweet = re.sub(r"youve", "you have", tweet) 
    tweet = re.sub(r"donbt", "do not", tweet)
    tweet = re.sub(r"dont", "do not", tweet)
    tweet = re.sub(r"thats", "that is", tweet) 
    tweet = re.sub(r"noooooooooooooooooo", "no", tweet)
    tweet = re.sub(r"nooooooooo", "no", tweet)
    tweet = re.sub(r"coldddd", "cold", tweet)
    tweet = re.sub(r"lllooovvveee", "love", tweet)
    tweet = re.sub(r"luckyyyyyyy", "lucky", tweet)
    tweet = re.sub(r"lunchhhhhhhh", "lunch", tweet)
    tweet = re.sub(r"aaaaaaaahhhhhhhh", "ah", tweet)
    tweet = re.sub(r"loveeee", "love", tweet)
    tweet = re.sub(r"goooooood", "good", tweet)
    tweet = re.sub(r"pleaseeeeeeeeeee", "please", tweet) 
    tweet = re.sub(r"mondaycant", "monday can not", tweet) 
    tweet = re.sub(r"bac", "back", tweet)
    tweet = re.sub(r"dint", "did not", tweet)
    tweet = re.sub(r"rubbishhhhhh", "rubish", tweet)
    tweet = re.sub(r"michaelblessings", "michael blessings", tweet)
    tweet = re.sub(r"decembbberrrrrrrr", "december", tweet)
    
    
    # Special characters
    tweet = re.sub(r"\x89Û_", "", tweet)
    tweet = re.sub(r"\x89ÛÒ", "", tweet)
    tweet = re.sub(r"\x89ÛÓ", "", tweet)
    tweet = re.sub(r"\x89ÛÏWhen", "When", tweet)
    tweet = re.sub(r"\x89ÛÏ", "", tweet)
    tweet = re.sub(r"China\x89Ûªs", "China's", tweet)
    tweet = re.sub(r"let\x89Ûªs", "let's", tweet)
    tweet = re.sub(r"\x89Û÷", "", tweet)
    tweet = re.sub(r"\x89Ûª", "", tweet)
    tweet = re.sub(r"\x89Û\x9d", "", tweet)
    tweet = re.sub(r"å_", "", tweet)
    tweet = re.sub(r"\x89Û¢", "", tweet)
    tweet = re.sub(r"\x89Û¢åÊ", "", tweet)
    tweet = re.sub(r"fromåÊwounds", "from wounds", tweet)
    tweet = re.sub(r"åÊ", "", tweet)
    tweet = re.sub(r"åÈ", "", tweet)
    tweet = re.sub(r"JapÌ_n", "Japan", tweet)    
    tweet = re.sub(r"Ì©", "e", tweet)
    tweet = re.sub(r"å¨", "", tweet)
    tweet = re.sub(r"SuruÌ¤", "Suruc", tweet)
    tweet = re.sub(r"åÇ", "", tweet)
    tweet = re.sub(r"å£3million", "3 million", tweet)
    tweet = re.sub(r"åÀ", "", tweet)

    # Words with punctuations and special characters
    punctuations = '@#!?+&[]-%.*:/();$=><|{}^'
    for p in punctuations:
        tweet = tweet.replace(p, f' {p} ')
    
    # Character entity references
    tweet = re.sub(r"&gt;", ">", tweet)
    tweet = re.sub(r"&lt;", "<", tweet)
    tweet = re.sub(r"&amp;", "&", tweet)
    tweet = re.sub('<.?>+', '', tweet)
    tweet = re.sub('[%s]' % re.escape(punctuation), '', tweet)
    tweet = re.sub('\n', '', tweet)
    tweet = re.sub('\[.?\]', '', tweet)

    
    return tweet

# improve text cleaning with texthero library
train1['text_clean'] = train1['text'].apply(lambda s: clean(s))
train1['labels_clean'] = train1['selected_text'].apply(lambda s: clean(s))

spell = SpellChecker()
def correct_spellings(text):
    corrected_text = []
    misspelled_words = spell.unknown(text.split())
    for word in text.split():
        if word in misspelled_words:
            corrected_text.append(spell.correction(word))
        else:
            corrected_text.append(word)
    return " ".join(corrected_text)

#train1['text_clean']=train1['text_clean'].apply(lambda x : correct_spellings(x))
#train1['labels_clean'] = train1['labels_clean'].apply(lambda x : correct_spellings(x))

REPLACE_NO_SPACE = re.compile(
    "(\.)|(\;)|(\:)|(\!)|(\')|(\?)|(\,)|(\")|(\|)|(\()|(\))|(\[)|(\])|(\%)|(\$)|(\>)|(\<)|(\{)|(\})")
REPLACE_WITH_SPACE = re.compile("(<br\s/><br\s/?)|(-)|(/)|(:).")

def clean_tweets(df):
    tempArr = []
    for line in df:
        tmpL = p.clean(line)
        tmpL = REPLACE_NO_SPACE.sub("", tmpL.lower())
        tmpL = REPLACE_WITH_SPACE.sub(" ", tmpL)
        tempArr.append(tmpL)
    return tempArr


all_tweets = list(train1['text_clean'])

all_labels =  list(train1['labels_clean'])

print(all_tweets[:100])


# balancing selected_text and text after cleaning 
# (and due to some selection mistakes made by dataset creatprs)
import difflib

for k,v in zip(all_tweets, all_labels):
  if len([i for i in v.split() if i not in k.split()])>0:
    a = v.split()
    for i in a:
      try:
        a[a.index(i)] = \
        difflib.get_close_matches(i, all_tweets[all_labels.index(v)].split(), cutoff=0.1)[0]
      except IndexError:
        all_tweets.remove(k)
        all_labels.remove(v)
    all_labels[all_labels.index(v)] = a
    all_tweets[all_tweets.index(k)] = k.split()
  else:
    all_tweets[all_tweets.index(k)] = k.split()
    all_labels[all_labels.index(v)] = v.split()

"""# Processing pre-trained embedding matrix and reorganizing the data"""

cleaned_df = pd.DataFrame({
    'text': [' '.join(i for i in y) for y in all_tweets],
    'selected_text': [' '.join(i for i in y) for y in all_labels]
})


vocabulary = []

for i in all_tweets:
  for y in i:
    if y not in vocabulary:
      vocabulary.append(y)

# pretrained glove embeddings for twitter with dim of 200
glove = torchtext.vocab.GloVe(name="twitter.27B", dim=200)


matrix_len = len(vocabulary)
weights_matrix = np.zeros((matrix_len+1, 200))
#weights_matrix[0] = np.random.normal(scale=0.6, size=(100, ))

words_found = 0

for i, word in enumerate(vocabulary, start=1):
    if float(torch.sum(glove[word]))!=0.:
        weights_matrix[i] = glove[word]
        words_found += 1
    else:
        weights_matrix[i] = np.random.normal(scale=0.6, size=(200, ))

print(f'Words found: {words_found} out of {len(vocabulary)}')
from sklearn.decomposition import PCA
def all_but_the_top(v, D):
    v_tilde = v[1:] - np.mean(v[1:])

    U1 = PCA(n_components=D).fit(v_tilde).components_
    new_matrix = np.zeros((matrix_len+1, 200))
    for s, x in enumerate(v_tilde, start=1):
	    for u in U1:        
        	x = x - np.dot(u.transpose(),x) * u 
	    new_matrix[s] = x

    return new_matrix

weights_matrix = all_but_the_top(weights_matrix,5)

# function for inserting embeddings into neural net
def create_emb_layer(weights_matrix, non_trainable=False):
    num_embeddings, embedding_dim = weights_matrix.shape
    emb_layer = nn.Embedding(num_embeddings, embedding_dim)
    emb_layer.load_state_dict({'weight': torch.tensor(weights_matrix)})
    if non_trainable:
        emb_layer.weight.requires_grad = False

    return emb_layer, num_embeddings, embedding_dim

voc_dic = {i:vocabulary.index(i)+1 for i in vocabulary}
print('Dictionary: ', voc_dic)

tweets_num = []

for i in all_tweets:
  tweets_num.append([voc_dic[y] for y in i])


print('Tokenized: ', tweets_num[0])

padded = pad_sequences(tweets_num, padding='post')

print('Padded: ', padded[0])

# mask for not paying attention to zero padding
mask = [np.array([1 if y!=0 else 0 for y in i]) for i in padded]


le = preprocessing.LabelEncoder()
labels_sent = le.fit_transform(train1['sentiment'])

cleaned_df['sentiment'] = labels_sent
cleaned_df.to_csv('cleaned_text.csv')

labels_num = []

for i in all_labels:
  labels_num.append([voc_dic[y] if y in voc_dic else 0 for y in i])

for i in labels_num:
  if np.count_nonzero(np.array(i))==0:
    print('Zero: ', all_tweets[labels_num.index(i)])

print('Labels tokenized: ', labels_num[0])


padded1 = [list(i) for i in padded]

k=[[i, labels_num[padded1.index(i)]] for i in padded1]

labelsl = []
for i in k:
  labelsl.append([0 if y not in i[1] else 1 for y in i[0]])


labels = [np.array([1/int(torch.sum(torch.tensor(i))) if y == 1 else 0 for y in i]) for i in labelsl]

#concatenate both types pf labels
labels = np.array([np.append(i,k) for i,k in zip(labels, labels_sent)])
print(labels[0])

final_padded = np.array([np.concatenate((k,v)) for k,v in zip(padded, mask)])
print(final_padded[:5])

X_train, X_val, y_train, y_val = train_test_split(final_padded, labels, test_size=0.2)
vocab_reversed = {v:k for k,v in voc_dic.items()}

print('Text', [vocab_reversed[i] if i!=0 else 0 for i in X_train[0]])
print('Selected', y_train[0])

"""# Model&Training

Self-attention mechanism implemented in this notebook utilizes hidden states of bidirectional LSTM layer to create the embedding of the sentence through applying several linear layers in order to represent the relative significance of separate words in forming sentence sentiment. More spicifically, two linear layers without biases, size `d` and `r`, with `tanh` activation in between are used, followed by `softmax` activation to derive a sentiment probability distribution. Resulting attention mask can later be used for weightening words in a sentence with purposes of sentiment classification.

In this case we extract this intermediate mask to see what words our net pays most attention to when classifying tweets as negative, neutral or positive, and then use this information to calculate target Jaccard score.

![](https://miro.medium.com/max/700/1*6c4-E0BRRLo197D_-vyXdg.png)
![](https://miro.medium.com/max/700/1*dtC80EsitkHgK421wqJijw.png)
"""

train_data = TensorDataset(torch.from_numpy(X_train), torch.tensor(y_train))
valid_data = TensorDataset(torch.from_numpy(X_val), torch.from_numpy(y_val))

batch_size = 300

train_loader = DataLoader(train_data, shuffle=True, batch_size=batch_size, 
                          drop_last=True)
valid_loader = DataLoader(valid_data, shuffle=True, batch_size=batch_size, 
                          drop_last=True)

train_on_gpu = torch.cuda.is_available()


class Sent(nn.Module):
    def __init__(self, weights_matrix, hidden_size, linear_hid, d, r):
        super(Sent, self).__init__()
        self.hidden_size = hidden_size
        self.d = d
        self.r = r
        self.linear_hid = linear_hid
        self.embed, num_embeddings, embedding_dim = create_emb_layer(weights_matrix, True)

        self.lstm = nn.LSTM(embedding_dim, hidden_size, batch_first=True, 
                            bidirectional=True)
        self.w1 = nn.Linear(2*hidden_size, d, bias=False)
        self.tanh = nn.Tanh()
        self.w2 = nn.Linear(d, r, bias = False)
        self.soft = nn.Softmax(dim=1)
        self.drop = nn.Dropout(.3)

        self.lin1 = nn.Linear(2*hidden_size, linear_hid)
        self.relu = nn.ReLU()
        self.lin2 = nn.Linear(linear_hid, 3)


    def forward(self, x, hidden):
      # [132x70]
      batch_size = x.size(0)
      x = x.long()
      em = self.embed(x[:, :35])  # [132x35x50]
      out, hidden = self.lstm(em, hidden)  # [132x35x16]
      out = self.drop(out)

      _w = self.tanh(self.w1(out))
      w = self.w2(_w)
      w = torch.abs(w) # [132x35x1]
      
      # 132x35x1
      #att = w.mean(dim=2).squeeze(2)
      
      att = self.soft(w)
      
      att = w.transpose(dim0=1, dim1=2)
    
      m = torch.matmul(att, out)
      m = m.mean(dim=1)
      
      m = m.view(batch_size, -1)
      x = self.relu(self.lin1(m))
      # [32x3]
      x = self.lin2(x)

      return x, hidden, w.squeeze(2) # [132x35]

    def initHidden(self, batch_size):
        weight = next(self.parameters()).data
        if train_on_gpu:
          hidden = (weight.new(2, batch_size, self.hidden_size).zero_().cuda(), #//2
                  weight.new(2, batch_size, self.hidden_size).zero_().cuda())
        else:
          hidden = (weight.new(2, batch_size, self.hidden_size).zero_().cpu(), #//2
                  weight.new(2, batch_size, self.hidden_size).zero_().cpu())
        return hidden


hidden_size = 16
d = 10
r = 1
linear_hid = 200

net = Sent(weights_matrix, hidden_size, linear_hid, d, r)
print(net)

def count_parameters(model):
    return sum(p.numel() for p in net.parameters() if p.requires_grad)

print(f'Number of parameters: {count_parameters(net)}')

optimizer = torch.optim.Adam(net.parameters(), lr=0.03)
criterion = nn.L1Loss()
criterion1 = nn.CrossEntropyLoss()

epochs = 8
counter = 0
clip = 5
print_every = 200
count_ep = 0

if train_on_gpu:
    net.cuda()

net.train()
av_jac =[]

for epoch in range(epochs):
  val_attention = []
  input_text = []
  selected = []
  my_texts = []
  result = []
  selectedd = []
  atten = []
  jaccard = []
  count_ep+=1
  
  train_res = []
  train_lab = []
  valid_res = []
  valid_lab = []
  hidden = net.initHidden(batch_size)
  for input, label in train_loader:

    counter += 1
    if train_on_gpu:
        input, label = input.cuda(), label.cuda()
    
    hidden = tuple([e.data for e in hidden])
    
    net.zero_grad()
    
    output, hidden, att = net(input, hidden)
    
    for i in output:
      train_res.append(int(torch.argmax(i)))
    for i in label:
      train_lab.append(int(i[-1]))
    
    loss = criterion(att.float(), torch.stack([i[:-1] for i in label.float()])*10)
    loss.backward(retain_graph=True)
    
    loss1 = criterion1(output, torch.stack([i[-1] for i in label.long()]))
    loss1.backward()
    
    nn.utils.clip_grad_norm_(net.parameters(), clip)
    #print('Gradients', net.w1.weight.grad)
    optimizer.step()
    
    acc = np.sum(np.array(train_res) == np.array(train_lab)) / len(np.array(train_lab))
    
  valid_hidden_state = net.initHidden(batch_size)
  valid_losses = []
  valid_losses1 = []
  net.eval()
  for input, label in valid_loader:
    
    valid_hidden_state = tuple([e.data for e in valid_hidden_state])
    if train_on_gpu:
      input, label = input.cuda(), label.cuda()

    output, valid_hidden_state, att = net(input, valid_hidden_state)

    for k, v in zip(input.cpu().detach(), att.cpu().detach()):
      v[~torch.tensor(k[35:], dtype=torch.bool)] = float('-inf')
      v = torch.softmax(v, dim=0)
      #print('sentence:', k[:35])
      #print('attention', v)
      val_attention.append(v.float().numpy())
      #input_text.append(k[:35].numpy())
      my_texts.append([vocab_reversed[o] for o in k[:35].numpy() if int(o)!= 0])
    
    for i in label.cpu().detach().numpy():
      selected.append(i[:-1])
    for i in output:
      valid_res.append(int(torch.argmax(i)))
    for i in label:
      valid_lab.append(int(i[-1]))

    val_loss = criterion(att.float(), torch.stack([i[:-1] for i in label.float()]))
    val_loss1 = criterion1(output, torch.stack([i[-1] for i in label.long()]))
    
    valid_losses.append(val_loss.item())
    valid_losses1.append(val_loss1.item())
    
    val_acc = np.sum(np.array(valid_res) == np.array(valid_lab)) / len(np.array(valid_lab))
    
    for u, k, v, l in zip(np.array(val_attention), my_texts, np.array(selected), valid_lab):
      atten.append(u)
      try:
        if l == 1:
          result.append([k[list(u).index(i)] for i in u if i>np.mean(u)])
          #print('Attention:', [k[list(u).index(i)] for i in u if i>np.mean(u)])
        else:
          result.append([k[i] for i in np.argpartition(u, -1)[-1:]])
          #print('Attention:', [k[i] for i in np.argpartition(u, -1)[-1:]])
      except IndexError:
        print(k)
        print(u)
      #result.append([k[i] for i in np.argpartition(u, -np.count_nonzero(v))[-np.count_nonzero(v):] if k[i]!='0' and k[i]!=0])
      selectedd.append([i for i in k if v[k.index(i)]!=0 and i!=0])
      
      
    for k,v,u in zip(result, selectedd,atten):
      #print('Selected', k)
      #print('Actual',v)
      #print('Attentiion', u)
      if len(k)!= 0 and len(v) != 0:
        intersection = set(k).intersection(set(v))
        union = set(k).union(set(v))
        jaccard.append(len(intersection)/len(union))

  net.train()

  print(f'Epoch: {epoch + 1}/{epochs}')
  print(f'Step: {counter}')
  print(f'Train_acc: {acc}')
  print(f'Valid_acc: {val_acc}')
  print('Report: ')
  print(classification_report(valid_lab, valid_res))
  print(f'Loss L1: {loss.item()}')
  print(f'Loss Cross: :{loss1.item()}')
  print(f'Val_loss L1: {np.mean(valid_losses)}')
  print(f'Val_loss Cross: {np.mean(valid_losses1)}')
  av_jac.append(np.mean(jaccard))
  print('Average jaccard: ', np.mean(jaccard))

print(f'Final average jaccard: {np.mean(av_jac)}')

torch.save(net.state_dict(), 'tweet_model.pt')
print('Model saved!')

"""Resulting validation accuracy is `75%` with Jaccard index at about `65%`. However it could not be considered as valid result as Jaccard was calculated with respect to preprocessed text, and all empty results were dropped as well - so in reality it should be lower. Extracting original words/parts of the sentence shouldn't be that complicated though, despite it being an artificial and rudimental process having nothing in common with machine learning per se. Common sense could be applied here, e.g. it's worth taking into consideration that selected text is usually uninterrupted, so for sentence "a b c" where words "a" and "c" have got attention from the model, word "b" should also be included as a probable intermediate part of selected sequence."""