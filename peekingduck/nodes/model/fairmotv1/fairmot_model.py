# Modifications copyright 2022 AI Singapore
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Original copyright (c) 2020 YifuZhang
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""FairMOT model for human detection and tracking."""

import logging
from typing import Any, Dict, List, Tuple

import numpy as np

from peekingduck.nodes.base import ThresholdCheckerMixin, WeightsDownloaderMixin
from peekingduck.nodes.model.fairmotv1.fairmot_files.tracker import Tracker


class FairMOTModel(ThresholdCheckerMixin, WeightsDownloaderMixin):
    """FairMOT Model for person tracking.
    Args:
        config (Dict[str, Any]): Model configuration options.
        frame_rate (float): The frame rate of the current video sequence,
            used for computing the size of track buffer.
    Raises:
        ValueError: `score_threshold` is beyond [0, 1].
        ValueError: `K` is less than 1.
        ValueError: `min_box_area` is less than 1.
        ValueError: `track_buffer` is less than 1.
    """

    def __init__(self, config: Dict[str, Any], frame_rate: float) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.check_bounds(["K", "min_box_area", "track_buffer"], "(0, +inf]")
        self.check_bounds("score_threshold", "[0, 1]")

        model_dir = self.download_weights()
        self.tracker = Tracker(
            model_dir,
            frame_rate,
            self.config["model_type"],
            self.weights["model_file"],
            self.config["input_size"],
            self.config["K"],
            self.config["min_box_area"],
            self.config["track_buffer"],
            self.config["score_threshold"],
        )

    def predict(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        """Track objects from image.

        Args:
            image (np.ndarray): Image in numpy array.

        Returns:
            (Tuple[np.ndarray, np.ndarray, List[int]]): A tuple of
            - Numpy array of detected bounding boxes.
            - List of detection confidence scores.
            - List of track IDs.

        Raises:
            TypeError: The provided `image` is not a numpy array.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError("image must be a np.ndarray")
        bboxes, track_ids, bbox_scores = self.tracker.track_objects_from_image(image)
        return bboxes, bbox_scores, track_ids
