import gymnasium as gym

from .mt4_reach_env import MT4ReachEnv, MT4ReachEnvCfg
from . import agents

gym.register(
    id="Isaac-MT4-Simplified-Reach-Direct-v0",
    entry_point=f"{__name__}.mt4_reach_env:MT4ReachEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": MT4ReachEnvCfg,
        "rsl_rl_cfg_entry_point": f"{agents.__name__}.rsl_rl_ppo_cfg:MT4ReachPPORunnerCfg",
    },
)
