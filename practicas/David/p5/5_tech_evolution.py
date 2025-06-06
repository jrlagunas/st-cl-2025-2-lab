# -*- coding: utf-8 -*-
"""5_tech_evolution.ipynb

# 5. Evolución de técnicas. Caso: POS tagging

<img src="https://nextcloud.tepezil.net/apps/files_sharing/publicpreview/Hiczm3M7NMTzGt4?file=/&fileId=65945&x=2560&y=1440&a=true&etag=1815fb54c51fb48b187ae17565238c81">

## Objetivos

- Describir la tarea de etiquetado *POS*
- Hacer una revisión incremental de métodos para resolver esta tarea
- Comparar el rendimiento de diferentes enfoques

## In deepth Part of Speech Tags

- Las palabras que conforman un texto tienen diferentes propiedades gramaticales y los lingüístas han propuesto categorías para agrupar las características comunes.

- Dichas clases son llamadas *Part of Speech (POS)*. Al etiquetar palabras con su respectiva POS tag hacemos explícitas ciertas propiedades gramaticales

- En *NLP*, el *POS tagging* consiste en asignar automáticamente a las palabras su *POS tag*.

### Clases de etiquetas POS

Las etiquetas POS se asignan a dos clases principales de palabras: abiertas y cerradas.

Las palabras de clase cerradas son aquellas que son relativamente estables en el tiempo y que tienen un rol funcional. Incluyen palabras como artículos, determinantes, pronombres, por mencionar algunas.

Las palabras de clases abiertas conforman el grueso del vocabulario. Todas las palabras "nuevas" que se van creando caerían en esta categoría. Las palabras de clases abiertas serían sustantivos, adjetivos, verbos y adverbios.

### Gramátical features

Las categorías básicas pueden reinarse o subcategorizarse. Por ejemplo, los sustantivos pueden agrparse en singulares y plurales. Incluso dependiendo de la lengua puede que haya mas o menos subcategorias. Por ejemplo, el aleman subdivide los sustantivos por generos: másculino, femenino y neutro.

Estas propiedades adicionales que especifican las categorías principales son llamadas **gramatical features**. Estas categorias varian dependiendo de las lenguas e incluyen numero, genero, persona, caso y tiempo, entre otras.

Cada sub-categoria tendrá un conjunto de valores posibles y variaran tambien con base en la etiqueta POS.

### POS tagging como desambiguación

Podemos pensar en el etiquetado POS como una tarea de desambigüación ya que las palabras pueden tener más de una etiqueta POS asociada. El objetivo será encontrar la etiqueta adecuada.

Ejemplos de palabras con etiquetas ambigüas:

- *book*
  - "**book/VERB** that flight"
  - "hand me that **book/NOUN**"
- *that*
  - "**That/DET** white table"
  - "Is not **that/ADV** easy"

## Corpus

### https://universaldependencies.org/
"""

# HIT: Restart session
!pip install numpy==1.26.4
!pip install -U gensim

URL = "https://raw.githubusercontent.com/UniversalDependencies/UD_Spanish-AnCora/refs/heads/master/es_ancora-ud-train.conllu"

import requests
from rich import print as rprint

raw_data = requests.get(URL).text

rprint(raw_data[:1000])

"""### Estandarización de POS tagsets y grammatical features: formato CoNLL

Hay dos esquemas de anotación populares:

1. El *Universal Part-of-Speech Tagset (UPOS)* para etiquetas POS
2. MULTEXT para *grammatical features*

Estos formatos fueron adoptados en los shared tasks de *The Conference on Natural Language Learning (CoNLL)* convirtiendose en el estandar *de facto* para entrenar modelos de *machine-learning* para resolver diversas tareas como: POS tagging, parse mofphologico, parseo de dependencias, entre otros.
"""

def get_raw_corpus(lang: str) -> str:
    """Obtiene el corpus crudo de Universal Dependencies

    Parameters
    ----------
    lang: str
        Idioma del corpus. Puede ser "es" o "en"

    Return
    ------
    str
        Corpus crudo en formato CoNLL
    """
    file_variants = ["train", "test", "dev"]
    result = dict.fromkeys(file_variants)
    DATASETS = {"es": ["UD_Spanish-AnCora", "es_ancora-ud"], "en": ["UD_English-GUM", "en_gum-ud"]}
    repo, file_name = DATASETS[lang]
    for variant in file_variants:
        url = f"https://raw.githubusercontent.com/UniversalDependencies/{repo}/refs/heads/master/{file_name}-{variant}.conllu"
        r = requests.get(url)
        result[variant] = r.text
    return result

raw_corpus = get_raw_corpus("en")
raw_spanish_corpus = get_raw_corpus("es")

rprint(raw_spanish_corpus["test"][:2500])

class Token(dict):
    """Modela cada renglon de un corpus en formato CoNLL
    """
    pass

t = Token(
    {
        "ID": "1",
        "FORM": "Las",
        "LEMMA": "el",
        "UPOS": "DET",
        "FEATS": "Definite=Def|Gender=Fem|Number=Plur|PronType=Art",
    }
)
rprint(t)

import re

class CoNLLDictorizer:
    """Convierte un corpus en formato CoNLL a una lista de diccionarios

    Define los métodos fit, transform y fit_transform para que
    sea compatible con la api de scikit-learn.

    Parameters
    ----------
    column_names: list
        Nombre de las columnas del corpus.
        Default: ["ID", "FORM", "LEMMA", "UPOS", "XPOS", "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"]
    sent_sep: str
        Separador de oraciones. Default: "\n\n"
    col_sep: str
        Separador de columnas. Default: "\t+"
    """
    DEFAULT_COLS = [
        "ID",
        "FORM",
        "LEMMA",
        "UPOS",
        "XPOS",
        "FEATS",
        "HEAD",
        "DEPREL",
        "HEAD",
        "DEPS",
        "MISC",
    ]

    def __init__(self, column_names: list=DEFAULT_COLS, sent_sep="\n\n", col_sep="\t+"):
        self.column_names = column_names
        self.sent_sep = sent_sep
        self.col_sep = col_sep

    def fit(self):
        pass

    def transform(self, corpus: str) -> list[Token]:
        """Convierte un corpus en formato CoNLL a una lista de diccionarios.

        Parameters
        ----------
        corpus: str
            Corpus en formato CoNLL

        Return
        ------
        list
            Lista de diccionarios con los tokens del corpus
        """
        corpus = corpus.strip()
        sentences = re.split(self.sent_sep, corpus)
        return list(map(self._split_in_words, sentences))

    def fit_transform(self, corpus):
        return self.transform(corpus)

    def _split_in_words(self, sentence: list[str]) -> list[Token]:
        """Preprocesa una oración en formato CoNLL

        Ignora las lineas que comienzan con "#" y separa
        cada línea en un diccionario.

        Parameters
        ----------
        sentence: str
            Oracion en formato CoNLL

        Return
        ------
        list
            Lista de diccionarios con los tokens de la oración
        """
        rows = re.split("\n", sentence)
        rows = [row for row in rows if row[0] != "#"]
        return [
            Token(dict(zip(self.column_names, re.split(self.col_sep, row))))
            for row in rows
        ]

