"""
Q-Learning Habit Formation Training

Trains a tabular Q-Learning agent to optimize habit-building strategies.
Uses a simulated habit environment with streak mechanics.
"""

import json, os, random, math
from pathlib import Path
from typing import Optional, Dict, Tuple
import numpy as np


class HabitEnvironment:
    """Simulated habit environment for Q-Learning."""

    HABIT_TYPES = ["eat_protein_breakfast", "log_meals", "drink_water", "exercise_30min", "sleep_8hrs"]
    MAX_STREAK = 30
    DAYS_TO_FORM = 21

    def __init__(self, habit: str = "log_meals"):
        self.habit = habit
        self.reset()

    def reset(self):
        self.streak = 0
        self.day = 0
        self.motivation = 1.0
        return self._get_state()

    def _get_state(self) -> Tuple[int, float, int]:
        return (min(self.streak, self.MAX_STREAK), round(self.motivation, 2), self.day % 7)

    def step(self, action: int) -> Tuple[Tuple, float, bool]:
        """
        Action: 0 = skip, 1 = complete
        """
        if action == 1:
            self.streak += 1
            base_reward = 10.0
            streak_bonus = min(self.streak * 0.5, 25.0)
            motivation_boost = 0.05
            self.motivation = min(self.motivation + motivation_boost, 1.0)
            reward = base_reward + streak_bonus
            if self.streak >= self.DAYS_TO_FORM:
                reward += 50.0
        else:
            self.streak = 0
            self.motivation = max(self.motivation - 0.1, 0.3)
            reward = -2.0

        self.day += 1
        done = self.day >= 90
        return self._get_state(), reward, done

    def get_state_size(self) -> int:
        return len(self._get_state())


class QTable:
    def __init__(self, state_bins: Tuple = (30, 10, 7), n_actions: int = 2):
        self.state_bins = state_bins
        self.n_actions = n_actions
        self.q = {}

    def _discretize(self, state: Tuple) -> Tuple:
        streak = min(int(state[0]), self.state_bins[0] - 1)
        motivation = min(int(state[1] * self.state_bins[1]), self.state_bins[1] - 1)
        day_of_week = min(state[2], self.state_bins[2] - 1)
        return (streak, motivation, day_of_week)

    def get(self, state: Tuple, action: int) -> float:
        key = (*self._discretize(state), action)
        return self.q.get(key, 0.0)

    def set(self, state: Tuple, action: int, value: float):
        key = (*self._discretize(state), action)
        self.q[key] = value

    def size(self) -> int:
        return len(self.q)


class QLearningTrainer:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or "app/training/models/qlearning")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def train(self, episodes: int = 1000, alpha: float = 0.1, gamma: float = 0.95,
              epsilon_start: float = 1.0, epsilon_end: float = 0.01) -> Dict:
        print("=" * 70)
        print("  Q-LEARNING HABIT FORMATION TRAINING")
        print("=" * 70)
        print(f"  Episodes: {episodes} | Alpha: {alpha} | Gamma: {gamma}")
        print()

        habits = HabitEnvironment.HABIT_TYPES
        q_tables = {h: QTable() for h in habits}
        episode_rewards = {h: [] for h in habits}

        for habit in habits:
            epsilon = epsilon_start
            best_avg = -float("inf")
            q = q_tables[habit]

            for ep in range(episodes):
                env = HabitEnvironment(habit)
                state = env.reset()
                total_reward = 0.0
                done = False

                while not done:
                    if random.random() < epsilon:
                        action = random.randrange(2)
                    else:
                        if q.get(state, 0) >= q.get(state, 1):
                            action = 0
                        else:
                            action = 1

                    next_state, reward, done = env.step(action)
                    old_q = q.get(state, action)
                    next_max = max(q.get(next_state, 0), q.get(next_state, 1))
                    new_q = old_q + alpha * (reward + gamma * next_max - old_q)
                    q.set(state, action, new_q)

                    state = next_state
                    total_reward += reward

                epsilon = max(epsilon_end, epsilon * 0.998)
                episode_rewards[habit].append(total_reward)

                avg = np.mean(episode_rewards[habit][-100:]) if len(episode_rewards[habit]) >= 100 else np.mean(episode_rewards[habit])
                if avg > best_avg:
                    best_avg = avg

            print(f"  {habit}: {ep} eps, best avg reward: {best_avg:.1f}, Q-table size: {q.size()}")

        # Save all Q-tables
        import joblib
        model_path = self.output_dir / "qlearning_habits.joblib"
        joblib.dump({h: qt.q for h, qt in q_tables.items()}, model_path)
        print(f"\n[OK] Training complete!")
        print(f"[SAVE] Model saved to {model_path}")

        return {
            "status": "success",
            "episodes": episodes,
            "habits_trained": habits,
            "q_table_sizes": {h: qt.size() for h, qt in q_tables.items()},
            "final_avg_rewards": {
                h: round(np.mean(episode_rewards[h][-100:]), 2) if len(episode_rewards[h]) >= 100 else round(np.mean(episode_rewards[h]), 2)
                for h in habits
            },
            "model_path": str(model_path),
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train Q-Learning habit former")
    parser.add_argument("--episodes", type=int, default=1000)
    parser.add_argument("--alpha", type=float, default=0.1)
    parser.add_argument("--gamma", type=float, default=0.95)
    args = parser.parse_args()

    trainer = QLearningTrainer()
    result = trainer.train(episodes=args.episodes, alpha=args.alpha, gamma=args.gamma)
    print(f"\n[RESULT] {json.dumps(result, indent=2)}")
