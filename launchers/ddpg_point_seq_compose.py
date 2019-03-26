import os.path as osp

from garage.config import GARAGE_LOG_DIR
from garage.experiment import run_experiment
from garage.exploration_strategies import OUStrategy
from garage.tf.algos import DDPG
from garage.tf.envs import TfEnv
from garage.tf.policies import ContinuousMLPPolicy
from garage.tf.q_functions import ContinuousMLPQFunction
import joblib
import tensorflow as tf

from embed2learn.envs import AlmostContinuousEmbeddedPolicyEnv
from embed2learn.envs import SequencePointEnv


USE_LOG = "local/ppo-point-embed-random-start-192-polent/ppo_point_embed_random_start_192_polent_2018_08_14_17_01_37_0001"
latent_policy_pkl = osp.join(GARAGE_LOG_DIR, USE_LOG, "itr_400.pkl")


def run_task(*_):
    sess = tf.Session()
    sess.__enter__()
    latent_policy = joblib.load(latent_policy_pkl)["policy"]

    inner_env = SequencePointEnv(completion_bonus=100)
    env = TfEnv(AlmostContinuousEmbeddedPolicyEnv(inner_env, latent_policy))

    action_noise = OUStrategy(env, sigma=0.8)

    actor_net = ContinuousMLPPolicy(
        env_spec=env.spec,
        name="Actor",
        hidden_sizes=[64, 64],
        hidden_nonlinearity=tf.nn.relu,
        output_nonlinearity=tf.nn.tanh)

    critic_net = ContinuousMLPQFunction(
        env_spec=env.spec,
        name="Critic",
        hidden_sizes=[64, 64],
        hidden_nonlinearity=tf.nn.relu)

    ddpg = DDPG(
        env.spec,
        actor=actor_net,
        actor_lr=1e-4,
        critic_lr=1e-3,
        critic=critic_net,
        plot=False,
        target_update_tau=1e-2,
        n_epochs=500,
        n_epoch_cycles=100,
        n_rollout_steps=50,
        n_train_steps=50,
        discount=0.9,
        replay_buffer_size=int(1e6),
        min_buffer_size=int(1e4),
        exploration_strategy=action_noise,
        actor_optimizer=tf.train.AdamOptimizer,
        critic_optimizer=tf.train.AdamOptimizer,)

    ddpg.train(sess=sess)


run_experiment(
    run_task,
    n_parallel=2,
    exp_prefix="ddpg_point_compose_seq",
    seed=1,
    plot=True,
)
