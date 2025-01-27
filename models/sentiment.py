#!/bin/python

def read_files(tarfname, vectorizer = 'BOW'):
    """Read the training and development data from the sentiment tar file.
    The returned object contains various fields that store sentiment data, such as:

    train_data,dev_data: array of documents (array of words)
    train_fnames,dev_fnames: list of filenames of the doccuments (same length as data)
    train_labels,dev_labels: the true string label for each document (same length as data)

    The data is also preprocessed for use with scikit-learn, as:

    count_vec: CountVectorizer used to process the data (for reapplication on new data)
    trainX,devX: array of vectors representing Bags of Words, i.e. documents processed through the vectorizer
    le: LabelEncoder, i.e. a mapper from string labels to ints (stored for reapplication)
    target_labels: List of labels (same order as used in le)
    trainy,devy: array of int labels, one for each document
    """
    import tarfile
    tar = tarfile.open(tarfname, "r:gz")
    trainname = "train.tsv"
    devname = "dev.tsv"
    for member in tar.getmembers():
        if 'train.tsv' in member.name:
            trainname = member.name
        elif 'dev.tsv' in member.name:
            devname = member.name


    class Data: pass
    sentiment = Data()
    print("-- train data")
    sentiment.train_data, sentiment.train_labels = read_tsv(tar,trainname)
    print(len(sentiment.train_data))

    print("-- dev data")
    sentiment.dev_data, sentiment.dev_labels = read_tsv(tar, devname)
    print(len(sentiment.dev_data))
    print("-- transforming data and labels")
    if vectorizer is 'BOW':
        print('Bag of words')
        from sklearn.feature_extraction.text import CountVectorizer
        sentiment.count_vect = CountVectorizer(ngram_range = (1, 3), min_df = 1, max_df = 1.0, stop_words = frozenset(['the', 'a', 'an', 'i', 'he', 'she', 'they', 'to', 'of', 'it', 'from']))
        sentiment.trainX = sentiment.count_vect.fit_transform(sentiment.train_data)
        sentiment.devX = sentiment.count_vect.transform(sentiment.dev_data)
    elif vectorizer is 'tfidf':
        print('TfidfVectorizer:')
        from sklearn.feature_extraction.text import TfidfVectorizer
        sentiment.count_vect = TfidfVectorizer(max_features = 200000, min_df = 1, max_df = 1.0, tokenizer = LemmaTokenizer(), sublinear_tf = False, ngram_range = (1, 3), stop_words = frozenset(['the', 'a', 'an', 'i', 'he', 'she', 'they', 'to', 'of', 'it', 'from']))
        sentiment.trainX = sentiment.count_vect.fit_transform(sentiment.train_data)
        sentiment.devX = sentiment.count_vect.transform(sentiment.dev_data)
        print('yeet2')
    from sklearn import preprocessing
    sentiment.le = preprocessing.LabelEncoder()
    sentiment.le.fit(sentiment.train_labels)
    sentiment.target_labels = sentiment.le.classes_
    sentiment.trainy = sentiment.le.transform(sentiment.train_labels)
    sentiment.devy = sentiment.le.transform(sentiment.dev_labels)
    tar.close()
    return sentiment

import nltk
#nltk.download('wordnet')
from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer
class LemmaTokenizer(object):
    def __init__(self):
        self.wnl = WordNetLemmatizer()
    def __call__(self, articles):
        return [self.wnl.lemmatize(t) for t in word_tokenize(articles)]

def read_unlabeled(tarfname, sentiment):
    """Reads the unlabeled data.

    The returned object contains three fields that represent the unlabeled data.

    data: documents, represented as sequence of words
    fnames: list of filenames, one for each document
    X: bag of word vector for each document, using the sentiment.vectorizer
    """
    import tarfile
    tar = tarfile.open(tarfname, "r:gz")
    class Data: pass
    unlabeled = Data()
    unlabeled.data = []

    unlabeledname = "unlabeled.tsv"
    for member in tar.getmembers():
        if 'unlabeled.tsv' in member.name:
            unlabeledname = member.name

    print(unlabeledname)
    tf = tar.extractfile(unlabeledname)
    for line in tf:
        line = line.decode("utf-8")
        text = line.strip()
        unlabeled.data.append(text)


    unlabeled.X = sentiment.count_vect.transform(unlabeled.data)
    print(unlabeled.X.shape)
    tar.close()
    return unlabeled

def read_tsv(tar, fname):
    member = tar.getmember(fname)
    print(member.name)
    tf = tar.extractfile(member)
    data = []
    labels = []
    for line in tf:
        line = line.decode("utf-8")
        (label,text) = line.strip().split("\t")
        labels.append(label)
        data.append(text)
    return data, labels

