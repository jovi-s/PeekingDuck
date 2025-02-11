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
"""callback logger class"""

import logging
import time
import pandas as pd
from configs import LOGGER_NAME

from src.trainer.base import Trainer
from src.callbacks.base import Callback
from src.callbacks.order import CallbackOrder


logger = logging.getLogger(LOGGER_NAME)  # pylint: disable=invalid-name


# pylint: disable=logging-fstring-interpolation
class Logger(Callback):
    """Logger"""

    def __init__(self) -> None:
        """Constructor for Logger class."""
        super().__init__(order=CallbackOrder.LOGGER)
        self.logger: logging.Logger = logger
        self.train_elapsed_time: str = ""
        self.valid_elapsed_time: str = ""
        self.train_start_time: float = 0.0
        self.val_start_time: float = 0.0

    def on_trainer_start(self, trainer: Trainer) -> None:
        """on_trainer_start"""
        self.logger.info(f"Fold {trainer.current_fold} started")

    def on_train_loader_end(self, trainer: Trainer) -> None:
        """on_train_loader_end"""
        metrics_df = pd.DataFrame.from_dict([trainer.epoch_dict["train"]["metrics"]])
        self.logger.info(f"\ntrain_metrics:\n{metrics_df}\n")

    # pylint: disable=unused-argument
    def on_train_epoch_start(self, trainer: Trainer) -> None:
        """on_train_epoch_start"""
        self.train_start_time = time.time()

    def on_train_epoch_end(self, trainer: Trainer) -> None:
        """on_train_epoch_end"""
        # total time elapsed for the epoch
        self.train_elapsed_time = time.strftime(
            "%H:%M:%S", time.gmtime(time.time() - self.train_start_time)
        )
        trainer.train_elapsed_time = self.train_elapsed_time
        self.logger.info(
            f"\n[RESULT]: Train. Epoch {trainer.current_epoch}:"
            f"\nAvg Train Summary Loss: {trainer.epoch_dict['train']['train_loss']:.3f}"
            f"\nLearning Rate: {trainer.curr_lr:.5f}"
            f"\nTime Elapsed: {self.train_elapsed_time}\n"
        )

    def on_valid_loader_end(self, trainer: Trainer) -> None:
        """on_valid_loader_end"""
        metrics_df = pd.DataFrame.from_dict(
            [trainer.epoch_dict["validation"]["metrics"]]
        )
        self.logger.info(f"\nvalid_metrics:\n{metrics_df}\n")

    # pylint: disable=unused-argument
    def on_valid_epoch_start(self, trainer: Trainer) -> None:
        """on_valid_epoch_start"""
        self.val_start_time = time.time()  # start time for validation

    def on_valid_epoch_end(self, trainer: Trainer) -> None:
        """on_valid_epoch_end"""
        # total time elapsed for the epoch
        self.valid_elapsed_time = time.strftime(
            "%H:%M:%S", time.gmtime(time.time() - self.val_start_time)
        )
        trainer.valid_elapsed_time = self.valid_elapsed_time
        self.logger.info(
            f"\n[RESULT]: Validation. Epoch {trainer.current_epoch}:"
            f"\nAvg Val Summary Loss: {trainer.epoch_dict['validation']['valid_loss']:.3f}"
            f"\nAvg Val Accuracy: "
            f"{trainer.epoch_dict['validation']['metrics']['val_MulticlassAccuracy']:.3f}"
            f"\nAvg Val Macro AUROC: "
            f"{trainer.epoch_dict['validation']['metrics']['val_MulticlassAUROC']:.3f}"
            f"\nTime Elapsed: {self.valid_elapsed_time}\n"
        )
