"""
Deep Q-Network (DQN) Training for Meal Sequencing

Trains a DQN agent to select optimal meal sequences
given remaining macro targets. Uses a simulated meal environment.
"""

import json, os, sys, random
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from collections import deque
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class MealEnvironment:
    """Simulated meal environment for DQN training."""

    MEALS = [
        {"name": "Oatmeal & Protein", "calories": 350, "protein": 30, "carbs": 45, "fat": 8, "time": "breakfast"},
        {"name": "Eggs & Avocado Toast", "calories": 420, "protein": 25, "carbs": 30, "fat": 22, "time": "breakfast"},
        {"name": "Grilled Chicken Salad", "calories": 380, "protein": 40, "carbs": 15, "fat": 18, "time": "lunch"},
        {"name": "Turkey Wrap", "calories": 450, "protein": 35, "carbs": 40, "fat": 14, "time": "lunch"},
        {"name": "Salmon & Rice", "calories": 520, "protein": 42, "carbs": 50, "fat": 16, "time": "dinner"},
        {"name": "Lean Steak & Veggies", "calories": 480, "protein": 45, "carbs": 20, "fat": 22, "time": "dinner"},
        {"name": "Greek Yogurt & Berries", "calories": 200, "protein": 20, "carbs": 25, "fat": 3, "time": "snack"},
        {"name": "Protein Shake", "calories": 180, "protein": 30, "carbs": 8, "fat": 3, "time": "snack"},
    ]

    MEAL_TIMES = ["breakfast", "lunch", "dinner", "snack"]

    def __init__(self, daily_calories: float = 2000, protein_target: float = 150):
        self.daily_calories = daily_calories
        self.protein_target = protein_target
        self.reset()

    def reset(self):
        self.cal_remaining = self.daily_calories
        self.protein_remaining = self.protein_target
        self.day = 0
        self.totals = {"calories": 0, "protein": 0}
        return self._get_state()

    def _get_state(self) -> np.ndarray:
        return np.array([
            self.cal_remaining / self.daily_calories,
            self.protein_remaining / self.protein_target,
            self.day / 7,
        ], dtype=np.float32)

    def step(self, action_idx: int) -> Tuple[np.ndarray, float, bool]:
        meal = self.MEALS[action_idx % len(self.MEALS)]
        self.cal_remaining -= meal["calories"]
        self.protein_remaining -= meal["protein"]
        self.totals["calories"] += meal["calories"]
        self.totals["protein"] += meal["protein"]

        cal_diff = abs(self.cal_remaining)
        prot_diff = abs(self.protein_remaining)
        reward = -0.001 * cal_diff - 0.005 * prot_diff
        if 0 <= self.cal_remaining < 200 and 0 <= self.protein_remaining < 20:
            reward += 50.0

        done = self.cal_remaining <= 0 or self.protein_remaining <= 0 or self.day >= 7
        self.day += 1
        return self._get_state(), reward, done


class DQN(nn.Module):
    def __init__(self, state_dim: int, action_dim: int, hidden: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
            nn.Linear(hidden, action_dim),
        )

    def forward(self, x):
        return self.net(x)


class ReplayBuffer:
    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int) -> List[Tuple]:
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))

    def __len__(self):
        return len(self.buffer)


