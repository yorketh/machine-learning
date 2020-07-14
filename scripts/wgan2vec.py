# -*- coding: utf-8 -*-
"""WGAN2vec.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/19qjVEPxFRBrkPlvpYT0gGe-yFis1fPKk

## WGAN2vec: reimplementing Generative Adversarial Network for text generation

This notebook tries to implement a GAN model proposed by Akshay Budhkar, et. al in the paper [Generative Adversarial Networks for text using word2vec intermediaries](https://arxiv.org/abs/1904.02293) (2019). Basically, authors make attempt to generate coherent sentences in the form of word embeddings using Generative Adversarial Network, while evaluating model performance by converting generated embeddings into text based on cosine similarity (nearest neighbors approach). The algorithm is as follows:

![Замещающий текст](http://drive.google.com/uc?export=view&id=1g0MLMrhlKWaVvWUfJfhu65_vqV8XtCWL)

And general framework structure looks like this:
![Замещающий текст](https://storage.googleapis.com/groundai-web-prod/media%2Fusers%2Fuser_14%2Fproject_348561%2Fimages%2Fx1.png)

Official code wasn't released by the authors yet, and the only [unofficial attempt](https://github.com/adventure2165/GAN2vec/blob/master/GAN2vec.ipynb) to implement the paper ended up with mode collapse (Generator managed to produce only 2 almost indentical sentences).

Despite the fact that the paper describes overall model architecture and training algorithm in pretty straightforward manner, specific hyperparameters choices weren't covered. It has led to a great level of ambiguity as GANs are highly sensitive to any architecture modifications in both Generator and Discriminator. Kernel sizes in transposed and regular convolutional layers used in this notebook are the same as in the mentioned impementation (basic GAN framework code implementation was taken from [this post](https://medium.com/ai-society/gans-from-scratch-1-a-deep-introduction-with-code-in-pytorch-and-tensorflow-cb03cdcdba0f) regarding generating MNIST-like images).

In order to prevent mode collapse, some changes were made to the original proposition. Namely:
1. Traditional GAN training algorithm was replaced by [Wasserstein GAN (WGAN)](https://arxiv.org/abs/1701.07875)![Замещающий текст](https://wiseodd.github.io/img/2017-02-04-wasserstein-gan/00.png).

  This involved changes in calculation of D and G losses, D architecture (no `Sigmoid` activation for output), training iterations, learning and decay rates, D weight clipping, and optimizer type.
2. In order for discriminator to learn to distinguish between coherent and non-coherent sentences (and not only check for correct distribution of generated data) it was pretrained on the train corpus splitted into original sentences and sentences with two random words swapped.
3. Learning rate for Generator is `10` times bigger than that of Discriminator.
4. Number of epochs is reduced to `50`.
5. Random noise size is increased to `256` instead of `100`.
6. Label smoothing was dismissed.
7. Other minor changes.

As a result, quality of generated senteces is comparable to the original work (w/ a few nuances).
"""

import torch
from torch import nn, optim
import pandas as pd
import numpy as np
import re
from torch.utils.data import TensorDataset, DataLoader

"""# Preparing data"""

sentences = []
train_sen = []
length = []

sent = pd.read_fwf('cmu-se.txt') # CMU-SE dataset

test_sent = [len(i.split(' ')) for i in sent.text]

from collections import Counter
data = Counter(test_sent)

print(data.most_common()) # most common sentence length
print(np.mean(test_sent)) # average sentence length

for i in sent.text:
    splitsent = i.split(' ')
    train_sen.append(splitsent) # add all sentences to train embedding matrix on
    if len(splitsent)>=7: # length <=7
        sentences.append(splitsent[:7])


newdf = pd.DataFrame(columns=['sentence', 'score'])
newdf['sentence'] = sentences
scores = [1 for i in range(len(sentences))]
newdf['score'] = scores

print(newdf.head())
newdf.to_csv('sentences.csv')

from gensim.models import Word2Vec
from tqdm import tqdm

tqdm.pandas()

# creating embedding model using gensim library
model = Word2Vec(sentences=train_sen, window=3, min_count=1,
                 sg=1, 
                 size=64,  
                 workers=4)

# closest words to 'nice' based on cosine similarity
model.wv.most_similar('nice')

import random

print(len(model.wv.vocab.keys())) # number of unique embeddings in dataset

vocabulary = []

for i in sentences:
  for y in i:
    if y not in vocabulary:
      vocabulary.append(y)

print(vocabulary[:20])
print(len(vocabulary)) # number of unique embeddings for sentences of length <=7