conll_dict = CoNLLDictorizer()

corpora = {}
for variant in ["train", "test", "dev"]:
    corpora[variant] = conll_dict.transform(raw_corpus[variant])

spanish_corpora = {}
for variant in ["train", "test", "dev"]:
    spanish_corpora[variant] = conll_dict.transform(raw_spanish_corpus[variant])

rprint(corpora["train"][0])

"""## Baseline: Look-up dictionary

### 0. Usar el POS tag más frecuente

Considerar el uso de las palabras con base en entradas de diccionario. Generalmente las palabras de diccionarios tienen un POS tag asociado o, al menos, tienen una preferencia fuerte por alguna etiqueta a pesar de que una palabra pueda ser ambigua.

Este sera nuestro *baseline*. El baseline es un termino ampliamente utilizado en NLP para referirnos a un punto de partida que usualmente es fácil de implementar obteniendo una métrica con métodos "simples".

Con base en este baseline evaluaremos si métodos más complejos tienen un mejor desempeño.
"""

from collections import Counter

def calculate_pos_distribution(corpus: list[list[Token]], word_key="FORM", pos_key="UPOS"):
    """Calcula la distribución de POS para cada palabra

    Parameters
    ----------
    corpus: list[Token]
        Corpus en formato CoNLL
    word_key: str
        Nombre de la columna que contiene la palabra. Default: "FORM"
    pos_key: str
        Nombre de la columna que contiene la etiqueta POS. Default: "UPOS"

    Return
    ------
    dict
        Diccionario con la distribución de POS para cada palabra
    """
    pos_distributions = {}
    for sentence in corpus:
        for token in sentence:
            word = token[word_key]
            pos_tag = token[pos_key]
            if word not in pos_distributions:
                pos_distributions[word] = Counter()
            pos_distributions[word][pos_tag] += 1
    return pos_distributions

pos_dist = calculate_pos_distribution(corpora["train"])
spanish_pos_dist = calculate_pos_distribution(spanish_corpora["train"])

for i, word in enumerate(pos_dist):
    rprint(f"{word} -> {pos_dist[word]}")
    if i == 10:
        break

for i, word in enumerate(spanish_pos_dist):
    rprint(f"{word} -> {spanish_pos_dist[word]}")
    if i == 10:
        break

baseline = {}
for word in pos_dist:
    # Elegimos la etiqueta POS más frecuente
    baseline[word] = max(pos_dist[word], key=pos_dist[word].get)

spanish_baseline = {}
for word in spanish_pos_dist:
    spanish_baseline[word] = max(spanish_pos_dist[word], key=spanish_pos_dist[word].get)

rprint(baseline)

test_sent = input(">> ")
for word in test_sent.split():
    rprint(word, "->", f"[red]{baseline.get(word, 'UNK')}")

spanish_test_sent = input(">> ")
for word in spanish_test_sent.split():
    rprint(word, "->", f"[red]{spanish_baseline.get(word, 'UNK')}")

"""El conjuto de pruebas puede contener palabras no vistas en nuestro conjunto de entrenamiento. Podemos aplicar una estrategía simple y obtener la etiqueta más común de nuestro conjunto de validación."""

def unseen_words_pos_dist(corpus: list[list[Token]], model: dict, word_key="FORM", pos_key="UPOS"):
    """Obtiene la distribución de POS de las palabras no vistas en el modelo

    Parameters
    ----------
    corpus: list[Token]
        Corpus en formato CoNLL
    model: dict
        Modelo de lenguaje
    """
    unseen_words = Counter()
    for sentence in corpus:
        for token in sentence:
            if not token[word_key] in model:
                unseen_words[token[pos_key]] += 1
    return unseen_words

unseen_pos_dist = unseen_words_pos_dist(corpora["dev"], baseline)

spanish_unseen_pos_dist = unseen_words_pos_dist(spanish_corpora["dev"], spanish_baseline)

rprint(unseen_pos_dist)

rprint(spanish_unseen_pos_dist)

BACKOFF_POS = max(unseen_pos_dist, key=unseen_pos_dist.get)
rprint(f"Backoff POS: {BACKOFF_POS}")

SPANISH_BACKOFF_POS = max(spanish_unseen_pos_dist, key=spanish_unseen_pos_dist.get)
rprint(f"Spanish Backoff POS: {SPANISH_BACKOFF_POS}")

"""### Probando nuestro baseline"""

def get_predictions(corpus: list[list[Token]], model: dict, backoff_pos: str, word_key="FORM", pos_key="UPOS"):
    """Obtiene las predicciones del modelo y el gold standar

    Parameters
    ----------
    corpus: list[Token]
        Corpus en formato CoNLL
    model: dict
        Modelo de lenguaje
    """
    predictions = []
    gold_standar = []
    for sentence in corpus:
        for token in sentence:
            word = token[word_key]
            gold = token[pos_key]
            predictions.append(model.get(word, backoff_pos))
            gold_standar.append(gold)
    assert len(predictions) == len(gold_standar)
    return predictions, gold_standar

predictions, gold_standar = get_predictions(corpora["test"], baseline, BACKOFF_POS)

def get_accuracy(predictions: list[str], gold_standar: list[str]) -> float:
    """Obtiene la precisión del modelo

    Parameters
    ----------
    predictions: list[str]
        Predicciones del modelo
    gold_standar: list[str]
        Etiquetas gold standar

    Return
    ------
    float
        Precisión del modelo
    """
    correct = 0
    for p, g in zip(predictions, gold_standar):
        if p == g:
            correct += 1
    return (correct / len(predictions))

baseline_accuracy = get_accuracy(predictions, gold_standar)
rprint(f"Accuracy [green]ENGLISH[/]: {baseline_accuracy * 100:.2f}%")

