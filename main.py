import numpy as np # linear algebra
import pandas as pd
import os

import random

#deep learning imports
import tensorflow as tf
import keras
from tensorflow.keras.layers import Conv2D, MaxPool2D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.optimizers import Adam
from tensorflow.keras import regularizers
from tensorflow.keras.losses import categorical_crossentropy
from tensorflow.keras import backend as K
from keras.utils.vis_utils import plot_model

#data visualization and plotting imports
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.utils.multiclass import unique_labels
import cv2
import matplotlib.pyplot as plt
import seaborn as sn
import time

#word library import
# from nltk.corpus import words


os.environ['KMP_DUPLICATE_LIB_OK']='True'

#setting up global variables
DATADIR = "./dataset/asl_alphabet_train/asl_alphabet_train" #training data directory
CATEGORIES = ['A', 'B' , 'C' , 'D' , 'del', 'E' , 'F' , 'G' , 'H', 'I', 'J', 'K', 'L' ,'M' , 'N', 'nothing', 'O', 'P' , 'Q' , 'R' , 'S' , 'space' , 'T' ,'U' , 'V', 'W', 'X' , 'Y' , 'Z']
test_dir = "./dataset/asl_alphabet_test/asl_alphabet_test"
# own_dir = "./input/ishaan/ishaan_pics/ishaan_pics"


def create_training_data(modeltype):
    '''This function is run for each model in order to get the training data from the filepath
    and convert it into array format'''
    training_data = []
    if(modeltype == 'cnn'):
        for category in CATEGORIES:
            path = os.path.join(DATADIR, category) #path to alphabets
            class_num = CATEGORIES.index(category)
            for img in os.listdir(path):
                try:
                    img_array = cv2.imread(os.path.join(path,img), cv2.IMREAD_COLOR)
                    new_array = cv2.resize(img_array, (64, 64))
                    final_img = cv2.cvtColor(new_array, cv2.COLOR_BGR2RGB)
                    training_data.append([final_img, class_num])
                except Exception as e:
                    pass
    else:
         for category in CATEGORIES:
            path = os.path.join(DATADIR, category) #path to alphabets
            class_num = CATEGORIES.index(category)
            for img in os.listdir(path):
                try:
                    img_array = cv2.imread(os.path.join(path,img), cv2.IMREAD_GRAYSCALE)
                    new_array = cv2.resize(img_array, (64, 64))
                    # new_array = preprocess_image(new_array)
                    training_data.append([new_array, class_num])
                except Exception as e:
                    pass
    return training_data

def preprocess_image(image):
    '''Sobel filter on the images'''
    sobelimage = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=5)
    return sobelimage

def make_data(modeltype, training_data):
    '''This formats the training data into the proper format and passes it through an generator
    so that it can be augmented(shifted left/right, rotated, etc) and fed into the model '''
    X = []
    y = []
    for features, label in training_data:
        X.append(features)
        y.append(label)
    if (modeltype == "cnn"):
        X = np.array(X).reshape(-1, 64, 64, 3)
        X = X.astype('float32') / 255.0  # to normalize data
        y = keras.utils.to_categorical(y)  # one-hot encoding
        y = np.array(y)
        datagen = ImageDataGenerator(
            validation_split=0.1,
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            horizontal_flip=True)
        train_data = datagen.flow(X, y, batch_size=64, shuffle=True, subset='training')
        val_data = datagen.flow(X, y, batch_size=64, shuffle=True, subset='validation')
        return (train_data, val_data, X, y)
    else:
        X = np.array(X).flatten().reshape(-1, 4096)
        X = X.astype('float32') / 255.0
        y = keras.utils.to_categorical(y)
        y = np.array(y)
        return (X, y)


