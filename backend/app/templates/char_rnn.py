"""Character-level RNN notebook section template (TensorFlow 2 / Keras)."""

from __future__ import annotations

from typing import Any

from ..catalog import DATASETS
from .common import section
from .image_common import export_section

TEXT_URL = (
    "https://raw.githubusercontent.com/karpathy/char-rnn/"
    "master/data/tinyshakespeare/input.txt"
)


def build_sections(dataset_key: str, *, batch_size: int, epochs: int) -> list[dict[str, Any]]:
    dataset = DATASETS[dataset_key]

    setup = section(
        "setup",
        "1. Environment Setup",
        f"""
        Import TensorFlow 2 / Keras and configure the character-level language
        model. Everything needed for text training ships with Colab; no extra
        dependencies are required.

        **Dataset:** {dataset["label"]} ({dataset["samples"]}, {dataset["license"]["name"]})
        """,
        [
            """
            %matplotlib inline
            import math
            import os
            import random

            import matplotlib.pyplot as plt
            import numpy as np
            import tensorflow as tf

            SEED = 42
            BATCH_SIZE = __BATCH_SIZE__
            EPOCHS = __EPOCHS__
            SEQ_LENGTH = 100
            EMBEDDING_DIM = 128
            RNN_UNITS = 256
            AUTOTUNE = tf.data.AUTOTUNE

            random.seed(SEED)
            np.random.seed(SEED)
            tf.random.set_seed(SEED)

            print("TensorFlow:", tf.__version__)
            print("GPU devices:", tf.config.list_physical_devices("GPU"))
            """.replace("__BATCH_SIZE__", str(batch_size)).replace("__EPOCHS__", str(epochs)),
        ],
        icon="terminal",
    )

    data = section(
        "data",
        "2. Data Loading",
        f"""
        Download the {dataset["label"]} corpus with
        `tf.keras.utils.get_file`, build a character vocabulary, and pack the
        stream into `(input, next-character)` sequences of length
        **{100}**.
        """,
        [
            f"""
            data_path = tf.keras.utils.get_file("tinyshakespeare.txt", "{TEXT_URL}")
            with open(data_path, "r", encoding="utf-8") as handle:
                text = handle.read()

            vocab = sorted(set(text))
            vocab_size = len(vocab)
            char2idx = {{character: index for index, character in enumerate(vocab)}}
            idx2char = np.array(vocab)
            text_as_int = np.array([char2idx[character] for character in text])

            print("corpus characters:", len(text))
            print("vocabulary size:", vocab_size)
            print(text[:300])

            char_dataset = tf.data.Dataset.from_tensor_slices(text_as_int)
            sequences = char_dataset.batch(SEQ_LENGTH + 1, drop_remainder=True)


            def split_input_target(chunk):
                return chunk[:-1], chunk[1:]


            dataset = (
                sequences.map(split_input_target)
                .shuffle(10000, seed=SEED)
                .batch(BATCH_SIZE, drop_remainder=True)
                .prefetch(AUTOTUNE)
            )

            example_input, example_target = next(iter(dataset))
            print("input batch:", example_input.shape, "target batch:", example_target.shape)
            print("batches per epoch:", len(dataset))
            """,
        ],
        icon="database",
    )

    architecture = section(
        "architecture",
        "3. Model Architecture",
        """
        Embedding → stateful GRU → vocabulary logits. Keeping the GRU stateful
        lets the model carry context across batches; the state is reset between
        epochs and before generation.
        """,
        [
            """
            def build_model(vocab_size, embedding_dim, rnn_units, batch_size):
                inputs = tf.keras.Input(batch_shape=(batch_size, None), dtype=tf.int32)
                x = tf.keras.layers.Embedding(vocab_size, embedding_dim)(inputs)
                x = tf.keras.layers.GRU(
                    rnn_units,
                    return_sequences=True,
                    stateful=True,
                    recurrent_initializer="glorot_uniform",
                )(x)
                outputs = tf.keras.layers.Dense(vocab_size)(x)
                return tf.keras.Model(inputs, outputs)


            model = build_model(vocab_size, EMBEDDING_DIM, RNN_UNITS, batch_size=BATCH_SIZE)


            def reset_model_states(model):
                for layer in model.layers:
                    if hasattr(layer, "reset_states"):
                        layer.reset_states()


            model.summary()
            """,
        ],
        llm_editable=True,
        icon="box",
    )

    training = section(
        "training",
        "4. Training Loop",
        """
        Sparse categorical cross-entropy over the next character. The callback
        resets the stateful GRU at every epoch boundary so each epoch sees
        independent windows.
        """,
        [
            """
            class ResetStatesCallback(tf.keras.callbacks.Callback):
                def on_epoch_end(self, epoch, logs=None):
                    reset_model_states(self.model)


            model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=3e-3),
                loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
            )

            history = model.fit(
                dataset,
                epochs=EPOCHS,
                callbacks=[ResetStatesCallback()],
            )

            plt.figure(figsize=(8, 4))
            plt.plot(history.history["loss"])
            plt.title("char-RNN training loss")
            plt.xlabel("epoch")
            plt.ylabel("cross-entropy")
            plt.grid(alpha=0.2)
            plt.show()
            """,
        ],
        llm_editable=True,
        icon="activity",
    )

    inference = section(
        "inference",
        "5. Inference & Evaluation",
        """
        Rebuild a batch-size-1 inference model with the trained weights, then
        sample characters from the output distribution. Lower temperatures are
        safer; higher temperatures are more creative.
        """,
        [
            """
            def generate_text(model, start_string, num_generate=400, temperature=0.8):
                input_eval = [char2idx[character] for character in start_string]
                input_eval = tf.expand_dims(input_eval, 0)
                text_generated = []
                reset_model_states(model)

                for _ in range(num_generate):
                    logits = model(input_eval)[:, -1, :]
                    next_id = tf.random.categorical(
                        logits / temperature, num_samples=1
                    )[0, 0].numpy()
                    input_eval = tf.expand_dims([next_id], 0)
                    text_generated.append(idx2char[next_id])

                return start_string + "".join(text_generated)


            inference_model = build_model(vocab_size, EMBEDDING_DIM, RNN_UNITS, batch_size=1)
            inference_model.set_weights(model.get_weights())

            generated_text = generate_text(
                inference_model, "ROMEO: ", num_generate=500, temperature=0.8
            )
            print("=" * 70)
            print(generated_text)

            print("=" * 70)
            print(generate_text(inference_model, "To be, or not to be: ", 300, 0.6))

            reset_model_states(model)
            test_loss = model.evaluate(dataset.take(8), verbose=0)
            print("held-out cross-entropy:", round(float(test_loss), 4))
            print("perplexity:", round(math.exp(float(test_loss)), 2))
            """,
        ],
        llm_editable=True,
        icon="wand",
    )

    export = export_section(
        dataset_key,
        "char_rnn",
        """
        model.save_weights("/content/outputs/char_rnn.weights.h5")
        inference_model.save_weights("/content/outputs/char_rnn_inference.weights.h5")
        with open("/content/outputs/generated_text.txt", "w", encoding="utf-8") as handle:
            handle.write(generated_text + "\\n")
        """,
        section_number=6,
    )

    return [setup, data, architecture, training, inference, export]