spanish_predictions, spanish_gold_standar = get_predictions(
    spanish_corpora["test"], spanish_baseline, SPANISH_BACKOFF_POS)

rprint(f"Accuracy [Spanish]: {get_accuracy(spanish_predictions, spanish_gold_standar) * 100:.2f}%")

"""## Clasificadores Lineales

- Los clasificadores lineales como regresion logistica o feed-forwad nets son técnicas númericas eficientes para estimar etiquetas POS
- Como entrada el etiquetador leerá la oración de entrada y usando un modelo previamente entrenado predecirá la etiqueta POS más probable
- Para entrenar estos modelos, tipicamente, se tienen que extraer con conjunto de características (*features*) de las palabras aledañas

### Preprocesamiento
"""

def extract_pairs(sentence: list[Token], word_key="FORM", pos_key="UPOS"):
    """ Extrae las palabras y sus etiquetas POS

    Parameters
    ----------
    sentence: list[Token]
        Oracion en formato CoNLL
    word_key: str
        Nombre de la columna que contiene la palabra. Default: "FORM"
    pos_key: str
        Nombre de la columna que contiene la etiqueta POS. Default: "UPOS"

    Return
    ------
    tuple
        Tupla con las palabras y sus etiquetas POS
    """
    _input, target = [], []
    for token in sentence:
        _input += [token[word_key]]
        target += [token.get(pos_key, None)]
    return _input, target

train_pairs = [extract_pairs(sentence) for sentence in corpora["train"]]
val_pairs = [extract_pairs(sentence) for sentence in corpora["dev"]]
test_pairs = [extract_pairs(sentence) for sentence in corpora["test"]]

rprint(train_pairs[-1])

train_sent_words, train_sent_pos = zip(*train_pairs)
val_sent_words, val_sent_pos = zip(*val_pairs)
test_sent_words, test_sent_pos = zip(*test_pairs)

for word, pos in zip(train_sent_words[42], train_sent_pos[42]):
    rprint(f"{word}--> [red]{pos}")

def extract_features(sentence: list[str], context: int=2) -> list:
    """Extraer las features de cada oración

    Para tener siempre la misma cantidad de features
    por oración aplica un ventaneo llenando los espacios
    restantes con "<BOS>" y "<EOS>"

    Parameters
    ----------
    sentence: list[str]
        Oracion en formato CoNLL
    context: int
        Cantidad de palabras a la izquierda y derecha de la palabra actual. Default: 2

    Return
    ------
    list
        Lista de diccionarios con las features de cada palabra
    """
    start_pad = ["<BOS>"] * context
    end_pad = ["<EOS>"] * context
    sentence = start_pad + sentence + end_pad
    features = []
    for i in range(len(sentence) - 2 * context):
        aux = []
        for j in range(2 * context + 1):
            aux += [sentence[i + j]]
        features += [aux]
    features = [dict(enumerate(feature)) for feature in features]
    return features

rprint(extract_features(train_sent_words[42]))

def extract_corpus_features(words_set: list[list[str]], pos_tags_set: list[list[str]]):
    """Extraer las features del corpus

    Parameters
    ----------
    words_set: list[list[str]]
        Lista de listas con las palabras de cada oración
    pos_tags_set: list[list[str]]
        Lista de listas con las etiquetas POS de cada oración

    Return
    ------
    tuple
        Tupla con las features y las etiquetas POS
    """
    X_features = [row for sent in words_set for row in extract_features(sent)]
    y_features = [pos for sent in pos_tags_set for pos in sent]
    return X_features, y_features

X_train_features, y_train_features = extract_corpus_features(train_sent_words, train_sent_pos)
X_val_features, y_val_features = extract_corpus_features(val_sent_words, val_sent_pos)
X_test_features, y_test_features = extract_corpus_features(test_sent_words, test_sent_pos)

rprint(X_train_features[0])

rprint(y_train_features[0])

"""## 1. Regresión logística"""

import numpy as np
from sklearn.feature_extraction import DictVectorizer

vectorizer = DictVectorizer()
X_train = vectorizer.fit_transform(X_train_features)

X_train.shape

v = DictVectorizer(sparse=False)

rprint(X_train_features[0:2])
result = v.fit_transform(X_train_features[0:2])
result

rprint(v.inverse_transform(result))

"""### Aplicando el clasificador"""

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# Commented out IPython magic to ensure Python compatibility.
# %%time
# classifier = LogisticRegression()
# logistic_model = classifier.fit(X_train, y_train_features)

def predict_sentence(sentence: list[Token], model: LogisticRegression, vectorizer: DictVectorizer, ppos_key="PPOS") -> list[Token]:
    """Realiza la predicción de las etiquetas POS para una oración

    Parameters
    ----------
    sentence: list[Token]
        Oración en formato CoNLL
    model: LogisticRegression
        Modelo de clasificador
    vectorizer: DictVectorizer
        Vectorizador de features

    Return
    ------
    list[Token]
        Oración en formato CoNLL con las etiquetas POS predichas
    """
    sent_words, _ = extract_pairs(sentence)
    sent_features = extract_features(sent_words)
    X_test = vectorizer.transform(sent_features)
    y_pred_vec = model.predict(X_test)
    for token, y_pred in zip(sentence, y_pred_vec):
        # Add predicted pos
        token[ppos_key] = y_pred
    return sentence

correct = 0
tokens_count = 0
for sentence in corpora["test"]:
    pred_sent = predict_sentence(sentence, logistic_model, vectorizer)
    for token in pred_sent:
        tokens_count += 1
        if token["UPOS"] == token["PPOS"]:
            correct += 1

logistic_accuracy = (correct / tokens_count)
rprint(f"Accuracy (Logistic): {logistic_accuracy * 100:.2f}%")
rprint(f"Δ from baseline: {(logistic_accuracy - baseline_accuracy) * 100:.2f}%")

"""## 2. Feed-forward Networks"""

import numpy as np
import torch
from torch import nn
from torch.utils.data import TensorDataset, DataLoader

device = "cuda" if torch.cuda.is_available() else "cpu"
rprint(f"Working on device={device}")

"""### 2.1 Single layer"""

# Nos aseguramos de la consistencia de los vectores
ff_vectorizer = DictVectorizer(sparse=False, dtype=np.float32)