# converting text into embeddings
sent_embed = np.array([[model.wv[y] for y in i] for i in sentences])

print(sent_embed[0])

print(sent_embed.shape)

scores = np.array(scores)

swapped = sent_embed[:]
sent_embed = sent_embed.copy()

# randomly choose and swap two words in a sentence
for i in swapped:
  ix1, ix2 = random.sample(range(7),2)
  i[[ix1, ix2]] = i[[ix2, ix1]]

labels_or = [1 for i in range(len(sent_embed))] # labels for original sentences
labels_sw = [0 for i in range(len(swapped))] # labels for swapped sentences

print(swapped.shape)

print(sent_embed[0]) # first original sentence
print(swapped[0]) # first swapped sentence

print(' '.join([model.wv.most_similar([i], topn=1)[0][0] for i in sent_embed[0]]))
print(' '.join([model.wv.most_similar([i], topn=1)[0][0] for i in swapped[0]]))

"""# Model

Generator uses one linear layer to transform from the size of initial random noise and two 2-D fractionally strided convolution layers. Output size is batch size \* sentence length \* embedding dimension. Two Leaky RELU and batch normalization layers with a single dropout layer have been used to stabilize generated data.
"""

batch_size = 100
class GeneratorNet(torch.nn.Module):
    def __init__(self):
        super(GeneratorNet, self).__init__()
        n_features = 256

        self.lin1 = nn.Linear(n_features, 512)
        self.relu = nn.LeakyReLU(0.2)
        self.drop = nn.Dropout(.3)
        self.conv1 = nn.ConvTranspose2d(512, 256, kernel_size=(3,16), stride=1,
                                        bias=False)
        self.norm1 = nn.BatchNorm2d(256)
        self.norm2 = nn.BatchNorm2d(1)
        self.conv2 = nn.ConvTranspose2d(256, 1, kernel_size=(3,34), stride=2,
                                        bias=False)
    
    def forward(self, x):
        batch_size = x.size(0)
        x = self.lin1(x)
        x = x.view(batch_size, 512,1,1)
        x = self.relu(x)
        x = x.float()
        x = self.relu(self.norm1(self.conv1(x)))
        x = self.drop(self.relu(self.norm2(self.conv2(x)))) 

        return x.squeeze(1)

"""Discriminator is somewhat mirrored version of Generator, using 2-D convolutional layers. Note that `Sigmoid` function isn't used due to WGAN loss function that doesn't include logarithm, hence D output isn't a probability but a regular continious value."""

class DiscriminatorNet(nn.Module):
    def __init__(self):
        super(DiscriminatorNet, self).__init__()

        self.conv1 = nn.Conv2d(1, 512, kernel_size=(3,64), bias=False)
        self.relu = nn.LeakyReLU(0.2)
        self.conv2 = nn.Conv2d(512, 64, kernel_size=(5,1), bias=False)
        self.ln1 = nn.Linear(64, 1)
        self.drop = nn.Dropout(.3)

    def forward(self, x):
        batch_size = x.size(0)
        x = x.view(batch_size, 1, 7, 64)
        x = x.float()
        x = self.relu(self.conv1(x))
        x = self.drop(self.relu(self.conv2(x)))
        x = x.view(batch_size, -1)
        x = self.ln1(x)
        
        return x

discriminator = DiscriminatorNet()
generator = GeneratorNet()

if torch.cuda.is_available():
    discriminator.cuda()
    generator.cuda()

"""Optmizer type and learning rates were suggested by WGAN authors. Generator learning rate is 0.0005, Discriminator learning rate is 0.00005"""

d_optimizer = optim.RMSprop(discriminator.parameters(), lr=5e-5)
g_optimizer = optim.RMSprop(generator.parameters(), lr=5e-4)

# Loss function for pretraining Discriminator
# We can no longer use BCELoss because of no Sigmoid 
# (BCEWithLogitsLoss is more stable anyway)
loss = nn.BCEWithLogitsLoss()

print(len(scores))

data = TensorDataset(torch.from_numpy(sent_embed), torch.from_numpy(scores))
data_loader = DataLoader(data, batch_size=100, shuffle=True, drop_last=True)

print(len(data_loader)) # data for GAN

features = np.concatenate([sent_embed, swapped]) # all sentences
print(len(features))

labels = np.concatenate([labels_or,labels_sw])
print(len(labels)) # all labels

from sklearn.model_selection import train_test_split

X_train, X_val, y_train, y_val = train_test_split(features, labels, 
                                                  test_size=0.2, shuffle=True)

train_data = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train))
val_data = TensorDataset(torch.from_numpy(X_val), torch.from_numpy(y_val))

