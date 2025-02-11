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

"""data module"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import logging

from albumentations import Compose
from hydra.utils import instantiate
from omegaconf import DictConfig
import pandas as pd

from torch.utils.data import DataLoader

from src.data.base import AbstractDataSet
from src.data.dataset import PTImageClassificationDataset
from src.data.data_adapter import DataAdapter
from src.transforms.augmentations import ImageClassificationTransforms
from src.utils.general_utils import (
    create_dataframe_with_image_info,
    download_to,
    extract_file,
    return_list_of_files,
    stratified_sample_df,
)

from configs import LOGGER_NAME

# pylint: disable=invalid-name,too-many-instance-attributes,logging-fstring-interpolation
logger: logging.Logger = logging.getLogger(LOGGER_NAME)


class ImageClassificationDataModule:
    """Data module for generic image classification dataset."""

    def __init__(
        self,
        cfg: DictConfig,
        **kwargs: Dict[str, Any],
    ) -> None:
        self.cfg: DictConfig = cfg
        self.transforms: ImageClassificationTransforms = ImageClassificationTransforms(
            cfg.transform[cfg.framework]
        )
        self.dataset_loader: Optional[DataAdapter] = None  # Setup in self.setup()

        self.train_df: pd.DataFrame
        self.test_df: pd.DataFrame
        self.validation_df: pd.DataFrame
        self.train_dataset: Union[AbstractDataSet, pd.DataFrame]
        self.validation_dataset: Union[AbstractDataSet, pd.DataFrame]
        self.test_dataset: Union[AbstractDataSet, pd.DataFrame]
        self.train_transforms: Compose = self.transforms.train_transforms
        self.validation_transforms: Compose = self.transforms.validation_transforms
        self.test_transforms: Compose = self.transforms.test_transforms
        self.kwargs = kwargs

    def get_train_dataloader(self) -> Union[DataLoader, AbstractDataSet]:
        """Return training data loader adapter"""
        assert self.dataset_loader is not None, "call setup() before getting dataloader"
        return self.dataset_loader.train_dataloader(
            self.train_dataset,
            transforms=self.train_transforms,
        )

    def get_validation_dataloader(
        self,
    ) -> Union[DataLoader, AbstractDataSet]:
        """Return validation data loader adapter"""
        assert self.dataset_loader is not None, "call setup() before getting dataloader"
        return self.dataset_loader.validation_dataloader(
            self.validation_dataset,
            transforms=self.validation_transforms,
        )

    def get_test_dataloader(self) -> Union[DataLoader, AbstractDataSet]:
        """Return test data loader adapter"""
        assert self.dataset_loader is not None, "call setup() before getting dataloader"
        return self.dataset_loader.test_dataloader(
            self.test_dataset,
            transforms=self.test_transforms,
        )

    def prepare_data(self) -> None:
        """Step 2 after __init__()
        Load the dataframe from user-defined csv file"""
        url: str = self.cfg.dataset.url
        blob_file: str = self.cfg.dataset.blob_file
        root_dir: Path = Path(self.cfg.dataset.root_dir)
        train_dir: Path = Path(self.cfg.dataset.train_dir)
        test_dir: Path = Path(self.cfg.dataset.test_dir)
        class_name_to_id: Dict[str, int] = self.cfg.dataset.class_name_to_id
        train_csv: str = self.cfg.dataset.train_csv
        stratify_by: List[Any] = self.cfg.dataset.stratify_by

        if self.cfg.dataset.download:
            logger.info(f"downloading from {url} to {blob_file} in {root_dir}")
            download_to(url, blob_file, root_dir)
            extract_file(root_dir, blob_file)

        train_images: Union[List[str], List[Path]] = return_list_of_files(
            train_dir, extensions=[".jpg", ".png", ".jpeg"], return_string=False
        )
        test_images: Union[List[str], List[Path]] = return_list_of_files(
            test_dir, extensions=[".jpg", ".png", ".jpeg"], return_string=False
        )
        logger.info(f"Total number of images: {len(train_images)}")
        logger.info(f"Total number of test images: {len(test_images)}")

        if Path(train_csv).exists():
            # this step is assumed to be done by user where
            # image_path is inside the csv.
            df: pd.DataFrame = pd.read_csv(train_csv)
        else:
            # only invoke this if images are store in the following format
            # train_dir
            #   - class1 ...
            df = create_dataframe_with_image_info(
                train_images,
                class_name_to_id,
                save_path=train_csv,
            )
        logger.info(df.head())

        self.train_df = df

        self.train_df, self.test_df = self._cross_validation_split(
            self.cfg.resample.resample_strategy, df, stratify_by=stratify_by
        )
        self.train_df, self.validation_df = self._cross_validation_split(
            self.cfg.resample.resample_strategy, self.train_df, stratify_by=stratify_by
        )

        if self.cfg.debug:
            num_debug_samples: int = self.cfg.num_debug_samples
            logger.info(
                f"Debug mode is on, using {num_debug_samples} images for training."
            )
            if stratify_by is None:
                self.train_df = self.train_df.sample(num_debug_samples)
                self.validation_df = self.validation_df.sample(num_debug_samples)
            else:
                self.train_df = stratified_sample_df(
                    self.train_df, stratify_by, num_debug_samples
                )
                self.validation_df = stratified_sample_df(
                    self.validation_df, stratify_by, num_debug_samples
                )

        logger.info(self.train_df.info())

    def setup(self, stage: str) -> None:
        """Step 3 after prepare()"""

        if stage == "fit":
            if self.cfg.framework == "pytorch":
                self.train_dataset = PTImageClassificationDataset(
                    self.cfg,
                    dataframe=self.train_df,
                    stage="train",
                    transforms=self.train_transforms,
                )
                self.validation_dataset = PTImageClassificationDataset(
                    self.cfg,
                    dataframe=self.validation_df,
                    stage="valid",
                    transforms=self.validation_transforms,
                )
                self.test_dataset = PTImageClassificationDataset(
                    self.cfg,
                    dataframe=self.test_df,
                    stage="test",
                    transforms=self.test_transforms,
                )
            if self.cfg.framework == "tensorflow":
                self.train_dataset = self.train_df
                self.validation_dataset = self.validation_df
                self.test_dataset = self.test_df

        self.dataset_loader = DataAdapter(self.cfg.data_adapter[self.cfg.framework])

    @staticmethod
    def _cross_validation_split(
        resample_strategy: DictConfig,
        df: pd.DataFrame,
        # fold: Optional[int] = None,
        stratify_by: Optional[list] = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Split the dataframe into train and validation dataframes."""
        resample_func = instantiate(resample_strategy)

        if stratify_by is None:
            return resample_func(df)

        logger.info(f"stratify_by: {stratify_by}")
        return resample_func(df, stratify=df[stratify_by])