class DQNTrainer:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or "app/training/models/dqn")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.mock_mode = not TORCH_AVAILABLE

    def train(self, episodes: int = 500, batch_size: int = 64, lr: float = 0.001,
              gamma: float = 0.99, epsilon_start: float = 1.0, epsilon_end: float = 0.01,
              epsilon_decay: float = 0.995) -> Dict:
        if self.mock_mode:
            return self._mock_result(episodes)

        print("=" * 70)
        print("  DQN MEAL SEQUENCER TRAINING")
        print("=" * 70)
        print(f"  Episodes: {episodes} | Batch: {batch_size} | LR: {lr} | Gamma: {gamma}")
        print()

        state_dim = 3
        action_dim = len(MealEnvironment.MEALS)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        policy_net = DQN(state_dim, action_dim).to(device)
        target_net = DQN(state_dim, action_dim).to(device)
        target_net.load_state_dict(policy_net.state_dict())
        target_net.eval()

        optimizer = optim.Adam(policy_net.parameters(), lr=lr)
        memory = ReplayBuffer(10000)
        criterion = nn.MSELoss()

        epsilon = epsilon_start
        total_rewards = []
        best_avg_reward = -float("inf")

        for ep in range(episodes):
            env = MealEnvironment()
            state = env.reset()
            total_reward = 0.0
            done = False

            while not done:
                if random.random() < epsilon:
                    action = random.randrange(action_dim)
                else:
                    with torch.no_grad():
                        q_vals = policy_net(torch.FloatTensor(state).unsqueeze(0).to(device))
                        action = q_vals.argmax().item()

                next_state, reward, done = env.step(action)
                memory.push(state, action, reward, next_state, done)
                state = next_state
                total_reward += reward

                if len(memory) >= batch_size:
                    batch = memory.sample(batch_size)
                    states = torch.FloatTensor(np.array([b[0] for b in batch])).to(device)
                    actions = torch.LongTensor([b[1] for b in batch]).to(device)
                    rewards = torch.FloatTensor([b[2] for b in batch]).to(device)
                    next_states = torch.FloatTensor(np.array([b[3] for b in batch])).to(device)
                    dones = torch.FloatTensor([b[4] for b in batch]).to(device)

                    current_q = policy_net(states).gather(1, actions.unsqueeze(1))
                    with torch.no_grad():
                        next_q = target_net(next_states).max(1)[0]
                        target_q = rewards + gamma * next_q * (1 - dones)

                    loss = criterion(current_q.squeeze(), target_q.detach())
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()

            epsilon = max(epsilon_end, epsilon * epsilon_decay)
            total_rewards.append(total_reward)

            avg_reward = np.mean(total_rewards[-50:]) if len(total_rewards) >= 50 else np.mean(total_rewards)

            if (ep + 1) % 100 == 0 or ep == 0:
                print(f"Episode [{ep+1}/{episodes}] Reward: {total_reward:.1f} | Avg(50): {avg_reward:.1f} | Epsilon: {epsilon:.3f}")

            if (ep + 1) % 10 == 0:
                target_net.load_state_dict(policy_net.state_dict())

            if avg_reward > best_avg_reward:
                best_avg_reward = avg_reward
                torch.save(policy_net.state_dict(), self.output_dir / "dqn_meal.pth")

        print(f"\n[OK] Training complete! Best avg reward: {best_avg_reward:.2f}")
        print(f"[SAVE] Model saved to {self.output_dir / 'dqn_meal.pth'}")

        return {
            "status": "success",
            "episodes": episodes,
            "best_avg_reward": round(best_avg_reward, 2),
            "final_avg_reward": round(np.mean(total_rewards[-100:]), 2),
            "final_epsilon": round(epsilon, 4),
            "model_path": str(self.output_dir / "dqn_meal.pth"),
            "state_dim": state_dim,
            "action_dim": action_dim,
        }

    def _mock_result(self, episodes: int) -> Dict:
        return {
            "status": "mock",
            "episodes": episodes,
            "best_avg_reward": 42.5,
            "final_avg_reward": 38.7,
            "model_path": str(self.output_dir / "dqn_meal.pth"),
            "note": "Install PyTorch for real training",
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train DQN meal sequencer")
    parser.add_argument("--episodes", type=int, default=500)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--gamma", type=float, default=0.99)
    args = parser.parse_args()

    trainer = DQNTrainer()
    result = trainer.train(episodes=args.episodes, batch_size=args.batch, lr=args.lr, gamma=args.gamma)
    print(f"\n[RESULT] {json.dumps(result, indent=2)}")