X_train_ff = ff_vectorizer.fit_transform(X_train_features)
X_val_ff = ff_vectorizer.transform(X_val_features)
X_test_ff = ff_vectorizer.transform(X_test_features)

X_train_t = torch.from_numpy(X_train_ff)
X_val_t = torch.from_numpy(X_val_ff)
X_test_t = torch.from_numpy(X_test_ff)

"""$y$ deberá ser un vector de indices a diferencia de scikitlearn que eran listas de palabras"""

idx2pos = dict(enumerate(set(y_train_features)))
pos2idx = {v: k for k, v in idx2pos.items()}

"""Convertimos las etiquetas POS"""

y_train_t = torch.LongTensor(list(map(lambda key: pos2idx.get(key), y_train_features)))
y_val_t = torch.LongTensor(list(map(lambda key: pos2idx.get(key), y_val_features)))
y_test_t = torch.LongTensor(list(map(lambda key: pos2idx.get(key), y_test_features)))

"""Creamos los objetos para cargar los datasets en la red"""

train_dataset = TensorDataset(X_train_t, y_train_t)
val_dataset = TensorDataset(X_val_t, y_val_t)
test_dataset = TensorDataset(X_test_t, y_test_t)

train_dataloader = DataLoader(train_dataset, batch_size=512, shuffle=True)
val_dataloader = DataLoader(val_dataset, batch_size=2048, shuffle=False)
test_dataloader = DataLoader(test_dataset, batch_size=2048, shuffle=False)

LR = 0.005
EPOCHS = 10

class FeedForward(nn.Module):
    def __init__(self, input_size: int, output_size: int):
        super().__init__()
        self.linear = nn.Linear(input_size, output_size)

    def forward(self, x):
        return self.linear(x)

ff_model = FeedForward(X_train_t.size(dim=1), len(pos2idx)).to(device)
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.NAdam(ff_model.parameters(), lr=LR)

def evaluate_ff(model: nn.Module, loss_fn: nn.Module, dataloader: DataLoader):
    model.eval()
    with torch.no_grad():
        total_loss = 0
        accuracy = 0
        batch_count = 0
        for X_batch, y_batch in dataloader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            batch_count += 1
            y_batch_pred = model(X_batch)
            total_loss += loss_fn(y_batch_pred, y_batch).item()
            accuracy += (sum(torch.argmax(y_batch_pred, dim=-1) == y_batch) / y_batch.size(dim=0)).item()
    return total_loss / batch_count, accuracy / batch_count

"""#### Training loop"""

from tqdm.notebook import trange, tqdm
from google.colab import drive
drive.mount('/content/drive', force_remount=True)

MODELS_PATH = "/content/drive/MyDrive/models"

ff_history = {"accuracy": [], "loss": [], "val_loss": [], "val_accuracy": []}
for epoch in trange(EPOCHS):
    train_loss, train_acc, batch_count = 0, 0, 0
    ff_model.train()
    for X_batch, y_batch in tqdm(train_dataloader):
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        batch_count += 1
        y_batch_pred = ff_model(X_batch)
        loss = loss_fn(y_batch_pred, y_batch)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        train_acc += (sum(torch.argmax(y_batch_pred, dim=-1) == y_batch) / y_batch.size(dim=0)).item()
        train_loss += loss.item()
    ff_model.eval()
    with torch.no_grad():
        ff_history["accuracy"].append(train_acc / batch_count)
        ff_history["loss"].append(train_loss / batch_count)
        val_loss, val_acc = evaluate_ff(ff_model, loss_fn, val_dataloader)
        ff_history["val_loss"].append(val_loss)
        ff_history["val_accuracy"].append(val_acc)
    torch.save(ff_model.state_dict(), f"{MODELS_PATH}/pos_tagger_ff_{device}_{epoch}.pth")
torch.save(ff_history, f"{MODELS_PATH}/pos_tagger_ff.history")

import matplotlib.pyplot as plt

