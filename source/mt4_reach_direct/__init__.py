import gymnasium as gym

from .mt4_reach_env import MT4ReachEnv, MT4ReachEnvCfg
from .mt4_mars_twin_env import (
    MT4MarsTwinEnv,
    MT4MarsTwinPickEnvCfg,
    MT4MarsTwinPlaceEnvCfg,
    MT4MarsTwinPullEnvCfg,
    MT4MarsTwinPushEnvCfg,
    MT4MarsTwinStackEnvCfg,
)
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

_MARS_TWIN_TASKS = {
    "Isaac-MT4-Mars-Twin-Pick-Direct-v0": MT4MarsTwinPickEnvCfg,
    "Isaac-MT4-Mars-Twin-Place-Direct-v0": MT4MarsTwinPlaceEnvCfg,
    "Isaac-MT4-Mars-Twin-Stack-Direct-v0": MT4MarsTwinStackEnvCfg,
    "Isaac-MT4-Mars-Twin-Push-Direct-v0": MT4MarsTwinPushEnvCfg,
    "Isaac-MT4-Mars-Twin-Pull-Direct-v0": MT4MarsTwinPullEnvCfg,
}

for task_id, cfg_cls in _MARS_TWIN_TASKS.items():
    gym.register(
        id=task_id,
        entry_point=f"{__name__}.mt4_mars_twin_env:MT4MarsTwinEnv",
        disable_env_checker=True,
        kwargs={
            "env_cfg_entry_point": cfg_cls,
            "rsl_rl_cfg_entry_point": f"{agents.__name__}.rsl_rl_ppo_cfg:MT4ReachPPORunnerCfg",
        },
    )