train_load = DataLoader(train_data, batch_size=100, shuffle=True, drop_last=True)
valid_load = DataLoader(val_data, batch_size=100, shuffle=True, drop_last=True)

print(len(train_load)) # train set size
print(len(valid_load)) # valid set size

"""# Pretraining the Discriminator
After 10 epochs we got `90% `validation accuracy on 15,9k sentences.
"""

from sklearn.metrics import accuracy_score
sig = nn.Sigmoid()
 
optimizer = optim.Adam(discriminator.parameters(), lr=0.01)

for e in range(10):

  train_res = []
  val_res = []
  train_loss = []
  val_loss = []
  train_lab = []
  val_lab = []
    
  for f,l in train_load:
    
    if torch.cuda.is_available():
      f, l = f.cuda(), l.cuda()
    
    discriminator.zero_grad()
    out = discriminator(f)

    for i in out.squeeze().cpu().detach():
      train_res.append(sig(i))
 
    error = loss(out.squeeze(), l.float())

    train_loss.append(error.item())

    for i in l.cpu().detach().numpy():
      train_lab.append(i)
 
    error.backward()
    optimizer.step()
 
  discriminator.eval()
  
  for f_val, l_val in valid_load:
    if torch.cuda.is_available():
      f_val, l_val = f_val.cuda(), l_val.cuda()
    
    out = discriminator(f_val)
 
    for i in out.squeeze().cpu().detach():
      val_res.append(torch.round(sig(i)))
 
    error = loss(out.squeeze(), l_val.float())
    val_loss.append(error.item())

    for i in l_val.cpu().detach().numpy():
      val_lab.append(i)
 
    discriminator.train()
 
    
  print(f'Epoch: {e+1}/10')
  print(f'Train loss: {np.mean(train_loss)}')
  print(f'Valid loss: {np.mean(val_loss)}')
  print(f'Training acc: {accuracy_score(train_lab, np.round(train_res, decimals=0))}')
  print(f'Val acc: {accuracy_score(val_lab, np.round(val_res, decimals=0))}')

# random noise of normal distribution
def noise(size):
    n = torch.randn(size, 256)
    if torch.cuda.is_available(): return n.cuda() 
    return n

"""WGAN adresses a lot of issues that are naturally built in regular GAN: mode collapse, unstable training, failing to converge (e.g. due to gradient vanishing), lack of information about learning process derived from D and G losses (now D loss allows to track progress explicitly). More info could be found in the [original paper](https://arxiv.org/abs/1701.07875), [here](https://wiseodd.github.io/techblog/2017/02/04/wasserstein-gan/) or [here](https://paper.dropbox.com/doc/Wasserstein-GAN-GvU0p2V9ThzdwY3BbhoP7).

# Training
"""

def train_discriminator(optimizer, real_data, fake_data):

    optimizer.zero_grad()

    # D prediction for actual sentences
    prediction_real = discriminator(real_batch)
    # D prediction for generated sentences
    prediction_fake = discriminator(fake_data)
    
    """
    WGAN loss for D, now referred to as critic (update D parameters).
    It utilizes Wasserstein-1 distance and basically shows the difference 
    between D's estimation of generated and real samples quality. 
    In practice, training behaviour is identical to 
    error_d = torch.mean(prediction_real) - torch.mean(prediction_fake)
    given that error_g = torch.mean(prediction).
    Here we add minus sign before substraction to ensure correct param update
    w1 = w0 + lr * gradient (see WGAN algorithm)
    """
    error_d = -(torch.mean(prediction_real) - torch.mean(prediction_fake))

    error_d.backward()
    optimizer.step()

    # clipping the weights of D to model only K-Lipschitz function
    for p in discriminator.parameters():
            p.data.clamp_(-0.01, 0.01)

    return error_d

def train_generator(optimizer, fake_data):

    optimizer.zero_grad()

    # D prediction for generated sentences
    prediction = discriminator(fake_data)

    """
    WGAN loss for G (update G parameters).
    In practice, training behaviour is identical to 
    error_g = torch.mean(prediction) given that 
    error_d = torch.mean(prediction_real) - torch.mean(prediction_fake)
    """
    error_g = -torch.mean(prediction)
    
    error_g.backward()
    optimizer.step()

    return error_g

num_test_samples = 100
test_noise = noise(num_test_samples) # for intermediate testing

num_epochs = 50

import warnings
warnings.filterwarnings("ignore")
from sklearn.metrics import accuracy_score

g_errors = []
d_errors = []
d_loss_history = []
g_loss_history = []