def plot_history(history: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    axes[0].plot(history["accuracy"], label="Accuracy")
    axes[0].plot(history["val_accuracy"], label="Validation accuracy")
    axes[0].set_title("Accuracy")
    axes[0].set_xlabel("Epochs")
    axes[0].set_ylabel("Accuracy")
    axes[0].legend()

    axes[1].plot(history["loss"], label="Loss")
    axes[1].plot(history["val_loss"], label="Validation loss")
    axes[1].set_title("Loss")
    axes[1].set_xlabel("Epochs")
    axes[1].set_ylabel("Loss")
    axes[1].legend()

    plt.show()

plot_history(ff_history)

_, accuracy_ff = evaluate_ff(ff_model, loss_fn, test_dataloader)

rprint(f"Accuracy (FF): {accuracy_ff * 100:.2f}%")
rprint(f"Δ from baseline: {(accuracy_ff - baseline_accuracy) * 100:.2f}%")
rprint(f"Δ from logistic: {(accuracy_ff - logistic_accuracy) * 100:.2f}%")

"""### 2.2 Embeddings

Contruir un modelo con más capas es relativamente sencillo gracias a pytorch. En la red anterior las palabras eran one-hot vectors.

#### ¿Qué problemas ven a esto?

- Matrices repletas de 0's bastante grandes
- No se toma en cuenta posibles relaciones entre los vectores de palabras
- Utilizaremos un modelo de embeddings pre-entrenado
"""

import gensim.downloader as gensim_api
from gensim.models.keyedvectors import KeyedVectors

rprint(gensim_api.info()['models'].keys())

vectors = gensim_api.load("glove-wiki-gigaword-100")

def get_embeddings(model: KeyedVectors) -> dict[str, torch.FloatTensor]:
    """Obtiene los embeddings de las palabras del modelo

    Parameters
    ----------
    model: KeyedVectors
        Modelo de embeddings

    Return
    ------
    dict[str, torh.FloatTensor]
        Diccionario con las palabras como keys y los embeddings como values
    """
    embeddings = {}
    for word, idx in model.key_to_index.items():
        embeddings[word] = torch.FloatTensor(vectors[idx].copy())
    return embeddings

embeddings = get_embeddings(vectors)

corpus_words = [
    value.lower() for feature in X_train_features
    for value in feature.values()
]
corpus_words = sorted(set(corpus_words))

embeddings_words = embeddings.keys()
vocabulary = set(corpus_words + list(embeddings_words))

idx2word = dict(enumerate(vocabulary), start=1)
word2idx = {v: k for k, v in idx2word.items()}

for train_feature in X_train_features:
    for word in train_feature:
        train_feature[word] = word2idx[train_feature[word].lower()]

for val_feature in X_val_features:
    for word in val_feature:
        val_feature[word] = word2idx.get(val_feature[word].lower(), 0)

for test_feature in X_test_features:
    for word in test_feature:
        test_feature[word] = word2idx.get(test_feature[word].lower(), 0)

embedd_vectorizer = DictVectorizer(sparse=False, dtype=np.int64)

X_train_emb = embedd_vectorizer.fit_transform(X_train_features)
X_val_emb = embedd_vectorizer.transform(X_val_features)
X_test_emb = embedd_vectorizer.transform(X_test_features)

X_train_emb = torch.from_numpy(X_train_emb)
X_val_emb = torch.from_numpy(X_val_emb)
X_test_emb = torch.from_numpy(X_test_emb)

"""Notemos que las matrices resultantes contienen indices y no one-hot vectors. TODO mostrarlo"""

EMBEDDING_DIM = 100

embedding_table = torch.randn((len(vocabulary) + 1, 100)) / 10

"""Llenamos la tabla con los valores de los embeddings extraidos de GLoVe si estan en el modelo"""

for word in vocabulary:
    if word in embeddings:
        embedding_table[word2idx[word]] = embeddings[word]

idx2pos = dict(enumerate(set(y_train_features)))
pos2idx = {v: k for k, v in idx2pos.items()}

"""Convertimos las etiquetas POS"""

y_train_e = torch.LongTensor(list(map(lambda key: pos2idx.get(key), y_train_features)))
y_val_e = torch.LongTensor(list(map(lambda key: pos2idx.get(key), y_val_features)))
y_test_e = torch.LongTensor(list(map(lambda key: pos2idx.get(key), y_test_features)))

"""Creamos los objetos para cargar los datasets en la red"""

train_dataset = TensorDataset(X_train_emb, y_train_e)
val_dataset = TensorDataset(X_val_emb, y_val_e)
test_dataset = TensorDataset(X_test_emb, y_test_e)

train_dataloader = DataLoader(train_dataset, batch_size=512, shuffle=True)
val_dataloader = DataLoader(val_dataset, batch_size=2048, shuffle=False)
test_dataloader = DataLoader(test_dataset, batch_size=2048, shuffle=False)

LR = 0.005
EPOCHS = 10

class EmbeddingsModel(nn.Module):
    def __init__(self,
                 embedding_table,
                 num_classes: int,
                 freeze_embeddings: bool = False):
        super().__init__()
        self.embedding = nn.Embedding.from_pretrained(
            embedding_table,
            freeze=freeze_embeddings
            )
        self.flatten = nn.Flatten()
        self.linear = nn.Linear(5 * embedding_table.size(dim=1), num_classes)

    def forward(self, sentence):
        embeds = self.embedding(sentence)
        flatten = self.flatten(embeds)
        logist = self.linear(flatten)
        return logist

embeddings_model = EmbeddingsModel(embedding_table, len(pos2idx)).to(device)
loss_fn = nn.CrossEntropyLoss()
optimizer = torch.optim.NAdam(embeddings_model.parameters(), lr=LR)

"""#### Training loop (with embeddings)"""

from tqdm.notebook import trange, tqdm

MODELS_PATH = "/content/drive/MyDrive/models"

emb_history = {"accuracy": [], "loss": [], "val_loss": [], "val_accuracy": []}
for epoch in trange(EPOCHS):
    train_loss, train_acc, batch_count = 0, 0, 0
    embeddings_model.train()
    for X_batch, y_batch in tqdm(train_dataloader):
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        batch_count += 1
        y_batch_pred = embeddings_model(X_batch)
        loss = loss_fn(y_batch_pred, y_batch)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        train_acc += (sum(torch.argmax(y_batch_pred, dim=-1) == y_batch) / y_batch.size(dim=0)).item()
        train_loss += loss.item()
    embeddings_model.eval()
    with torch.no_grad():
        emb_history["accuracy"].append(train_acc / batch_count)
        emb_history["loss"].append(train_loss / batch_count)
        # Reutilizamos la función de evaluación de FF
        val_loss, val_acc = evaluate_ff(embeddings_model, loss_fn, val_dataloader)
        emb_history["val_loss"].append(val_loss)
        emb_history["val_accuracy"].append(val_acc)
    torch.save(embeddings_model.state_dict(), f"{MODELS_PATH}/pos_tagger_emb_{device}_{epoch}.pth")
torch.save(emb_history, f"{MODELS_PATH}/pos_tagger_emb.history")

plot_history(emb_history)

_, accuracy_emb = evaluate_ff(embeddings_model, loss_fn, test_dataloader)
rprint(f"Accuracy (Embeddings): {accuracy_emb * 100:.2f}%")
rprint(f"Δ from baseline: {(accuracy_emb - baseline_accuracy) * 100:.2f}% ({baseline_accuracy * 100:.2f}%)")
rprint(f"Δ from logistic: {(accuracy_emb - logistic_accuracy) * 100:.2f}% ({logistic_accuracy * 100:.2f}%)")
rprint(f"Δ from ff: {(accuracy_emb - accuracy_ff) * 100:.2f}% ({accuracy_ff * 100:.2f}%)")

"""## 3. Recurrent Neural Nets (RNNs)

Las redes recurrentes, *Recurrent Neural Networks (RNN)*, son una arquitectura que integra la noción temporal presente en el lenguaje de forma natural.

A diferencia de una red *Feedforward* donde tenemos una ventana fija que varía las *RNNs* representan el contexto mediante conexiones recurrentes, permitiendo que las decisiones del modelo tomen encuenta información de una cantidad variable de palabras en el pasado.

![](https://nextcloud.tepezil.net/apps/files_sharing/publicpreview/XZqZjcnrkttwCF2?file=/&fileId=65865&x=2560&y=1440&a=true&etag=713f6269c3d7bf51a3af36907f7066fa)

> Tomada de Speech and Language Processing (Jurafsky, 2025 *draft*)

En este enfoque las entradas serán embeddings de palabras y las salidas serán las distribuciones de probabilidades (generadas por la capa $softmax$) de un conjunto de etiquetas.

Dicho de otro modo, hasta hora hemos predecido las etiquetas en $t_i$ con base en las palabras que le rodean $(w_{i-2}, w_{i-1}, w_{i}, w_{i+1}, w_{i+2})$.

Una mejora a considerar podría ser incluir las predicciones previas en el vector de características para tener más información en el contexto:

$$
P(t_i|w_{i-2}, w_{i-1}, w_{i}, w_{i+1}, w_{i+2},t_{i-2},t_{i-1})
$$

### Sabores de RNNs

Las RNNs son bastante flexibles y no se limitan a considerar la entrada de la red los embeddings de palabras y la salida vectores útiles para predecir etiquetas, palabras o secuencias.

#### Stacked RNNs

Las salidas de una RNN se pueden utilizar como secuencias de entrada de otras RNNs teniendo como resultado *Stacked RNNs*. Esta arquitectura consiste en multiples redes recurrentes donde la salida de una red servirá como entrada de otra.

Generalmente las *stacked RNNs* son mejores que las RNNs de una sola capa. Una razón de esto podría ser que la red considera representaciones a diferentes niveles de abstracción a traves de las capas. Sin embargo, con forme aumenta el número de *stacks* el costo de entrenamiento aumenta rápidamente.

![](https://lena-voita.github.io/resources/lectures/lang_models/neural/rnn/multi_layer-min.png)

> Tomada de Lena Voita, [language modeling](https://lena-voita.github.io/nlp_course/language_modeling.html)

#### Bidirectional RNNs

Las RNNs usan información del contexto de izquierda a derecha para hacer alguna predicción en $t$. Sin embargo, dependiendo de la aplicación es deseable considerar el contexto de la derecha tambien.

Una forma de hacer esto es unir dos RNNs, una que compute de izquierda a derecha y otra de derecha a izquierda y al final concatenar sus representaciones.

Coinsideremos lo siguiente:

$$
h^{f}_{t} = RNN_{forward}(x_1,...,x_t)
$$

$$
h^{b}_{t} = RNN_{backward}(x_t,...,x_n)
$$

Una *bidirectional RNN* combinará el cómputo de ambas representaciones y las concatenará para obtener una sola representación:

$$
h_t = [h^{f}_{t} \otimes h^{b}_{t}]
$$

dónde $\otimes$ representa la operación *mean vector concatenation*.

Este tipo de redes han probado ser bastante buenas para tareas de clasificación de secuencias.

![](https://nextcloud.tepezil.net/apps/files_sharing/publicpreview/qsr9LeAro8FTJ4L?file=/&fileId=65980&x=2560&y=1440&a=true&etag=b4c980855f2cedc4b5af6fb719dae7e0)
"""

# Extracting the training set
rprint(train_sent_words[0])
rprint(train_sent_pos[0])

# Todas las palabras a minusculas para que sea compatible con GLoVe
train_sent_words_rnn = [list(map(str.lower, sentence)) for sentence in train_sent_words]
val_sent_words_rnn = [list(map(str.lower, sentence)) for sentence in val_sent_words]
test_sent_words_rnn = [list(map(str.lower, sentence)) for sentence in test_sent_words]

"""#### Indices"""

corpus_words_rnn = sorted(set([word for sentence in train_sent_words_rnn for word in sentence]))
pos_list_rnn = sorted(set([pos for sentence in train_sent_pos for pos in sentence]))

embeddings_words_rnn = embeddings.keys()
vocabulary = set(corpus_words_rnn + list(embeddings_words_rnn))

# Start on 2 because id 0 will be pad simbol and 1 will be UNK
idx2word = dict(enumerate(vocabulary), start=2)
idx2pos = dict(enumerate(pos_list_rnn), start=1)

word2idx = {v: k for k, v in idx2word.items()}
pos2idx = {v: k for k, v in idx2pos.items()}

def to_index(corpus: list[list[str]], word2idx: dict[str, int], unk_id: int = 1) -> torch.LongTensor:
    indexes = []
    for sent in corpus:
        sent_indexes = torch.LongTensor(
            list(map(lambda word: word2idx.get(word, unk_id), sent))
        )
        indexes += [sent_indexes]
    return indexes

t = to_index(train_sent_words_rnn[:2], word2idx)

for sent in t:
    for word in sent:
        print(idx2word[int(word)])

X_train_idx_rnn = to_index(train_sent_words_rnn, word2idx)
Y_train_idx_rnn = to_index(train_sent_pos, pos2idx)

X_val_idx_rnn = to_index(val_sent_words_rnn, word2idx)
Y_val_idx_rnn = to_index(val_sent_pos, pos2idx)

X_test_idx_rnn = to_index(test_sent_words_rnn, word2idx)
Y_test_idx_rnn = to_index(test_sent_pos, pos2idx)

"""#### Padding"""

from torch.nn.utils.rnn import pad_sequence

pad_sequence(X_train_idx_rnn[41:43], batch_first=True, padding_value=0)

X_train_rnn = pad_sequence(X_train_idx_rnn, batch_first=True, padding_value=0)
Y_train_rnn = pad_sequence(Y_train_idx_rnn, batch_first=True, padding_value=0)

X_val_rnn = pad_sequence(X_val_idx_rnn, batch_first=True, padding_value=0)
Y_val_rnn = pad_sequence(Y_val_idx_rnn, batch_first=True, padding_value=0)

X_test_rnn = pad_sequence(X_test_idx_rnn, batch_first=True, padding_value=0)
Y_test_rnn = pad_sequence(Y_test_idx_rnn, batch_first=True, padding_value=0)

"""#### Embeddings para RNN"""

EMBEDDING_DIM = 100

embedding_table = torch.randn((len(vocabulary) + 2, EMBEDDING_DIM)) / 10

for word in vocabulary:
    if word in embeddings:
        embedding_table[word2idx[word]] = embeddings[word]

"""### La Recurrent Neural Net con pytorch"""

class RnnModel(nn.Module):
    def __init__(self,
                 embedding_table,
                 hidden_size,
                 num_classes: int,
                 freeze_embeddings: bool = False,
                 num_layers: int=1,
                 bidirectional=False):
        super().__init__()
        embedding_dim = embedding_table.size(dim=-1)
        self.embedding = nn.Embedding.from_pretrained(
            embedding_table,
            freeze=freeze_embeddings,
            padding_idx=0
            )
        self.recurrent = nn.RNN(
            embedding_dim,
            hidden_size,
            num_layers=num_layers,
            bidirectional=bidirectional,
            batch_first=True
        )
        if bidirectional:
            # Dos veces las unidades si es bidireccional
            self.linear = nn.Linear(hidden_size * 2, num_classes)
        else:
            self.linear = nn.Linear(hidden_size, num_classes)

    def forward(self, sentence):
        embeds = self.embedding(sentence)
        rec_out, _ = self.recurrent(embeds)
        logist = self.linear(rec_out)
        return logist

rnn_model = RnnModel(
    embedding_table,
    hidden_size=100,
    num_classes=len(pos2idx) + 1,
    freeze_embeddings=False,
    num_layers=2,
    bidirectional=True
).to(device)

loss_fn = nn.CrossEntropyLoss(ignore_index=0)
optimizer = torch.optim.NAdam(rnn_model.parameters(), lr=0.005)

"""#### Training loop"""

EPOCHS = 15

train_dataset_rnn = TensorDataset(X_train_rnn, Y_train_rnn)
train_dataloader_rnn = DataLoader(train_dataset_rnn, batch_size=512, shuffle=True)

val_dataset_rnn = TensorDataset(X_val_rnn, Y_val_rnn)
val_dataloader_rnn = DataLoader(val_dataset_rnn, batch_size=2048, shuffle=False)

test_dataset_rnn = TensorDataset(X_test_rnn, Y_test_rnn)
test_dataloader_rnn = DataLoader(test_dataset_rnn, batch_size=2048, shuffle=False)

def evaluate_rnn(model: nn.Module, loss_fn: nn.Module, dataloader: DataLoader):
    model.eval()
    with torch.no_grad():
        total_loss = 0
        accuracy = 0
        t_words = 0
        for X_batch, y_batch in dataloader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            y_batch_pred = model(X_batch)
            current_loss = loss_fn(
                y_batch_pred.reshape(-1, y_batch_pred.size(dim=-1)),
                y_batch.reshape(-1)
            )
            n_words = torch.sum(y_batch > 0).item()
            t_words += n_words
            total_loss += n_words + current_loss.item()
            accuracy += torch.mul(
                torch.argmax(y_batch_pred, dim=-1) == y_batch,
                y_batch > 0).sum().item()
        return total_loss / t_words, accuracy / t_words

MODELS_PATH = "/content/drive/MyDrive/models"

rnn_history = {"accuracy": [], "loss": [], "val_loss": [], "val_accuracy": []}
for epoch in trange(EPOCHS):
    train_loss, train_acc, t_words = 0, 0, 0
    rnn_model.train()
    for X_batch, y_batch in tqdm(train_dataloader_rnn):
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        y_batch_pred = rnn_model(X_batch)
        loss = loss_fn(
            y_batch_pred.reshape(-1, y_batch_pred.size(dim=-1)),
            y_batch.reshape(-1)
            )
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        with torch.no_grad():
            n_words = torch.sum(y_batch > 0).item()
            t_words += n_words
            train_loss += n_words * loss.item()
            train_acc += torch.mul(
                torch.argmax(y_batch_pred, dim=-1) == y_batch,
                y_batch > 0).sum().item()

    rnn_model.eval()
    with torch.no_grad():
        rnn_history["accuracy"].append(train_acc / t_words)
        rnn_history["loss"].append(train_loss / t_words)
        val_loss, val_acc = evaluate_rnn(rnn_model, loss_fn, val_dataloader_rnn)
        rnn_history["val_loss"].append(val_loss)
        rnn_history["val_accuracy"].append(val_acc)
    torch.save(rnn_model.state_dict(), f"{MODELS_PATH}/pos_tagger_rnn_{device}_{epoch}.pth")
torch.save(rnn_history, f"{MODELS_PATH}/pos_tagger_rnn.history")

plot_history(rnn_history)

_, accuracy_rnn = evaluate_rnn(rnn_model, loss_fn, test_dataloader_rnn)
rprint(f"Accuracy (RNN): {accuracy_rnn * 100:.2f}%")
rprint(f"Δ accuracy (from baseline): {(accuracy_rnn - baseline_accuracy) * 100:.2f}%")
rprint(f"Δ accuracy (from logistic): {(accuracy_rnn - logistic_accuracy) * 100:.2f}% ({logistic_accuracy * 100:.2f}%)")
rprint(f"Δ accuracy (from ff): {(accuracy_rnn - accuracy_ff) * 100:.2f}% ({accuracy_ff * 100:.2f}%)")
rprint(f"Δ accuracy (from embeddings): {(accuracy_rnn - accuracy_emb) * 100:.2f}% ({accuracy_emb * 100:.2f}%)")

"""# Práctica 5: Tech evolution. Caso POS Tagging

**Fecha de entrega: 13 de Abril 2025 11:59pm**

- Obten los embeddings de 100 palabras al azar del modelo RNN visto en clase
  - Pueden ser los embeddings estáticos o los dinámicos del modelo
- Aplica un algoritmo de clusterización a las palabras y plotearlas en 2D
  - Aplica algun color para los diferentes clusters
- Agrega al plot los embeddings de las etiquetas POS
  - Utiliza un marcador que las distinga claramente de las palabras
- Realiza una conclusión sobre los resultados observados
"""

np.random.seed(82)
# Muestreamos las 100 palabras
sample_words = np.random.choice(corpus_words_rnn, size=100)
embeddings_sample = {word: rnn_model.embedding(torch.LongTensor([word2idx.get(word, 1)]).to(device)).detach().cpu().numpy()[0] for word in sample_words}
X = np.array(list(embeddings_sample.values()))
idx2sample = {idx: word for idx, word in enumerate(list(embeddings_sample.keys()))}
pos_sample = {word: np.argmax(rnn_model(torch.LongTensor([word2idx.get(word, 1)]).to(device)).detach().cpu().numpy()[0]) for word in embeddings_sample.keys()}
pos_sample = {word: idx2pos[pos] for word, pos in pos_sample.items()}
len(embeddings_sample)

from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage
from scipy.cluster.hierarchy import dendrogram

# Calcular la distancia coseno (1 - similitud coseno)
dist_cos = pdist(X, metric='cosine')
# linkage espera una forma de distancia y no una matriz completa
Z = linkage(dist_cos, method='complete')

plt.figure(figsize=(10, 5))
dendrogram(Z)
plt.title('Dendrograma con distancia coseno')
plt.xlabel('Índices de las muestras')
plt.ylabel('Distancia (1 - similitud coseno)')
plt.show()

agg = AgglomerativeClustering(n_clusters=3, metric='cosine', linkage='complete')
agg_labels = agg.fit_predict(X)

scaler = StandardScaler()
reduced_embeddings = scaler.fit_transform(X)

reducer = PCA(n_components=2)
reduced_embeddings = reducer.fit_transform(reduced_embeddings)

plt.figure(figsize=(10, 10))
plt.scatter(reduced_embeddings[:, 0], reduced_embeddings[:, 1], c=agg_labels, cmap='tab10_r')
for i, word in enumerate(list(embeddings_sample.values())):
  pos_tag = pos_sample[idx2sample[i]]
  plt.annotate(pos_tag, (reduced_embeddings[i, 0], reduced_embeddings[i, 1]))
plt.show()

"""Podemos observar que la muestra que tomamos no está balanceada y hay una presencia dominante de palabras de tipo `NOUN` Y `PRONOUN` (`SUSTANTIVO` Y `PRONOMBRE`), mientras que otras categorías están pobremente representadas como `ADJETIVO`, `VERBO` y `CONJUNCION`; por esta misma razón, a la hora de aplicar un algoritmo de clustering a los embeddings dinámicos resultantes del entrenamiento de la red es difícil encontrar separaciones claras entre grupos que se esperan contegan miembros de la misma categoría gramatical.

Sin embago sí podemos observar cómo en el grupo azul marino, se concentra la mayor cantidad de verbos, mientras que en eel grupo morado se agrupan los verbos restantes pero también algún adverbio y una preposición

### Extra: 0.5pt

- Implementa una red *Long short-term memory units (LSTM)* para la tarea de etiquetado POS
- Reporta el accuracy y comparalo con los resultados de la RNN simple
- Realiza un comentario sobre como impacta la arquitectura LSTM sobre el resultado obtenido
"""

import torch.nn as nn

class LstmModel(nn.Module):
    def __init__(self,
                 embedding_table,
                 hidden_size,
                 num_classes: int,
                 freeze_embeddings: bool = False,
                 num_layers: int = 1,
                 bidirectional: bool = False):
        super().__init__()
        embedding_dim = embedding_table.size(dim=-1)
        self.embedding = nn.Embedding.from_pretrained(
            embedding_table,
            freeze=freeze_embeddings,
            padding_idx=0
        )
        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            bidirectional=bidirectional,
            batch_first=True
        )
        if bidirectional:
            self.linear = nn.Linear(hidden_size * 2, num_classes)
        else:
            self.linear = nn.Linear(hidden_size, num_classes)

    def forward(self, sentence):
        embeds = self.embedding(sentence)           # (batch, seq_len, embed_dim)
        lstm_out, _ = self.lstm(embeds)             # lstm_out: (batch, seq_len, hidden)
        logits = self.linear(lstm_out)              # (batch, seq_len, num_classes)
        return logits

