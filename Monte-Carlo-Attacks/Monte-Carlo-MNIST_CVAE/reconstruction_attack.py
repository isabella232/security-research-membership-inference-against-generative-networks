import tensorflow as tf
import numpy as np
import mnist_data
import os
import vae
import glob
import sys
import time
import scipy

from calc_rec_error import *

""" parameters """

# source activate tensorflow_p36 && pip install pillow && pip install scikit-image && pip install scikit-learn
# source activate tensorflow_p36 && python run_main.py --dim_z 10 --num_epochs 300
# source activate tensorflow_p36 && python mc_attack_cvae.py 299 5 && python mc_attack_cvae.py 299 5 && sudo shutdown -P now

# combined:
# source activate tensorflow_p36 && pip install pillow && pip install scikit-image && pip install scikit-learn && python run_main.py --dim_z 10 --num_epochs 300 && python mc_attack_cvae.py 299 5 && python mc_attack_cvae.py 299 5 && sudo shutdown -P now
# source activate tensorflow_p36 && python mc_attack_cvae.py 299 5 && python mc_attack_cvae.py 299 5 && sudo shutdown -P now
# source activate tensorflow_p36 && python mc_attack_cvae.py 299 5 && python mc_attack_cvae.py 299 5 && python mc_attack_cvae.py 299 5 && sudo shutdown -P now
model_no = sys.argv[1] # which model to attack
exp_nos = int(sys.argv[2]) # how many different experiments ofr specific indexes

instance_no = np.random.randint(10000)
experiment = 'MC_ATTACK_CVAE' + str(instance_no)
percentage = np.loadtxt('percentage.csv')

dt = np.dtype([('instance_no', int),
               ('exp_no', int),
               ('method', int), # 1 = white box, 2 = euclidean_PCA, 3 = hog, 4 = euclidean_PCA category, 5 = hog category, 6 = ais
               ('pca_n', int),
               ('percentage_of_data', float),
               ('percentile', float),
               ('mc_euclidean_no_batches', int), # stuff
               ('mc_hog_no_batches', int), # stuff
               ('sigma_ais', float),
               ('11_perc_mc_attack_log', float),
               ('11_perc_mc_attack_eps', float),
               ('11_perc_mc_attack_frac', float), 
               ('50_perc_mc_attack_log', float), 
               ('50_perc_mc_attack_eps', float),
               ('50_perc_mc_attack_frac', float),
               ('50_perc_white_box', float),
               ('11_perc_white_box', float),
               ('50_perc_ais', float),
               ('50_perc_ais_acc_rate', float),
              ])

experiment_results = []

IMAGE_SIZE_MNIST = 28
n_hidden = 500
dim_img = IMAGE_SIZE_MNIST**2  # number of pixels for a MNIST image
dim_z = 10

""" prepare MNIST data """

train_total_data, train_size, valid_total_data, validation_size, test_total_data, test_size, _, _ = mnist_data.prepare_MNIST_data(reuse=True)
# compatibility with old attack
vaY = np.where(valid_total_data[:,784:795] == 1)[1]
trY = np.where(train_total_data[:,784:795] == 1)[1]
teY = np.where(test_total_data[:,784:795] == 1)[1]
vaX = valid_total_data[:,0:784]
trX = train_total_data[:,0:784]
teX = test_total_data[:,0:784]
n_samples = train_size

# bug https://github.com/Microsoft/vscode/issues/39149#issuecomment-347260954
# for now ignore!
# comment print in windows
def save_print(my_str):
    # my_str = my_str.encode("utf-8").decode("ascii")
    print(my_str)

def print_elapsed_time():
    end_time = int(time.time())
    d = divmod(end_time-start_time,86400)  # days
    h = divmod(d[1],3600)  # hours
    m = divmod(h[1],60)  # minutes
    s = m[1]  # seconds

    save_print('Elapsed Time: %d days, %d hours, %d minutes, %d seconds' % (d[0],h[0],m[0],s))


def reconstruction_attack(trX_inds, vaX_inds, repeats):
    results_sample = np.zeros((len(vaX_inds),2))
    for i in range(len(vaX_inds)):
        # indicate that dataset is a sample
        results_sample[i][0] = 0

        save_print('Working on test reconstruction error %d/%d'%(i, len(vaX_inds)))
        print_elapsed_time()
        results_sample[i][1] = compute_avg_rec_error(vaX[vaX_inds][i], vaY[vaX_inds][i], repeats)

    results_train = np.zeros((len(trX_inds),2))
    for i in range(len(trX_inds)):
        # indicate that dataset is a training data set
        results_train[i][0] = 1
        save_print('Working on training reconstruction error %d/%d'%(i, len(trX_inds)))
        print_elapsed_time()
        results_train[i][1] = compute_avg_rec_error(trX[trX_inds][i], trY[trX_inds][i], repeats)

    results = np.concatenate((results_sample, results_train))
    np.random.shuffle(results)

    # save data
    new_row = np.zeros(1, dtype = dt)[0]
    new_row['instance_no'] = instance_no
    new_row['exp_no'] = exp_no
    new_row['method'] = 42 # reconstruction attack
    new_row['percentage_of_data'] = 0.1

    # compute 1- ... because we would have to sort the other way around
    # smaller reconstruction error => more likely training data
    accuracy = 1 - results[results[:,1].argsort()][:,0][-len(results_train):].mean()
    new_row['50_perc_mc_attack_eps'] = accuracy
    save_print('50_perc_mc_attack_eps: %.3f'%(accuracy))
    
    experiment_results.append(new_row)
    np.savetxt(experiment+'.csv', np.array(experiment_results, dtype = dt))

start_time = int(time.time())

for exp_no in range(exp_nos):

    trX_inds = np.arange(len(trX))
    np.random.shuffle(trX_inds)
    trX_inds = trX_inds[0:100]

    vaX_inds = np.arange(len(trX))
    np.random.shuffle(vaX_inds)
    vaX_inds = vaX_inds[0:100]

    # reconstruction attack
    # reconstruction_attack(trX_inds, vaX_inds, 100) # local
    reconstruction_attack(trX_inds, vaX_inds, 300000) # production ready
    
    print_elapsed_time()