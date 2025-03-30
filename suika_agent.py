import numpy as np
import random
from collections import defaultdict
import pickle
import os
from constants import WINDOW_WIDTH

class SuikaAgent:
    def __init__(self, state_size=10, action_size=10, learning_rate=0.2, discount_factor=0.99, epsilon=1.0):
        self.state_size = state_size  # Number of grid cells for discretization
        self.action_size = action_size  # Number of possible drop positions
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.997  # Slower decay for more exploration
        self.q_table = defaultdict(lambda: np.zeros(action_size))
        self.model_file = "suika_agent.pkl"
        
        # Training statistics
        self.training_scores = []
        self.training_rewards = []
        self.best_score = 0
        self.total_episodes = 0
        self.episode_rewards = []
        self.episode_scores = []
        self.avg_score = 0
        self.avg_reward = 0
        
        self.load_model()

    def get_state(self, fruits):
        """Convert game state to a discrete representation"""
        # Create a grid representation of the game state
        state = []
        for fruit in fruits:
            # Discretize x and y positions with finer granularity
            x = int(fruit.position.x * self.state_size)
            y = int(fruit.position.y * self.state_size)
            kind = fruit.kind
            # Add velocity information
            velocity = int(fruit.scalar_velocity * 5)  # Scale velocity for discretization
            state.append((x, y, kind, velocity))
        return tuple(sorted(state))  # Sort to ensure same state gives same hash

    def get_action(self, state, available_width):
        """Choose action using epsilon-greedy policy"""
        if random.random() < self.epsilon:
            # Exploration: choose random action
            return random.random() * available_width
        else:
            # Exploitation: choose best action
            discretized_state = self.discretize_state(state)
            actions = self.q_table[discretized_state]
            return (np.argmax(actions) / self.action_size) * available_width

    def discretize_state(self, state):
        """Convert continuous state to discrete state for Q-table"""
        if not state:
            return (0,)
        # Use more fruits to capture more context
        top_n = 8  # Increased from 5 to 8
        state_list = list(state)[:top_n]
        return tuple(state_list)

    def train(self, state, action, reward, next_state, done):
        """Update Q-values using Q-learning algorithm"""
        disc_state = self.discretize_state(state)
        disc_next_state = self.discretize_state(next_state)
        
        # Discretize action
        disc_action = int((action * self.action_size) / WINDOW_WIDTH)
        disc_action = min(disc_action, self.action_size - 1)  # Ensure action is within bounds
        
        # Q-learning update
        old_value = self.q_table[disc_state][disc_action]
        next_max = np.max(self.q_table[disc_next_state])
        new_value = (1 - self.lr) * old_value + self.lr * (reward + self.gamma * next_max)
        self.q_table[disc_state][disc_action] = new_value

    def update_training_stats(self, episode, score, cumulative_reward):
        """Update training statistics"""
        self.episode_rewards.append(cumulative_reward)
        self.episode_scores.append(score)
        self.total_episodes = episode
        
        # Update best score
        if score > self.best_score:
            self.best_score = score
            self.save_model()  # Save model when we get a new best score
            
        # Calculate averages over last 10 episodes
        if len(self.episode_scores) >= 10:
            self.avg_score = np.mean(self.episode_scores[-10:])
            self.avg_reward = np.mean(self.episode_rewards[-10:])
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        # Print training progress after each episode
        print(f"\n=== Episode {episode} Complete ===")
        print(f"Score: {score}")
        print(f"Best Score: {self.best_score}")
        print(f"Average Score (last 10): {self.avg_score:.2f}")
        print(f"Average Reward (last 10): {self.avg_reward:.2f}")
        print(f"Current Epsilon: {self.epsilon:.3f}")
        print(f"Q-table size: {len(self.q_table)}")
        print("=" * 30)

    def save_model(self):
        """Save Q-table and training stats to file"""
        save_data = {
            'q_table': dict(self.q_table),
            'episode_scores': self.episode_scores,
            'episode_rewards': self.episode_rewards,
            'best_score': self.best_score,
            'total_episodes': self.total_episodes,
            'epsilon': self.epsilon,
            'avg_score': self.avg_score,
            'avg_reward': self.avg_reward
        }
        with open(self.model_file, 'wb') as f:
            pickle.dump(save_data, f)

    def load_model(self):
        """Load Q-table and training stats from file if it exists"""
        if os.path.exists(self.model_file):
            with open(self.model_file, 'rb') as f:
                save_data = pickle.load(f)
                self.q_table = defaultdict(lambda: np.zeros(self.action_size), save_data['q_table'])
                self.episode_scores = save_data.get('episode_scores', [])
                self.episode_rewards = save_data.get('episode_rewards', [])
                self.best_score = 0  # Reset best score to 0 each time
                self.total_episodes = save_data.get('total_episodes', 0)
                self.epsilon = save_data.get('epsilon', self.epsilon)
                self.avg_score = save_data.get('avg_score', 0)
                self.avg_reward = save_data.get('avg_reward', 0) 