lstm_model = LstmModel(
    embedding_table,
    hidden_size=100,
    num_classes=len(pos2idx) + 1,
    freeze_embeddings=False,
    num_layers=2,
    bidirectional=True
).to(device)

loss_fn = nn.CrossEntropyLoss(ignore_index=0)
optimizer = torch.optim.Adam(lstm_model.parameters(), lr=0.005)

lstm_history = {"accuracy": [], "loss": [], "val_loss": [], "val_accuracy": []}
for epoch in trange(EPOCHS):
    train_loss, train_acc, t_words = 0, 0, 0
    lstm_model.train()
    for X_batch, y_batch in tqdm(train_dataloader_rnn):
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        y_batch_pred = lstm_model(X_batch)
        loss = loss_fn(
            y_batch_pred.reshape(-1, y_batch_pred.size(dim=-1)),
            y_batch.reshape(-1)
            )
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        with torch.no_grad():
            n_words = torch.sum(y_batch > 0).item()
            t_words += n_words
            train_loss += n_words * loss.item()
            train_acc += torch.mul(
                torch.argmax(y_batch_pred, dim=-1) == y_batch,
                y_batch > 0).sum().item()

    lstm_model.eval()
    with torch.no_grad():
        lstm_history["accuracy"].append(train_acc / t_words)
        lstm_history["loss"].append(train_loss / t_words)
        val_loss, val_acc = evaluate_rnn(lstm_model, loss_fn, val_dataloader_rnn)
        lstm_history["val_loss"].append(val_loss)
        lstm_history["val_accuracy"].append(val_acc)
    torch.save(lstm_model.state_dict(), f"{MODELS_PATH}/pos_tagger_lstm_{device}_{epoch}.pth")
