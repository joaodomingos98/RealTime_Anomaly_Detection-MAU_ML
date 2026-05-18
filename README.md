# Real-Time Human Activity Recognition and Anomaly Detection
A real-time Human Activity Recognition (HAR) and anomaly detection system using hybrid Deep Learning architectures (CNN, RNN, &amp; Vision Transformers) to identify falls and injuries in live video streams.

## Hypothesis:
H0: Accuracy doesn't carry a negative correlation with computational efficiency

H1: Accuracy carries a negative correlation with computational efficiency

## Architectures Experiments

Vision Transformer - Wilmer

CNN + LSTM - Marteinn

3D-CNN - Jivan

 ## Hyperparameters & Measurable Metrics
 
    - SEED (=0)
    - TEST_SPLIT (0.2)
    - VAL_SPLIT (0.2)
    - BATCH_SIZE
    - NR_EPOCHS
    - LEARNING_RATE
    - CLIP_LEN
    - MODEL
 

## Topic and Motivation

Human Activity Recognition (HAR) has seen significant progress in recent years, aiming to automate activity recognition from sensory inputs such as cameras or sensors [1]. Recent work has extended HAR toward anomaly detection using deep learning models, demonstrating strong performance on benchmark datasets [2]. 

However, the suitability of different model architectures for real-time activity recognition and anomaly detection under low-latency constraints remains unclear. This makes it difficult to determine which approaches are most appropriate for practical deployment in continuous video settings. This research is critical, as real-time processing substantially increases both the technical complexity and practical applicability of such systems.

The problem is highly relevant due to the widespread availability of surveillance cameras across many domains. Reliable real-time anomaly detection could enable impactful applications such as:
* Fall detection in healthcare
* Emergency evacuation monitoring
* Safety analysis on construction sites [1]

Despite these opportunities, existing approaches often struggle to generalize across environments and maintain high accuracy under real-world variability.

---

## Goals

**Main Goal:** 
* Classify atomic human activities (i.e., walking, standing, sitting, running) from RGB video using computer vision in real-time.

**Subgoals:** 
* Classify anomalies in human activities, such as falls or movements exhibiting injuries. 
* Develop a robust model that remains relevant across diverse real-world conditions.
* Achieve high classification accuracy with low latency, ensuring the system can handle live footage.

---

## Data

### Existing Datasets
We utilize the **KTH Action Recognition Dataset (2004)**, which contains:
* **Classes:** 6 human activities - 'boxing', 'handclapping', 'handwaving', 'jogging', 'running', 'walking' 
* **Subjects & Scenarios:** Performed by 25 subjects across 4 scenarios (outdoors, different angles, different clothing, indoors).
* **Volume:** 600 videos total (100 videos per class).
* **Format:** Recorded at 25fps with a homogeneous background. 
* *Source:* [KTH Action Dataset](https://www.csc.kth.se/cvap/actions/) dowloaded from: [kaggle](https://www.kaggle.com/datasets/vafaeii/kth-action-recognition-dataset/data)

### Data Collection
We will also collect custom data in an indoor controlled environment (Room NI:C0614). We will capture, label, and process RGB videos from a camera installed at this location to augment our training and testing data.

---

## Method

Based on the latest computer vision research [3], we will apply several deep learning architectures and compare their results. For human activity classification, we aim to evaluate and compare:
* **2D-CNN** (TDN [4])
* **3D-CNN** [5]
* **CNN + RNN** (LSTM / GRU)
* **Vision Transformer (ViT)**
* **Hybrid CNN + Vision Transformer** [3]

**Novelty Approach:** 
To aspire for novelty, we will perform anomaly detection using a clustering model applied directly to the class probability outputs of the aforementioned classification models.

---

## Evaluation

### Qualitative Metrics
We expect the model to reliably detect anomalous activities across different environments and camera setups. We will analyze typical success and failure cases to assess overall robustness and generalization capabilities.

### Quantitative Metrics
The architectures will be evaluated against the following metrics:
* F1-score
* Precision and Recall
* Accuracy
* ROC-AUC
* Inference Time (to explicitly evaluate real-time performance)
* Frames Per Second (FPS)
* GFLOPS

---

## References

1. Naik, F., Rahman, H., Shaheen, M., Algarni, A., Almujally, N. A., & Jalal, A. (2024). A review of video-based human activity recognition: theory, methods and applications. *Multimedia Tools and Applications*.
2. Elmetwally, A., Eldeeb, R., & Elmougy, S. (2024). Deep learning based anomaly detection in real-time video. *Multimedia Tools and Applications*.
3. Alomar, K., & Cai, X. (2025). *Human action recognition based on convolutional neural networks and vision transformers* [Ph.D. thesis, University of Southampton].
4. Wang, L., Tong, Z., Ji, B., & Wu, G. (2021). Tdn: Temporal difference networks for efficient action recognition. In *Proceedings of the IEEE/CVF conference on computer vision and pattern recognition* (pp. 1895-1904).
5. Alomar, K., & Cai, X. (2023). TransNet: A transfer learning-based network for human action recognition. In *2023 International Conference on Machine Learning and Applications (ICMLA)* (pp. 1825-1832). IEEE.

### Additional Reading
* Ozel, M. E., Apaydin, N. N., Yaman, O., & Karakose, M. (2025). A CNN-based method using optimized parameters for dynamic human action recognition. In *2025 29th International Conference on Information Technology (IT)* (pp. 1-4). IEEE.
* Alomar, K., Aysel, H. I., & Cai, X. (2025). CNNs, RNNs and Transformers in human action recognition: a survey and a hybrid model. *Artificial Intelligence Review*, 58(12), 1-44.
