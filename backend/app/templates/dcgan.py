"""DCGAN notebook section template (TensorFlow 2 / Keras)."""

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
    sections = environment_sections("DCGAN", dataset_key, batch_size, epochs)

    sections.append(
        section(
            "architecture",
            "3. Model Architecture",
            """
            A canonical DCGAN pair: the generator projects a 128-D latent vector
            into a spatial volume and upsamples with strided transposed
            convolutions; the discriminator mirrors it with strided convolutions
            and outputs a single logit. Batch normalisation stabilises both
            networks, and `tanh` output matches the `[-1, 1]` data range.
            """,
            [
                f"""
                def build_generator():
                    start = IMAGE_SIZE // 4
                    model = tf.keras.Sequential(
                        [
                            tf.keras.Input(shape=(LATENT_DIM,)),
                            tf.keras.layers.Dense(start * start * 256, use_bias=False),
                            tf.keras.layers.BatchNormalization(),
                            tf.keras.layers.LeakyReLU(negative_slope=0.2),
                            tf.keras.layers.Reshape((start, start, 256)),
                            tf.keras.layers.Conv2DTranspose(
                                128, (5, 5), strides=(2, 2), padding="same", use_bias=False
                            ),
                            tf.keras.layers.BatchNormalization(),
                            tf.keras.layers.LeakyReLU(negative_slope=0.2),
                            tf.keras.layers.Conv2DTranspose(
                                64, (5, 5), strides=(2, 2), padding="same", use_bias=False
                            ),
                            tf.keras.layers.BatchNormalization(),
                            tf.keras.layers.LeakyReLU(negative_slope=0.2),
                            tf.keras.layers.Conv2DTranspose(
                                CHANNELS,
                                (5, 5),
                                strides=(1, 1),
                                padding="same",
                                activation="tanh",
                            ),
                        ],
                        name="dcgan_generator",
                    )
                    return model


                def build_discriminator():
                    inputs = tf.keras.Input(shape=(IMAGE_SIZE, IMAGE_SIZE, CHANNELS))
                    x = tf.keras.layers.Conv2D(64, (5, 5), strides=(2, 2), padding="same")(inputs)
                    x = tf.keras.layers.LeakyReLU(negative_slope=0.2)(x)
                    x = tf.keras.layers.Dropout(0.3)(x)
                    x = tf.keras.layers.Conv2D(128, (5, 5), strides=(2, 2), padding="same")(x)
                    x = tf.keras.layers.LeakyReLU(negative_slope=0.2)(x)
                    x = tf.keras.layers.Dropout(0.3)(x)
                    x = tf.keras.layers.Flatten()(x)
                    outputs = tf.keras.layers.Dense(1)(x)
                    return tf.keras.Model(inputs, outputs, name="dcgan_discriminator")


                generator = build_generator()
                discriminator = build_discriminator()

                print("Generator parameters:", generator.count_params())
                print("Discriminator parameters:", discriminator.count_params())
                generator.summary()
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
            The discriminator maximises the probability of real images and
            minimises it for generated ones; the generator maximises the
            discriminator's confidence on its fakes. A custom `@tf.function`
            train step keeps the loop fast, and a 4×4 preview is rendered after
            every epoch so progress is visible in Colab.
            """,
            [
                """
                binary_cross_entropy = tf.keras.losses.BinaryCrossentropy(from_logits=True)


                def discriminator_loss(real_output, fake_output):
                    real_loss = binary_cross_entropy(tf.ones_like(real_output), real_output)
                    fake_loss = binary_cross_entropy(tf.zeros_like(fake_output), fake_output)
                    return real_loss + fake_loss


                def generator_loss(fake_output):
                    return binary_cross_entropy(tf.ones_like(fake_output), fake_output)


                generator_optimizer = tf.keras.optimizers.Adam(2e-4, beta_1=0.5)
                discriminator_optimizer = tf.keras.optimizers.Adam(2e-4, beta_1=0.5)


                @tf.function
                def train_step(images):
                    noise = tf.random.normal([tf.shape(images)[0], LATENT_DIM])
                    with tf.GradientTape() as gen_tape, tf.GradientTape() as disc_tape:
                        generated_images = generator(noise, training=True)
                        real_output = discriminator(images, training=True)
                        fake_output = discriminator(generated_images, training=True)
                        gen_loss = generator_loss(fake_output)
                        disc_loss = discriminator_loss(real_output, fake_output)

                    gen_gradients = gen_tape.gradient(gen_loss, generator.trainable_variables)
                    disc_gradients = disc_tape.gradient(disc_loss, discriminator.trainable_variables)
                    generator_optimizer.apply_gradients(
                        zip(gen_gradients, generator.trainable_variables)
                    )
                    discriminator_optimizer.apply_gradients(
                        zip(disc_gradients, discriminator.trainable_variables)
                    )
                    return gen_loss, disc_loss


                generator_losses = []
                discriminator_losses = []

                for epoch in range(1, EPOCHS + 1):
                    epoch_generator, epoch_discriminator = [], []
                    for image_batch in train_ds:
                        g_loss, d_loss = train_step(image_batch)
                        epoch_generator.append(float(g_loss))
                        epoch_discriminator.append(float(d_loss))

                    generator_losses.append(float(np.mean(epoch_generator)))
                    discriminator_losses.append(float(np.mean(epoch_discriminator)))

                    preview = generator(tf.random.normal([16, LATENT_DIM]), training=False)
                    show_images(preview, title="Epoch %d/%d" % (epoch, EPOCHS), n=16)
                    print(
                        "Epoch %d/%d  generator=%.3f  discriminator=%.3f"
                        % (
                            epoch,
                            EPOCHS,
                            generator_losses[-1],
                            discriminator_losses[-1],
                        )
                    )

                plt.figure(figsize=(8, 4))
                plt.plot(generator_losses, label="generator")
                plt.plot(discriminator_losses, label="discriminator")
                plt.title("DCGAN training losses")
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
            Sample the latent space and export one image for the BLIP sanity
            check. Early training produces noisy textures; after 20–50 epochs
            on {dataset["label"]} the samples should start reading as
            {meta["display"]}.
            """,
            [
                """
                def generate_images(n=16, seed=None):
                    if seed is not None:
                        tf.random.set_seed(seed)
                    noise = tf.random.normal([n, LATENT_DIM])
                    return generator(noise, training=False)


                samples = generate_images(n=16, seed=2024)
                show_images(samples, title="DCGAN generated samples", n=16)

                sample_array = to_display(samples[:1])[0]
                if sample_array.ndim == 2:
                    sample_array = np.stack([sample_array] * 3, axis=-1)

                IMAGE_FOR_CAPTION_PATH = "/content/dcgan_sample.png"
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
            "dcgan",
            """
            generator.save("/content/outputs/dcgan_generator.keras")
            discriminator.save("/content/outputs/dcgan_discriminator.keras")
            """,
        )
    )
    return sections