for epoch in range(num_epochs):

  print(f'Epoch: {epoch + 1}/{num_epochs}')

  discriminator.train()
  generator.train()

  for n_batch, (real_batch,_) in enumerate(data_loader):

      if torch.cuda.is_available(): real_batch = real_batch.cuda()

      # training D (critic) for 5 times during each of the G training iterations
      for _ in range(5):
        # generate sentences w/ no gradients kept for the G
        with torch.no_grad():
          fake_data = generator(noise(real_batch.size(0)))

        # passing in D optimizer to update its parameters
        d_error = train_discriminator(d_optimizer, real_batch, fake_data)
        
        d_errors.append(d_error.item())

      # generating data for G training
      fake_data = generator(noise(real_batch.size(0)))

      # passing in G optimizer to update its parameters, skipping D's weights
      g_error = train_generator(g_optimizer, fake_data)

      g_errors.append(g_error.item())

  # putting G into evaluation mode to disable dropout and BN
  generator.eval()
  discriminator.eval()

  # generating 100 test sentences
  test_sent = generator(test_noise).data.cpu()
  # printing out most similar words per sentence
  print('_'*40)
  for i in test_sent:
    print(' '.join([model.wv.most_similar([y], topn=1)[0][0] for y in i.numpy()]))
    print(' '.join([str(model.wv.most_similar([y], topn=1)[0][1]) for y in i.numpy()]))
  
  print('_'*40)

  print(f'D loss: {np.mean(d_errors)}, G loss: {np.mean(g_errors)}')

  d_loss_history.append(np.mean(d_errors))
  g_loss_history.append(np.mean(g_errors))

  generator.train()
  discriminator.train()

"""Training progress isn't displayed here to save space (over 10k lines for 50 epochs)

G and D loss history
"""

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

