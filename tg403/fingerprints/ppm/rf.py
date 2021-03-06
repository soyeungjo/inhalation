import sys
sys.path.append('../../../')

from utils import (
    ppm_fing_load,
    data_split,
    ParameterGrid,
    MultiCV
)

import warnings

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier

import scipy.stats as stats
from sklearn.metrics import (
    precision_score, 
    recall_score, 
    f1_score, 
    accuracy_score
    )

try:
      import wandb
except: 
      import sys
      import subprocess
      subprocess.check_call([sys.executable, "-m", "pip", "install", "wandb"])
      import wandb

warnings.filterwarnings("ignore")


wandb.login(key="1c2f31977d15e796871c32701e62c5ec1167070e")
wandb.init(project="tg403-time-ppm", entity="soyoung")
wandb.run.name = 'rf'
wandb.run.save()


def ppm_rf_main(seed_):
    
    path = '../../data/'

    ppm, ppm_fingerprints, ppm_y = ppm_fing_load(path)
    train_ppm_fingerprints, train_ppm_y, test_ppm_fingerprints, test_ppm_y = data_split(
        ppm_fingerprints, 
        ppm_y.category,
        seed = seed_
    )


    # print('ppm', 
    #     '\n기초통계량:\n', ppm.value.describe(),
    #     '\n분위수: ', np.quantile(ppm.value, [0.2, 0.4, 0.6, 0.8, 1]))

    # print('범주에 포함된 데이터의 수\n', ppm_y.category.value_counts().sort_index(),
    #     '\n비율\n', ppm_y.category.value_counts(normalize = True).sort_index())

    # print('train 범주에 포함된 데이터의 수\n', train_ppm_y.value_counts().sort_index(),
    #     '\n비율\n', train_ppm_y.value_counts(normalize = True).sort_index())

    # print('test 범주에 포함된 데이터의 수\n', test_ppm_y.value_counts().sort_index(),
    #     '\n비율\n', test_ppm_y.value_counts(normalize = True).sort_index())


    '''
        Random Forest with ppm data
    '''

    params_dict = {
        'random_state': [seed_], 
        'n_estimators': np.arange(30, 155, 10),
        'min_samples_split': list(range(2, 9)),
        'max_features': ['auto', 'sqrt', 'log2'],
        'class_weight': [None, {1:1.6, 2:1.2, 3:2.6, 4:3.2, 5:1.4}]
    }

    params = ParameterGrid(params_dict)

    ppm_rf_result = MultiCV(
        train_ppm_fingerprints, 
        train_ppm_y, 
        RandomForestClassifier,
        params
    )

    max_tau_idx = ppm_rf_result.val_tau.argmax(axis = 0)
    best_params = ppm_rf_result.iloc[max_tau_idx][:5].to_dict()

    rf = RandomForestClassifier(**best_params)
    rf.fit(train_ppm_fingerprints, train_ppm_y)
    ppm_rf_pred = rf.predict(test_ppm_fingerprints)
      
    result_ = {
        'seed': seed_,
        'parameters': best_params,
        'precision': precision_score(test_ppm_y, ppm_rf_pred, average = 'macro'), 
        'recall': recall_score(test_ppm_y, ppm_rf_pred, average = 'macro'), 
        'f1': f1_score(test_ppm_y, ppm_rf_pred, average = 'macro'), 
        'accuracy': accuracy_score(test_ppm_y, ppm_rf_pred),
        'tau': stats.kendalltau(test_ppm_y, ppm_rf_pred).correlation
    }
            

    wandb.log({
        'seed': seed_,
        'parameters': best_params,
        'precision': precision_score(test_ppm_y, ppm_rf_pred, average = 'macro'), 
        'recall': recall_score(test_ppm_y, ppm_rf_pred, average = 'macro'), 
        'f1': f1_score(test_ppm_y, ppm_rf_pred, average = 'macro'), 
        'accuracy': accuracy_score(test_ppm_y, ppm_rf_pred),
        'tau': stats.kendalltau(test_ppm_y, ppm_rf_pred).correlation
    })
      
      
      
      # run = neptune.init(
      # project="ok69531/LC50-mgl-logistic",
      # api_token="my_api_token",
      # ) 
      
      # run['parameters'] = best_params
      # run['precision'] = precision_score(test_mgl_y, mgl_logit_pred, average = 'macro')
      # run['recall'] = recall_score(test_mgl_y, mgl_logit_pred, average = 'macro')
      # run['f1'] = f1_score(test_mgl_y, mgl_logit_pred, average = 'macro')
      # run['accuracy'] = accuracy_score(test_mgl_y, mgl_logit_pred)
      # run['tau'] = stats.kendalltau(test_mgl_y, mgl_logit_pred).correlation
      
      # run.stop()
      
    return result_


result = []
for seed_ in range(50):
    result.append(ppm_rf_main(seed_))
      
pd.DataFrame(result).to_csv('../../test_results/time/ppm_rf.csv', header = True, index = False)
wandb.finish()