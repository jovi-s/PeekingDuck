# Copyright 2023 AI Singapore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test training pipeline script"""
from typing import List
from pytest import mark

from hydra import compose, initialize

import src.training_pipeline
from src.utils.general_utils import seed_all


# Drives some framework with the composed config.
# In this case it calls src.training_pipeline.run(), passing it the composed config.
@mark.parametrize(
    "overrides, validation_loss_key, expected",
    [
        (
            [
                "project_name=test_training_pipeline_pytorch",
                "use_case=classification",
                "data_module/dataset=cifar10",
                "use_case.framework=pytorch",
                "use_case.debug=True",
                "use_case.random_state=11",
                "use_case.view_only=False",
                "data_module.num_debug_samples=180",
                "data_module.dataset.image_size=32",
                "data_module.dataset.download=True",
                "data_module.data_adapter.pytorch.train.batch_size=16",
                "data_module.data_adapter.pytorch.validation.batch_size=16",
                "data_module.data_adapter.pytorch.test.batch_size=16",
                "model.pytorch.adapter=timm",
                "model.pytorch.model_name=vgg16",
                "trainer.pytorch.stores.model_artifacts_dir=null",
            ],
            "valid_loss",
            1.5,
        ),
    ],
)
def test_training_pipeline_pytorch(
    overrides: List[str], validation_loss_key: str, expected: float
) -> None:
    """test_training_pipeline"""
    with initialize(version_base=None, config_path="../../configs"):
        cfg = compose(
            config_name="config",
            overrides=overrides,
        )
        trainer_config = cfg.trainer[cfg.use_case.framework]
        train_params = trainer_config.global_train_params
        seed_all(train_params.manual_seed)
        history = src.training_pipeline.run(cfg)
        assert history is not None
        assert validation_loss_key in history
        assert len(history[validation_loss_key]) != 0
        print(f"validation_loss: {history[validation_loss_key][-1]}")
        assert history[validation_loss_key][-1] < expected