def write_pred_kaggle_file(unlabeled, cls, outfname, sentiment):
    """Writes the predictions in Kaggle format.

    Given the unlabeled object, classifier, outputfilename, and the sentiment object,
    this function write sthe predictions of the classifier on the unlabeled data and
    writes it to the outputfilename. The sentiment object is required to ensure
    consistent label names.
    """
    yp = cls.predict(unlabeled.X)
    labels = sentiment.le.inverse_transform(yp)
    f = open(outfname, 'w')
    f.write("ID,LABEL\n")
    for i in range(len(unlabeled.data)):
        f.write(str(i+1))
        f.write(",")
        f.write(labels[i])
        f.write("\n")
    f.close()


def write_gold_kaggle_file(tsvfile, outfname):
    """Writes the output Kaggle file of the truth.

    You will not be able to run this code, since the tsvfile is not
    accessible to you (it is the test labels).
    """
    f = open(outfname, 'w')
    f.write("ID,LABEL\n")
    i = 0
    with open(tsvfile, 'r') as tf:
        for line in tf:
            (label,review) = line.strip().split("\t")
            i += 1
            f.write(str(i))
            f.write(",")
            f.write(label)
            f.write("\n")
    f.close()

def write_basic_kaggle_file(tsvfile, outfname):
    """Writes the output Kaggle file of the naive baseline.

    This baseline predicts POSITIVE for all the instances.
    """
    f = open(outfname, 'w')
    f.write("ID,LABEL\n")
    i = 0
    with open(tsvfile, 'r') as tf:
        for line in tf:
            (label,review) = line.strip().split("\t")
            i += 1
            f.write(str(i))
            f.write(",")
            f.write("POSITIVE")
            f.write("\n")
    f.close()

if __name__ == "__main__":
    print("Reading data")
    tarfname = "data/sentiment.tar.gz"
    sentiment = read_files(tarfname, vectorizer = 'tfidf')
    print("\nTraining classifier")
    import classify
    import numpy as np
    cval = 8
    cls = classify.train_classifier(sentiment.trainX, sentiment.trainy, cval, 'l2','lbfgs')
    print('training input shape: ' + str(sentiment.trainX.shape))
    print("\nEvaluating")
    train_acc = classify.evaluate(sentiment.trainX, sentiment.trainy, cls, name = 'training data')
    dev_acc = classify.evaluate(sentiment.devX, sentiment.devy, cls, name = 'validation data')
    print('Train accuracy: ' + str(train_acc))
    print('Dev accuracy: ' + str(dev_acc))
            # unlabeled = read_unlabeled(tarfname, sentiment)
            # perc = 10
            # ind_perc = int(10*unlabeled.X.shape[0]/100)
            # unlab_traindata_10 = unlabeled.data[:ind_perc]
            # unlabeled_totrain = sentiment.count_vect.transform(unlab_traindata_10)
            # yp_10perc = cls.predict(unlabeled_totrain)
            # sentiment.trainy_10perc = np.concatenate((sentiment.trainy, yp_10perc))
            # sentiment.traindata_10 = sentiment.train_data + unlab_traindata_10
            # sentiment.trainX_10 = sentiment.count_vect.fit_transform(sentiment.traindata_10)
            # sentiment.devX_10 = sentiment.count_vect.transform(sentiment.dev_data)
            # cval2 = 200
            # cls_2 = classify.train_classifier(sentiment.trainX_10, sentiment.trainy_10perc, cval2, 'l2','lbfgs')
            # train_acc1 = classify.evaluate(sentiment.trainX_10, sentiment.trainy_10perc, cls_2, name = 'training data')
            # dev_acc1 = classify.evaluate(sentiment.devX_10, sentiment.devy, cls_2, name = 'validation data')
            # print('Train accuracy: ' + str(train_acc1))
            # print('Dev accuracy: ' + str(dev_acc1))
    ##print("\nReading unlabeled data")
    ##print("Writing predictions to a file")
    ##unlabeled = read_unlabeled(tarfname, sentiment)
    ##write_pred_kaggle_file(unlabeled, cls_2, "data/sentiment-pred15.csv", sentiment)
#write_basic_kaggle_file("data/sentiment-unlabeled.tsv", "data/sentiment-basic.csv")

    # You can't run this since you do not have the true labels
    # print "Writing gold file"
    # write_gold_kaggle_file("data/sentiment-unlabeled.tsv", "data/sentiment-gold.csv")
