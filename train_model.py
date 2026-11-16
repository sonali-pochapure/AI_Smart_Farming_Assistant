import tensorflow as tf
from tensorflow.keras import layers, models

# ==============================
# DATASET PATH
# ==============================

DATASET_PATH = "dataset/Plant_leave_diseases_dataset_without_augmentation"

IMG_SIZE = (224, 224)
BATCH_SIZE = 32

# ==============================
# LOAD TRAINING DATA
# ==============================

train_dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

# ==============================
# LOAD VALIDATION DATA
# ==============================

validation_dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

# ==============================
# GET CLASS NAMES
# ==============================

class_names = train_dataset.class_names

print("\nClasses:")
print(class_names)

print("\nNumber of classes:", len(class_names))

# ==============================
# IMPROVE DATA PERFORMANCE
# ==============================

AUTOTUNE = tf.data.AUTOTUNE

train_dataset = train_dataset.prefetch(buffer_size=AUTOTUNE)
validation_dataset = validation_dataset.prefetch(buffer_size=AUTOTUNE)

# ==============================
# CREATE CNN MODEL
# ==============================

model = models.Sequential([
    
    layers.Rescaling(1./255, input_shape=(224, 224, 3)),

    layers.Conv2D(32, (3, 3), activation="relu"),
    layers.MaxPooling2D(),

    layers.Conv2D(64, (3, 3), activation="relu"),
    layers.MaxPooling2D(),

    layers.Conv2D(128, (3, 3), activation="relu"),
    layers.MaxPooling2D(),

    layers.Flatten(),

    layers.Dense(128, activation="relu"),
    layers.Dropout(0.5),

    layers.Dense(len(class_names), activation="softmax")
])

# ==============================
# COMPILE MODEL
# ==============================

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

# ==============================
# SHOW MODEL
# ==============================

model.summary()

# ==============================
# TRAIN MODEL
# ==============================

print("\nStarting model training...\n")

history = model.fit(
    train_dataset,
    validation_data=validation_dataset,
    epochs=10
)

# ==============================
# SAVE MODEL
# ==============================

model.save("disease_model.keras")

print("\n================================")
print("MODEL TRAINING COMPLETED!")
print("Model saved as disease_model.keras")
print("================================")