figure(num=None, figsize=(13, 8), dpi=80, facecolor='w', edgecolor='k')
epochs = range(1,num_epochs+1)
plt.plot(epochs, g_loss_history, 'r', label='G loss')
plt.plot(epochs, d_loss_history, 'b', label='D loss')
plt.title('Generator and Discriminator Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend(loc='lower right')
font = {'family' : 'normal',
        'size'   : 12}
plt.rc('font', **font)
plt.locator_params(axis='x', nbins=50)
plt.show()

"""As we can see, for first 2 epochs G loss has been dropping while D loss has been rising up. D loss has stabilized after about 15th epoch, and G loss has been slowly approaching zero ever since. Convergence at the point of zero is a goal here. Note that we can keep track of the improvements in generated samples quality by simply looking at D loss. The Wasserstein distance (or at least an approximation of it used for WGANs) shows the minimum cost needed to turn one distribution into another, i.e. the cost of turning generated samples into real ones. As it comes close to zero, there's a very little cost.

We could've added minus sign for interpretabilty, then our loss graph would've looked something close to this (taken from one of the other experiments):

![Замещающий текст](http://drive.google.com/uc?export=view&id=1g-jzO3OrWzRs69Eyj04LEr3HSK7OxTTW)

# Test samples
"""

num_test_samples = 100
test_noise = noise(num_test_samples)

generator.eval()

test_sent = generator(test_noise).data.cpu()

similarities = [] # for tracking cosine similarities
  
print('_'*40)
for i in test_sent:
  print(' '.join([model.wv.most_similar([y], topn=1)[0][0] for y in i.numpy()]))
  print(' '.join([str(model.wv.most_similar([y], topn=1)[0][1]) for y in i.numpy()]))
  similarities.append([model.wv.most_similar([y], topn=1)[0][1] for y in i.numpy()])
  
print('_'*40)

"""It is clearly noticeable that most of the generated samples are still pretty meaningless and non-coherent. However, there are some relatively successful sentences:
\
\<s> i 'd like a brooch .

\<s> can you arrange a manchester program

\<s> is there foreign tastes brochure ?

\<s> can you favor a souvenir loan

\<s> the tooth is warm . \</s>

\<s> i am grey portion of .

\<s> i am gonna enter everything .

\<s> do i have a towel red

\<s> i 'd like to withdraw .

\<s> hello , i catch the connection

\<s> it 's the slope . \</s>

\<s> it 's kindly kindly . \</s>

\<s> it 's says thursday . \</s>

\<s> i 'd like a adult exposure

\<s> could you remove the cheapest program

\<s> could you continue the oxford cruise

\<s> do you have a seafood rush

\<s> i 'd like to ride ?

\<s> do you have a hat wishes

\<s> i 'd like slide disembarkation .

\<s> i 'd like a perm .

\<s> do you prefer some diving newspaper

\<s> i shall arrange a spoon .
\
For comparison, here are the examples of generated sentences from the original paper (note they have batches of size 100 as well, but provide only some of the generated sentences):

![Замещающий текст](http://drive.google.com/uc?export=view&id=1tb0VZtU0iDYf-_LdQZ3sBpex0Qc2D4FQ)

While it is hard to imagine real-life situations suiting for some of these phrases to be actually pronounced (to be fair, same applies to some of the sentences generated by GPT-3 that are too far away from starting user input), it's important to notice overall lexical consistency within them. E.g., there's not much common sense in the sentence 'I shall arrange a spoon', but it's valid in terms of preserving part of speech sequence (pronoun - auxiliary verb - verb - article - noun). Say, instead of "arrange" we could've had "pick" or "use" -  which brings us to the problem of interpretation quality. 

While with images (primary GANs area of appliance) there's one reliable way to estimate quality of generated samples (G output is channel-splitted pixel values used directly to draw an image), it's not that simple with text. Using word embeddings allows for immediate converting continious values into human-readable text, but this algorithm isn't a direct depiction (as with images and pixel values which are two forms of the same thing), instead it results from previous training and relies on imperfect vector representation.

Parameter used for such transformation is cosine similarity, ranging from 0 to 1, zero meaning 90° between word vectors (absolute dissimilarity), and one being 0° (same word). Needless to say that word context is not completely reliable source of data for deriving vector values (and therefore cosine similarity), as same context often contains words of completely different meaning and lexical characteristics (e.g. belonging to different parts of speech). It requires from generator to produce embeddings with cosine similarity perfectly close to 1, otherwise they could be easily confused with other words by nearest neighbor algorithm, thus breaking sentence coherence.

Average cosine similarity of vectors in test sentences
"""

# average similarity of each word and its nearest neighbor in the corpus 
# among 100 generated sentences
mean_sim = np.average(np.array(similarities), axis=0)

figure(num=None, figsize=(13, 8), dpi=80, facecolor='w', edgecolor='k')
words= range(1,8)
plt.plot(words, mean_sim, 'b', label='Average similarity')
plt.title('Average Cosine Similarity')
plt.xlabel('Words')
plt.ylabel('Similarity')
plt.legend()
font = {'family' : 'normal',
        'size'   : 12}
plt.rc('font', **font)
plt.show()

"""Clearly, the model easily learns that the sentence should start with `<s>`, and loses its confidence as it approaches the end of the sentence. It's somewhat similar to the results obtained by the authors of the original paper, however presented version of GAN seems to have less randomness in its output, with even the 7th word having a neighbor at `.75` similarity, while original GAN2vec model produces vectors of varying directions:

![Замещающий текст](https://storage.googleapis.com/groundai-web-prod/media%2Fusers%2Fuser_14%2Fproject_348561%2Fimages%2Fx4.png)

Cosine similarity drawbacks

Here are two examples of using cosine similarity for deriving NN. None of the top 10 words closest to "home" from the created embedding matrix has common meaning with "home". Moreover, 3 of them wouldn't fit the sentence as the ones being from the other parts of speech. As for "walk", only "cross" and "fly" resemble the original word.
"""

model.wv.most_similar('home')

model.wv.most_similar('walk')

"""For comparison, here are the closest neighbors for same words using pre-trained Glove embedding matrix of 50 dimensions. As we can see, in case of "home" nothing useful could be extracted either, but we clearly have some improvements with "walk". So it could be reasonable to consider a possibility of taking advantage of pre-trained embeddings rather than the ones trained directly on the dataset being used. It also could've been easier if the authors of the original paper had provided us with the exact methods and hyperparameters (e.g. context window size) they have used for embeddings training."""

import gensim
from gensim.models import KeyedVectors

filename = 'glove.6B.50d.txt.word2vec'
model1 = KeyedVectors.load_word2vec_format(filename, binary=False)

print(model1.wv.most_similar('home'))
print(model1.wv.most_similar('walk'))

"""It seems like provided embeddings will still be used, further research should be made in the area of developing the interpretation algorithm that would be more tolerant to variance in the generator output, shifting the burden from GAN model itself to output data converting. This process could be artificial in its nature, but it would compensate for a problem of text-numeric value converting (e.g. we could try to use Word Mover’s Distance instead of cosine similarity when picking nearest neighbors).

On the other hand, improving the model is always a desirable option, and it could be possible to include a differetiable function of choosing values with maximum cosine similarity for generated samples to either output layer of the generator (preferrably), or input layer of the discriminator, so that the discriminator (critic) would see the same picture we do when extracting word embeddings turing training and inference.
"""