torch.save(lstm_history, f"{MODELS_PATH}/pos_tagger_lstm.history")

plot_history(lstm_history)

_, accuracy_lstm = evaluate_rnn(lstm_model, loss_fn, test_dataloader_rnn)
rprint(f"Accuracy (LSTM): {accuracy_lstm * 100:.2f}%")
rprint(f"Δ accuracy (from baseline): {(accuracy_lstm - baseline_accuracy) * 100:.2f}%")
rprint(f"Δ accuracy (from logistic): {(accuracy_lstm - logistic_accuracy) * 100:.2f}% ({logistic_accuracy * 100:.2f}%)")
rprint(f"Δ accuracy (from ff): {(accuracy_lstm - accuracy_ff) * 100:.2f}% ({accuracy_ff * 100:.2f}%)")
rprint(f"Δ accuracy (from embeddings): {(accuracy_lstm - accuracy_emb) * 100:.2f}% ({accuracy_emb * 100:.2f}%)")
rprint(f"Δ accuracy (from rnn): {(accuracy_lstm - accuracy_rnn) * 100:.2f}% ({accuracy_rnn * 100:.2f}%)")

"""Podemos ver que el cambio de la arquitectura de la red recurrente de una RNN convenional a una LSTM sí mejora el desempeño del modelo pero en una proporción relativamente pequeña (0.27%) en comparación al salto que hubo entre las feedfowrd y las RNN (1.51%).

### Referencias

- [Speech and Language Processing 3rd ed. draft (Jurafsky, 2025)](https://web.stanford.edu/~jurafsky/slp3/)
  - [Capítulo 8: RNNs y LSTMs](https://web.stanford.edu/~jurafsky/slp3/8.pdf)
- NLP for you course (Voita, 2023)
  - [Capítulo 3: Language Modeling](https://lena-voita.github.io/nlp_course/language_modeling.html)
- [Python for Natural Language Processing, 3rd edition (Nugues, 2024)](https://link.springer.com/book/10.1007/978-3-031-57549-5)
  - Capítulos 12 (Words, POS and Morphology) y 14 (POS and Sequence annotation)
"""