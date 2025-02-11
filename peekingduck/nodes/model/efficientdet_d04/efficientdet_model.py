# Copyright 2022 AI Singapore
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

"""
EfficientDet model with model types: D0-D4
"""

import json
import logging
from typing import Any, Dict, List, Tuple

import numpy as np

from peekingduck.nodes.base import ThresholdCheckerMixin, WeightsDownloaderMixin
from peekingduck.nodes.model.efficientdet_d04.efficientdet_files.detector import (
    Detector,
)


class EfficientDetModel(ThresholdCheckerMixin, WeightsDownloaderMixin):
    """EfficientDet model with model types: D0-D4"""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.check_valid_choice("model_type", {0, 1, 2, 3, 4})
        self.check_bounds("score_threshold", "[0, 1]")

        model_dir = self.download_weights()
        classes_path = model_dir / self.weights["classes_file"]
        class_names = {
            val["id"] - 1: val["name"]
            for val in json.loads(classes_path.read_text()).values()
        }
        self.detect_ids = config["detect"]  # change "detect_ids" to "detect"
        self.detector = Detector(
            model_dir,
            class_names,
            self.detect_ids,
            self.config["model_type"],
            self.config["num_classes"],
            self.weights["model_file"],
            self.config["model_nodes"],
            self.config["image_size"],
            self.config["score_threshold"],
            self.config["use_jit"],
        )

    @property
    def detect_ids(self) -> List[int]:
        """The list of selected object category IDs."""
        return self._detect_ids

    @detect_ids.setter
    def detect_ids(self, ids: List[int]) -> None:
        if not isinstance(ids, list):
            raise TypeError("detect_ids has to be a list")
        if not ids:
            self.logger.info("Detecting all EfficientDet classes")
        self._detect_ids = ids

    def predict(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """predict the bbox from frame

        Args:
            image (np.ndarray): Input image frame.

        Returns:
            bboxes (np.ndarray): Array of bboxes for the detected objects.
            labels (np.ndarray): Array of class labels of the detected objects.
            scores (np.ndarray): Array of confidence scores of the detected objects.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError("image must be a np.ndarray")

        return self.detector.predict_object_bbox_from_image(image)
