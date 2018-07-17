import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler


train = pd.read_csv('Data/train.csv')
test = pd.read_csv('Data/test.csv')

train.describe()
train.head()


tf.set_random_seed(1)
np.random.seed(1)

spacegroups = train.spacegroup.unique()
spacegroups.sort()
n_spacegroups = len(spacegroups)

t1 = 'formation_energy_ev_natom'
t2 = 'bandgap_energy_ev'

transform_columns = ['number_of_total_atoms', 'percent_atom_al',
                     'percent_atom_ga', 'percent_atom_in',
                     'lattice_vector_1_ang', 'lattice_vector_2_ang',
                     'lattice_vector_3_ang', 'lattice_angle_alpha_degree',
                     'lattice_angle_beta_degree', 'lattice_angle_gamma_degree']
feature_columns = ['spacegroup'] + transform_columns

all = pd.concat([train[feature_columns], test])


"""
colors = dict(zip(spacegroups, cm.rainbow(np.linspace(0, 1, n_spacegroups))))
plt.figure(figsize=(14, 5))

plt.subplot(1, 2, 1)
plt.title(t1)
for g in spacegroups:
    plt.scatter(
        range(train[train['spacegroup'] == g].shape[0]),
        train.loc[train['spacegroup'] == g, t1], s=9, color=colors[g], label=g)
plt.legend()

plt.subplot(1, 2, 2)
plt.title(t2)
for g in spacegroups:
    plt.scatter(
        range(train[train['spacegroup'] == g].shape[0]),
        train.loc[train['spacegroup'] == g, t2], s=9, color=colors[g], label=g)
plt.legend()

plt.show()
"""

scaler = MinMaxScaler()
# scaler = StandardScaler()
scaler.fit(all[transform_columns])

train[transform_columns] = scaler.transform(train[transform_columns])
test[transform_columns] = scaler.transform(test[transform_columns])

# print(train.head())

random_seed = 314

X_train, X_validation = train_test_split(train, test_size=0.2,
                                         random_state=random_seed)

y_train = np.log1p(X_train[[t1, t2]])
X_train = X_train.drop(['id', t1, t2], axis=1)

y_validation = np.log1p(X_validation[[t1, t2]])
X_validation = X_validation.drop(['id', t1, t2], axis=1)

layers = [16] * 8

# activation = None
# activation = tf.tanh
activation = tf.nn.relu
# activation = tf.nn.sigmoid

# kernel_regularizer_l2 = tf.contrib.layers.l2_regularizer(scale=0.00001)
kernel_regularizer_l2 = None

tf.reset_default_graph()

tf_is_training = tf.placeholder(tf.bool, None)

tf_x = tf.placeholder(tf.float32, (None, X_train.shape[1]), name='tf_x')
tf_y = tf.placeholder(tf.float32, (None, 2), name='tf_y')

l = tf_x
for i, n in enumerate(layers):
    l = tf.layers.dense(l, n, activation=activation,
                        kernel_regularizer=kernel_regularizer_l2,
                        name='layer%s' % (i + 1))

#     if i == 0:
#         l = tf.layers.dropout(l, training=tf_is_training, name='dropout%s' % (i + 1))

output = tf.layers.dense(l, 2, name='output')

# loss
loss_y = tf.sqrt(tf.reduce_mean(tf.squared_difference(tf_y, output), 0),
                 name='tf_y_loss')
loss_total = tf.reduce_mean(loss_y, name='tf_total_loss')

rl = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)
if len(rl) > 0:
    loss_total += tf.add_n(rl)

# optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.05)
# optimizer = tf.train.MomentumOptimizer(learning_rate=0.05, momentum=1.0)
optimizer = tf.train.AdamOptimizer(learning_rate=0.002)
train_op = optimizer.minimize(loss_total)

sess = tf.Session()
sess.run(tf.global_variables_initializer())

loss_data = []

for step in range(10000):
    # training loss
    _, lt, lt_y = sess.run([train_op, loss_total, loss_y],
                           {tf_x: X_train, tf_y: y_train,
                            tf_is_training: True})

    # validation loss
    lv, lv_y = sess.run([loss_total, loss_y],
                        {tf_x: X_validation, tf_y: y_validation,
                         tf_is_training: False})

    loss_data.append([step, lt, lt_y[0], lt_y[1], lv, lv_y[0], lv_y[1]])

