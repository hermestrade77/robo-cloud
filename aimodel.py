import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from ai.data import obter_dados
from ai.features import criar_features

def treinar_modelo():

    data = obter_dados()

    X, y = criar_features(data)

    model = GradientBoostingClassifier()
    model.fit(X, y)

    return model, X[-1]