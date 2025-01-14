# encoding: utf-8

##
## cartpole.py
## Gaetan JUVIN 06/24/2017
##

import gymnasium as gym
import random
import os
import numpy as np

from collections import deque
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam

class Agent():
    def __init__(self, state_size, action_size):
        self.weight_backup = "cartpole_weight.h5"
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.learning_rate = 0.001
        self.gamma = 0.9
        self.exploration_rate = 1.0
        self.exploration_min = 0.01
        self.exploration_decay = 0.996
        self.brain = self._build_model()

    def _build_model(self):
        # Neural Net for Deep-Q learning Model
        model = Sequential()
        model.add(Dense(24, input_dim=self.state_size, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(learning_rate=self.learning_rate))

        if os.path.isfile(self.weight_backup):
            model.load_weights(self.weight_backup)
            self.exploration_rate = self.exploration_min
        return model

    def save_model(self):
        self.brain.save(self.weight_backup)

    def act(self, state):
        if np.random.rand() <= self.exploration_rate:
            return random.randrange(self.action_size)
        act_values = np.array(self.brain(state, training=False))
        return np.argmax(act_values[0])

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def replay(self, sample_batch_size):
        if len(self.memory) < sample_batch_size:
            return
        sample_batch = random.sample(self.memory, sample_batch_size)
        state_batch = np.empty((sample_batch_size, 4))
        target_batch = np.empty((sample_batch_size, 2))
        index = 0
        for state, action, reward, next_state, done in sample_batch:
            state_batch[index] = state[0]
            if not done:
                target = reward + self.gamma * np.amax(np.array(self.brain(next_state, training=False))[0])
            else:
                target = reward
            current_target = np.array(self.brain(state, training=False))
            current_target[0][action] = target
            target_batch[index] = current_target[0]
            index = index + 1
        self.brain.fit(state_batch, target_batch, epochs=3, verbose=0)
        if self.exploration_rate > self.exploration_min:
            self.exploration_rate *= self.exploration_decay


class CartPole:
    def __init__(self, training=False):
        self.sample_batch_size = 128

        if not training:
            self.env = gym.make('CartPole-v1', render_mode="human")
            self.episodes = 1
        else:
            self.env = gym.make('CartPole-v1')
            self.episodes = 10000

        self.state_size = self.env.observation_space.shape[0]
        self.action_size = self.env.action_space.n
        self.agent = Agent(self.state_size, self.action_size)

    def run(self, training=False):
        try:
            for index_episode in range(self.episodes):
                state, _ = self.env.reset()
                state = np.reshape(state, [1, self.state_size])

                done = False
                index = 0
                while not done:
                    action = self.agent.act(state)

                    next_state, reward, done, _, _ = self.env.step(action)
                    next_state = np.reshape(next_state, [1, self.state_size])
                    self.agent.remember(state, action, reward, next_state, done)
                    state = next_state
                    index += 1
                    if index >= 100000 and training == True:
                        training = False
                        break
                print("Episode {}# Score: {}".format(index_episode, index + 1))
                if training:
                    self.agent.replay(self.sample_batch_size)
                else:
                    break
        finally:
            self.agent.save_model()


if __name__ == "__main__":
    cartpole = CartPole(training=False)
    cartpole.run(training=False)