loss_data = np.array(loss_data)
print("Final losses")
print(loss_data[-1][1:])
"""
plt.figure(figsize=(15,10))
plt.subplot(2, 1, 1)
plt.title('loss')
plt.plot(loss_data[:, 0], loss_data[:, 1], label='training')
plt.plot(loss_data[:, 0], loss_data[:, 4], label='validation')
plt.legend()

plt.subplot(2, 2, 3)
plt.title(t1)
plt.plot(loss_data[:, 0], loss_data[:, 2], label='training')
plt.plot(loss_data[:, 0], loss_data[:, 5], label='validation')
plt.legend()

plt.subplot(2, 2, 4)
plt.title(t2)
plt.plot(loss_data[:, 0], loss_data[:, 3], label='training')
plt.plot(loss_data[:, 0], loss_data[:, 6], label='validation')
plt.legend()

plt.show()
"""

loss, pred_y = sess.run([loss_total, output],
                        {tf_x: X_validation, tf_y: y_validation,
                         tf_is_training: False})

print('loss:', loss)

"""
n_row = len(y_validation)

plt.figure(figsize=(14, 5))
plt.suptitle('validation')

# Formation energy
plt.subplot(1, 2, 1)
plt.title(t1)
plt.scatter(range(n_row), y_validation[t1], s=12, label='labels')
plt.scatter(range(n_row), pred_y[:, 0], s=12, label='predictions')
plt.legend()

# Bandgap energy
plt.subplot(1, 2, 2)
plt.title(t2)
plt.scatter(range(n_row), y_validation[t2], s=12, label='labels')
plt.scatter(range(n_row), pred_y[:, 1], s=12, label='predictions')
plt.legend()

plt.show()
"""

pd_y_pred = pd.DataFrame()
pd_y_pred[t1] = pred_y[:, 0]
pd_y_pred[t2] = pred_y[:, 1]
pd_y_pred['index'] = y_validation.index
pd_y_pred.set_index('index', inplace=True)

for i, g in enumerate(spacegroups):
    labels = y_validation.loc[
        X_validation[X_validation['spacegroup'] == g].index]
    predictions = pd_y_pred.loc[
        X_validation[X_validation['spacegroup'] == g].index]
    loss = np.sqrt(
        mean_squared_error(labels, predictions, multioutput='raw_values'))
    # print('spacegroup=%d' % g, *loss, np.mean(loss))

"""
plt.figure(figsize=(14, 28))

for i, g in enumerate(spacegroups):
    for j, target in enumerate([t1, t2]):
        plt.subplot(n_spacegroups, 2, i * 2 + j + 1)
        if j == 0:
            plt.ylabel('spacegroup=%d' % g)
        plt.scatter(range(X_validation[X_validation['spacegroup'] == g].shape[0]), y_validation.loc[X_validation[X_validation['spacegroup'] == g].index, target], s=12, label='labels')
        plt.scatter(range(X_validation[X_validation['spacegroup'] == g].shape[0]), pd_y_pred.loc[X_validation[X_validation['spacegroup'] == g].index, target], s=12, label='predictions')
        plt.legend()

plt.show()
"""

# sample submission
sample = pd.read_csv('Data/sample_submission.csv')
sample.head()

y_train = np.log1p(train[[t1, t2]])
X_train = train.drop(['id', t1, t2], axis=1)

sess = tf.Session()
sess.run(tf.global_variables_initializer())

loss_data = []
for step in range(20000):
    # training loss
    _, l, l_y = sess.run([train_op, loss_total, loss_y],
                         {tf_x: X_train, tf_y: y_train, tf_is_training: True})

    loss_data.append([step, l, l_y[0], l_y[1]])
print("Final training losses")
print(loss_data[-1][1:])

loss_data = np.array(loss_data)

"""
plt.figure(figsize=(14, 8))
plt.subplot(2, 1, 1)
plt.title('loss')
plt.plot(loss_data[:, 0], loss_data[:, 1])
plt.subplot(2, 2, 3)
plt.title(t1)
plt.plot(loss_data[:, 0], loss_data[:, 2])
plt.subplot(2, 2, 4)
plt.title(t2)
plt.plot(loss_data[:, 0], loss_data[:, 3])
plt.show()
"""

X_test = test.drop(['id'], axis=1)
pred_y = sess.run(output, {tf_x: X_test, tf_is_training: False})

pred_y = np.expm1(pred_y)

pred_y[pred_y[:, 0] < 0, 0] = 0
pred_y[pred_y[:, 1] < 0, 1] = 0

subm = pd.DataFrame()
subm['id'] = sample['id']
subm[t1] = pred_y[:, 0]
subm[t2] = pred_y[:, 1]
subm.to_csv("subm2.csv", index=False)

subm.head()
