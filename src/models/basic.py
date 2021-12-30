from tensorflow import keras

from models.dense import build_dense_network, build_dense_classifier


class BasicRS(keras.Model):
    def __init__(
        self,
        dense_units=(512, 256, 128),
        clf_units=(64, 64),
        activation='relu'
    ):
        super().__init__()
        self.concat = keras.layers.Concatenate()
        self.unet = build_dense_network(dense_units, activation=activation)
        self.inet = build_dense_network(dense_units, activation=activation)
        self.clf = build_dense_classifier(clf_units, n_classes=1, activation=activation)

    def call(self, inputs):
        u, i = inputs
        u = self.unet(u)
        i = self.inet(i)
        x = self.concat([u, i])
        return self.clf(x)
