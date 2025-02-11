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
Creates a zone from a polygon area
"""

from typing import List, Tuple

from shapely.geometry.polygon import Point, Polygon


class Zone:  # pylint: disable=too-few-public-methods
    """This class uses polygon area to create a zone for counting."""

    def __init__(self, points: List[Tuple[int, int]]) -> None:
        # Each zone is a polygon created by a list of x, y coordinates
        self.polygon_points = points
        self.polygon = Polygon(self.polygon_points).buffer(1)

    def contains(self, point: Point) -> bool:
        """Checks if the specified point is within the area bounded by the
        zone.

        Args:
            point (Point): The x- and y- coordinate to check.

        Returns:
            (bool): True if ``point`` is within the zone.
        """
        return self.polygon.contains(point)
