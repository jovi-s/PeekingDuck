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

""" Test data module, data adapter, data loader and dataset
"""

from typing import Any, List, Tuple
from pytest import mark

from hydra import compose, initialize
import tensorflow as tf
import tensorflow_datasets as tfds

from src.training_pipeline import init_trainer
from src.model.tensorflow_model import TFClassificationModelFactory
from src.losses.adapter import LossAdapter
from src.metrics.tensorflow_metrics import TensorflowMetrics

# from src.callbacks.tensorflow_callbacks import TensorFlowCallbacksAdapter


@mark.parametrize(
    "overrides, validation_loss_key, expected",
    [
        (
            [
                "project_name=cifar10",
                "data_module=cifar10",
                "framework=tensorflow",
                "debug=True",
                "device=cpu",
                "data_module.dataset.download=False",
                "data_module.dataset.image_size=224",
                "data_module.dataset.num_classes=1",
                "data_module.data_adapter.tensorflow.train.batch_size=128",
                "data_module.data_adapter.tensorflow.validation.batch_size=128",
                "data_module.data_adapter.tensorflow.test.batch_size=128",
                "model.tensorflow.activation=null",
                "model.tensorflow.model_name=ResNet50",
                "model.tensorflow.fine_tune=False",
                "trainer.tensorflow.loss_params.loss_func=SparseCategoricalCrossentropy",
                "trainer.tensorflow.loss_params.loss_params.from_logits=True",
            ],
            "categorical_accuracy",
            0.5,
        ),
    ],
)
def test_tensorflow_model(
    overrides: List[str], validation_loss_key: str, expected: float
) -> None:
    """Test data_module"""
    with initialize(version_base=None, config_path="../../configs"):
        cfg = compose(
            config_name="config",
            overrides=overrides,
        )

        # """Test Tensorflow datasource"""
        # Step 1: Create your input pipeline
        # ### Load a dataset
        (ds_train, ds_test), ds_info = tfds.load(
            "mnist",
            split=["train[:400]", "test[:40]"],
            shuffle_files=True,
            as_supervised=True,
            with_info=True,
        )

        # ### Build a training pipeline
        def normalize_img(image: tf.Tensor, label: tf.Tensor) -> Tuple[Any, Any]:
            """Normalizes images: `uint8` -> `float32`."""
            image = tf.cast(image, tf.float32)
            image = image * 1 / 255.0
            image = tf.image.resize(image, (224, 224))
            image = tf.image.grayscale_to_rgb(image)
            return image, label

        ds_train = ds_train.map(normalize_img, num_parallel_calls=tf.data.AUTOTUNE)
        ds_train = ds_train.cache()
        ds_train = ds_train.shuffle(ds_info.splits["train"].num_examples)
        ds_train = ds_train.batch(128)
        ds_train = ds_train.prefetch(tf.data.AUTOTUNE)

        # ### Build an evaluation pipeline
        ds_test = ds_test.map(normalize_img, num_parallel_calls=tf.data.AUTOTUNE)
        ds_test = ds_test.batch(128)
        ds_test = ds_test.cache()
        ds_test = ds_test.prefetch(tf.data.AUTOTUNE)

        model_config = cfg.model[cfg.framework]
        metrics_config = cfg.metrics[cfg.framework]
        # callbacks_config = cfg.callbacks[cfg.framework]
        trainer_config = cfg.trainer[cfg.framework]
        # data_config = cfg.data_module
        train_params = trainer_config.global_train_params
        epochs = train_params.epochs

        # Set Seed
        tf.random.set_seed(train_params.manual_seed)

        # create model
        model = TFClassificationModelFactory.create_model(model_config)
        # init_optimizer
        # opt = OptimizersAdapter.get_tensorflow_optimizer(
        #     trainer_config.optimizer_params.optimizer,
        #     scheduler,
        #     trainer_config.optimizer_params.optimizer_params,
        # )

        # loss
        loss = LossAdapter.get_tensorflow_loss_func(
            trainer_config.loss_params.loss_func,
            trainer_config.loss_params.loss_params,
        )

        # metric
        metrics = TensorflowMetrics().get_metrics(metrics=metrics_config)

        # compile model
        model.compile(
            optimizer=tf.keras.optimizers.Adam(0.001), loss=loss, metrics=metrics
        )

        history = model.fit(
            ds_train,
            epochs=epochs,
            validation_data=ds_test,
            verbose="0",
        )

        # dataset = ds_train.take(5)
        # print(list(dataset.as_numpy_iterator()))

        assert history is not None
        assert hasattr(history, "history")
        assert validation_loss_key in history.history
        assert len(history.history[validation_loss_key]) != 0
        assert history.history[validation_loss_key][-1] >= expected


@mark.skip(reason="debug tensorflow test")
@mark.parametrize(
    "overrides, validation_loss_key, expected",
    [
        (
            [
                "project_name=cifar10",
                "data_module=cifar10",
                "framework=tensorflow",
                "debug=True",
                "device=cpu",
                "data_module.dataset.download=False",
                "data_module.dataset.image_size=224",
                "data_module.dataset.num_classes=1",
                "data_module.data_adapter.tensorflow.train.batch_size=128",
                "data_module.data_adapter.tensorflow.validation.batch_size=128",
                "data_module.data_adapter.tensorflow.test.batch_size=128",
                "model.tensorflow.activation=null",
                "model.tensorflow.model_name=ResNet50",
                "model.tensorflow.fine_tune=False",
                "trainer.tensorflow.loss_params.loss_func=SparseCategoricalCrossentropy",
                "trainer.tensorflow.loss_params.loss_params.from_logits=True",
            ],
            "val_loss",
            3.0,
        ),
    ],
)
def test_tensorflow_trainer(
    overrides: List[str], validation_loss_key: str, expected: float
) -> None:
    """Test data_module"""
    with initialize(version_base=None, config_path="../../configs"):
        cfg = compose(
            config_name="config",
            overrides=overrides,
        )

        # """Test Tensorflow datasource"""
        # Step 1: Create your input pipeline
        # ### Load a dataset
        (ds_train, ds_test), ds_info = tfds.load(
            "mnist",
            split=["train[:400]", "test[:40]"],
            shuffle_files=True,
            as_supervised=True,
            with_info=True,
        )

        # ### Build a training pipeline
        def normalize_img(image: tf.Tensor, label: tf.Tensor) -> Tuple[Any, Any]:
            """Normalizes images: `uint8` -> `float32`."""
            image = tf.cast(image, tf.float32)
            image = image * 1 / 255.0
            image = tf.image.resize(image, (224, 224))
            image = tf.image.grayscale_to_rgb(image)
            return image, label

        ds_train = ds_train.map(normalize_img, num_parallel_calls=tf.data.AUTOTUNE)
        ds_train = ds_train.cache()
        ds_train = ds_train.shuffle(ds_info.splits["train"].num_examples)
        ds_train = ds_train.batch(128)
        ds_train = ds_train.prefetch(tf.data.AUTOTUNE)

        # ### Build an evaluation pipeline
        ds_test = ds_test.map(normalize_img, num_parallel_calls=tf.data.AUTOTUNE)
        ds_test = ds_test.batch(128)
        ds_test = ds_test.cache()
        ds_test = ds_test.prefetch(tf.data.AUTOTUNE)

        trainer = init_trainer(cfg)
        history = trainer.train(ds_train, ds_test)

        assert history is not None
        assert validation_loss_key in history
        assert len(history[validation_loss_key]) != 0
        assert history[validation_loss_key][-1] < expected
