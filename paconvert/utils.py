# Copyright (c) 2022  PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import collections


class UniqueNameGenerator:
    def __init__(self):
        self.ids = collections.defaultdict(int)

    def __call__(self, key):
        counter = self.ids[key]
        self.ids[key] += 1
        return "_".join([key, str(counter)])


Generator = UniqueNameGenerator()


def get_unique_name(key):
    return Generator(key)