def build_model(modeltype):
    model = Sequential()

    if (modeltype == "cnn"):
        model.add(Conv2D(64, kernel_size=4, strides=1, activation='relu', input_shape=(64, 64, 3)))
        model.add(Conv2D(64, kernel_size=4, strides=2, activation='relu'))
        model.add(Dropout(0.5))

        model.add(Conv2D(128, kernel_size=4, strides=1, activation='relu'))
        model.add(Conv2D(128, kernel_size=4, strides=2, activation='relu'))
        model.add(Dropout(0.5))

        model.add(Conv2D(256, kernel_size=4, strides=1, activation='relu'))
        model.add(Conv2D(256, kernel_size=4, strides=2, activation='relu'))

        model.add(BatchNormalization())

        model.add(Flatten())
        model.add(Dropout(0.5))
        model.add(Dense(512, activation='relu', kernel_regularizer=regularizers.l2(0.001)))
        model.add(Dense(29, activation='softmax'))

    else:
        model.add(Dense(4096, activation='relu'))
        model.add(Dense(4096, activation='relu'))
        model.add(Dense(2000, activation='relu'))
        model.add(Dense(29, activation='softmax'))
    model.compile(optimizer=Adam(lr=0.0005), loss='categorical_crossentropy',
                  metrics=["accuracy"])  # learning rate reduced to help problems with overfitting
    return model


def fit_fully_connected_model(X, y, model):

    filepath = "weights2.best.h5"

    # saving model weights with lowest validation loss to reduce overfitting
    checkpoint = keras.callbacks.ModelCheckpoint(filepath, monitor='val_loss', verbose=1, save_best_only=True,
                                                 save_weights_only=False, mode='auto', period=1)
    # tensorboard
    tensorboard_callback = keras.callbacks.TensorBoard("logs")
    history = model.fit(X, y, epochs=10, validation_split=0.1, callbacks=[checkpoint, tensorboard_callback])

    # Plot training & validation accuracy values
    plt.plot(history.history['acc'])
    plt.plot(history.history['val_acc'])
    plt.title('Model accuracy')
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper left')
    plt.show()
    plt.savefig('TRAINING-VAL_ACCURACY_FNN.png')

    plt.clf()
    # Plot training & validation loss values
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('Model loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper left')
    plt.show()
    plt.savefig('TRAINING-VAL_LOSS_FNN.png')

def show_classification_report(X, y, input_shape, model):
    '''This function prints a classification report for the validation data'''
    start_time = time.time()
    validation = [X[i] for i in range(int(0.1 * len(X)))]
    validation_labels = [np.argmax(y[i]) for i in range(int(0.1 * len(y)))]
    validation_preds = []
    labels = [i for i in range(29)]
    for img in validation:
        img = img.reshape((1,4096))
        pred = model.predict_classes(img)
        validation_preds.append(pred[0])
    print(classification_report(validation_labels, validation_preds,labels, target_names=CATEGORIES))
    print("\n Evaluating the model took {:.0f} seconds".format(time.time()-start_time))
    return (validation_labels, validation_preds)


def plot_confusion_matrix(y_true, y_pred, classes,
                          normalize=False,
                          title=None,
                          cmap=plt.cm.Blues):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if not title:
        if normalize:
            title = 'Normalized confusion matrix'
        else:
            title = 'Confusion matrix, without normalization'

    # Compute confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    # Only use the labels that appear in the data
    #classes = classes[unique_labels(y_true, y_pred)]
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')

    # print(cm)

    fig, ax = plt.subplots(figsize=(20, 10))
    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
    ax.figure.colorbar(im, ax=ax)
    # We want to show all ticks...
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           # ... and label them with the respective list entries
           xticklabels=classes, yticklabels=classes,
           title=title,
           ylabel='True label',
           xlabel='Predicted label')

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], fmt),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    fig.savefig("CMatrix_FNN.png")
    return ax
np.set_printoptions(precision=2)


