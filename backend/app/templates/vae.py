"""Variational Autoencoder notebook section template (TensorFlow 2 / Keras)."""

from __future__ import annotations

from typing import Any

from ..catalog import DATASETS
from .common import section
from .image_common import (
    blip_section,
    environment_sections,
    export_section,
    image_meta,
)


def build_sections(dataset_key: str, *, batch_size: int, epochs: int) -> list[dict[str, Any]]:
    dataset = DATASETS[dataset_key]
    meta = image_meta(dataset_key)
    sections = environment_sections("VAE", dataset_key, batch_size, epochs)

    sections.append(
        section(
            "architecture",
            "3. Model Architecture",
            """
            The encoder maps an image to `z_mean` and `z_log_var`; the
            reparameterisation trick samples `z` from that Gaussian. The decoder
            projects `z` back to image space. The KL term is added as a model
            loss, so `model.fit` optimises reconstruction + KL together.
            """,
            [
                """
                class Sampling(tf.keras.layers.Layer):
                    def call(self, inputs):
                        z_mean, z_log_var = inputs
                        epsilon = tf.random.normal(shape=tf.shape(z_mean))
                        return z_mean + tf.exp(0.5 * z_log_var) * epsilon


                class VAE(tf.keras.Model):
                    def __init__(self, **kwargs):
                        super().__init__(**kwargs)
                        self.encoder = self._build_encoder()
                        self.decoder = self._build_decoder()

                    def _build_encoder(self):
                        inputs = tf.keras.Input(shape=(IMAGE_SIZE, IMAGE_SIZE, CHANNELS))
                        x = tf.keras.layers.Conv2D(32, 3, strides=2, padding="same")(inputs)
                        x = tf.keras.layers.LeakyReLU(negative_slope=0.2)(x)
                        x = tf.keras.layers.Conv2D(64, 3, strides=2, padding="same")(x)
                        x = tf.keras.layers.LeakyReLU(negative_slope=0.2)(x)
                        x = tf.keras.layers.Conv2D(128, 3, strides=2, padding="same")(x)
                        x = tf.keras.layers.LeakyReLU(negative_slope=0.2)(x)
                        x = tf.keras.layers.Flatten()(x)
                        x = tf.keras.layers.Dense(256, activation="relu")(x)
                        z_mean = tf.keras.layers.Dense(LATENT_DIM, name="z_mean")(x)
                        z_log_var = tf.keras.layers.Dense(LATENT_DIM, name="z_log_var")(x)
                        z = Sampling()([z_mean, z_log_var])
                        return tf.keras.Model(inputs, [z_mean, z_log_var, z], name="encoder")

                    def _build_decoder(self):
                        start = IMAGE_SIZE // 4
                        latent_inputs = tf.keras.Input(shape=(LATENT_DIM,))
                        x = tf.keras.layers.Dense(start * start * 128, activation="relu")(
                            latent_inputs
                        )
                        x = tf.keras.layers.Reshape((start, start, 128))(x)
                        x = tf.keras.layers.Conv2DTranspose(
                            128, 3, strides=2, padding="same", activation="relu"
                        )(x)
                        x = tf.keras.layers.Conv2DTranspose(
                            64, 3, strides=2, padding="same", activation="relu"
                        )(x)
                        outputs = tf.keras.layers.Conv2D(
                            CHANNELS, 3, padding="same", activation="tanh"
                        )(x)
                        return tf.keras.Model(latent_inputs, outputs, name="decoder")

                    def call(self, inputs, training=None):
                        z_mean, z_log_var, z = self.encoder(inputs, training=training)
                        reconstruction = self.decoder(z, training=training)
                        kl_loss = -0.5 * tf.reduce_mean(
                            tf.reduce_sum(
                                1 + z_log_var - tf.square(z_mean) - tf.exp(z_log_var),
                                axis=1,
                            )
                        )
                        self.add_loss(kl_loss)
                        return reconstruction

                    def generate(self, n=16, seed=None):
                        if seed is not None:
                            tf.random.set_seed(seed)
                        z = tf.random.normal([n, LATENT_DIM])
                        return self.decoder(z, training=False)


                vae = VAE()
                vae.encoder.summary()
                vae.decoder.summary()
                """,
            ],
            llm_editable=True,
            icon="box",
        )
    )

    sections.append(
        section(
            "training",
            "4. Training Loop",
            """
            A mean-squared reconstruction loss plus the model-level KL loss.
            Five epochs on 20k images is enough to see blurry but recognisable
            reconstructions; 30+ epochs sharpens them substantially.
            """,
            [
                """
                vae.compile(
                    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
                    loss=tf.keras.losses.MeanSquaredError(),
                )

                # An autoencoder's target is the input image itself.
                reconstruction_ds = train_ds.map(lambda images: (images, images))

                history = vae.fit(reconstruction_ds, epochs=EPOCHS)

                plt.figure(figsize=(8, 4))
                plt.plot(history.history["loss"], label="total loss")
                plt.title("VAE training loss (reconstruction + KL)")
                plt.xlabel("epoch")
                plt.ylabel("loss")
                plt.legend()
                plt.grid(alpha=0.2)
                plt.show()
                """,
            ],
            llm_editable=True,
            icon="activity",
        )
    )

    sections.append(
        section(
            "inference",
            "5. Inference & Evaluation",
            f"""
            Compare originals with reconstructions, then draw fresh samples from
            the prior. The single exported sample is captioned by BLIP in the
            next section. On {dataset["label"]} the model should learn
            {meta["display"]} structure.
            """,
            [
                """
                sample_batch = next(iter(train_ds))
                originals = sample_batch[:8]
                reconstructions = vae(originals, training=False)

                show_images(originals, title="Originals", n=8)
                show_images(reconstructions, title="Reconstructions", n=8)

                samples = vae.generate(n=16, seed=7)
                show_images(samples, title="Samples from the prior", n=16)

                sample_array = to_display(samples[:1])[0]
                if sample_array.ndim == 2:
                    sample_array = np.stack([sample_array] * 3, axis=-1)

                IMAGE_FOR_CAPTION_PATH = "/content/vae_sample.png"
                Image.fromarray(sample_array).resize((256, 256), Image.NEAREST).save(
                    IMAGE_FOR_CAPTION_PATH
                )
                print("Saved BLIP input to", IMAGE_FOR_CAPTION_PATH)
                """,
            ],
            llm_editable=True,
            icon="wand",
        )
    )

    sections.append(blip_section(dataset_key))
    sections.append(
        export_section(
            dataset_key,
            "vae",
            """
            vae.encoder.save("/content/outputs/vae_encoder.keras")
            vae.decoder.save("/content/outputs/vae_decoder.keras")
            """,
        )
    )
    return sections