def create_testing_data(path, input_shape, modeltype):
    '''This function will get and format both the testing data from the dataset and my own pictures.
    It works in almost the exact same way as training_data except it returns image names to evaluate predictions'''
    testing_data = []
    names = []
    for img in os.listdir(path):
        if(modeltype == 'cnn'):
            img_array = cv2.imread(os.path.join(path,img), cv2.IMREAD_COLOR)
            # rotated_90, rotated_180, rotated_270 = rotate_image(img_array) #in order to test predictions for rotated data
            # rotated_90, rotated_180, rotated_270 = rotate_image(img_array) #in order to test predictions for rotated data
            imgs = [img_array, rotated_90, rotated_180, rotated_270]
            final_imgs = []
            for image in imgs:
                new_array = cv2.resize(image, (64, 64))
                final_img = cv2.cvtColor(new_array, cv2.COLOR_BGR2RGB)
                final_imgs.append(final_img)
        else:
            img_array = cv2.imread(os.path.join(path,img), cv2.IMREAD_GRAYSCALE)
            imgs = [img_array]
            final_imgs = []
            for image in imgs:
                final_img = cv2.resize(image, (64, 64))
                final_imgs.append(final_img)
        # print(len(final_imgs))
        for final_img in final_imgs:
            testing_data.append(final_img)
            names.append(img)
    if modeltype == 'cnn':
        new_testing_data = np.array(testing_data).reshape((-1,) + input_shape)
    else:
        new_testing_data = np.array(testing_data).flatten().reshape(-1, input_shape)
    new_testing_data = new_testing_data.astype('float32')/255.0
    return (testing_data, new_testing_data, names)

def prediction_generator(testing_data, input_shape, model):
    '''This function generates predictions for both sets of testing data'''
    predictions=[]
    for img in testing_data:
        img = img.reshape((1, input_shape))
        pred = model.predict_classes(img)
        predictions.append(pred[0])
    predictions = np.array(predictions)
    return predictions


def plot_predictions(testing_data, predictions, names):
    fig = plt.figure(figsize=(200, 200))
    fig.subplots_adjust(hspace=0.9, wspace=0.9)
    index = 0
    for i in range(1, len(testing_data)):
        y = fig.add_subplot(6, np.ceil(len(testing_data) / float(9)), i)

        str_label = CATEGORIES[predictions[index]]
        y.imshow(testing_data[index], cmap='gray')

        if (index % 4 == 0):
            title = "prediction = {}\n {}".format(str_label, names[index]) # no rotation
        else:
            title = "prediction = {}\n {}".format(str_label, names[index])
        y.set_title(title, fontsize=90)
        y.axes.get_xaxis().set_visible(False)
        y.axes.get_yaxis().set_visible(False)
        index += 1
    fig.savefig("Predictions_FNN.png")

def calculate_loss(names, predictions):
    y_true = K.variable(np.array([CATEGORIES.index(name[0].upper()) for name in names]))
    y_pred = K.variable(np.array(predictions))
    print("Calculating loss...")
    # print(tf.Print(y_true))
    # print(tf.Print(y_pred))
    error = K.eval(categorical_crossentropy(y_true, y_pred))
    print("Error: ", error)

if __name__ == "__main__":

    # FULLY CONNECTED
    modeltype = "fully_connected"
    input_shape = 4096  # 64 x 64
    #input_shape = 1024  # 32 x 32

    #getting training data
    training_data = create_training_data(modeltype)
    random.shuffle(training_data)

    #building the model
    model = build_model(modeltype)

    #formatting data
    X, y = make_data(modeltype, training_data)

    #fitting model
    fit_fully_connected_model(X, y, model)
    model.load_weights("weights2.best.h5")
    graph = plot_model(model, to_file="FNN_model.png", show_shapes=True)

    # evaluating validation data
    validation_labels, validation_preds = show_classification_report(X, y, input_shape, model)

    # confusion matrix for validation data
    plot_confusion_matrix(validation_labels, validation_preds, classes=CATEGORIES,
                          title='Confusion matrix, without normalization')
    plt.show()
    plt.savefig('Cmatrix_validation_FNN.png')
    # database testing data and predictions
    testing_data, new_testing_data, names = create_testing_data(test_dir, input_shape, modeltype)
    predictions = prediction_generator(new_testing_data, input_shape, model)
    plot_predictions(testing_data, predictions, names)
    calculate_loss(names, predictions)

