# 迭代编号：3
import os
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from custom_face_data import CustomFace, deserialize_face
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def plot_embeddings(embeddings, labels=None, visualize_method='pca_3d', size=50, alpha=0.5):
    """
    可视化嵌入空间中的点。
    参数:
        embeddings: array, 嵌入向量数组。
        labels: array, 点的标签。
        visualize_method: str, 可视化方法选择（'pca_2d', 't-sne_2d', 'pca_3d'）。
        core_sample_indices: array, 核心样本的索引。
        size: int, 样本点的基础大小。
    """
    point_size = np.ones(len(embeddings)) * size  # 设置所有点的大小
    unique_labels = np.unique(labels)
    color_map = {label: color for label, color in zip(unique_labels, ['darkorange', 'blue', 'forestgreen', 'firebrick', 'darkcyan', 'gold', 'purple', 'yellow', 'pink', 'cyan'][:len(unique_labels)])}
    colors = [color_map[label] for label in labels]

    if visualize_method == 'pca_2d':
        pca = PCA(n_components=2)
        embeddings_pca = pca.fit_transform(embeddings)
        plt.figure(figsize=(8, 6))
        if labels is not None:
            scatter = plt.scatter(embeddings_pca[:, 0], embeddings_pca[:, 1], c=colors, s=point_size, alpha=alpha)
        else:
            scatter = plt.scatter(embeddings_pca[:, 0], embeddings_pca[:, 1], s=point_size, alpha=alpha)
        plt.title('PCA Results')
        # plt.colorbar(scatter, ticks=unique_labels)
        plt.show()
    elif visualize_method == 't-sne_2d':
        tsne = TSNE(n_components=2, perplexity=30, learning_rate=200)
        embeddings_tsne = tsne.fit_transform(embeddings)
        plt.figure(figsize=(8, 6))
        if labels is not None:
            scatter = plt.scatter(embeddings_tsne[:, 0], embeddings_tsne[:, 1], c=colors, s=point_size, alpha=alpha)
        else:
            scatter = plt.scatter(embeddings_tsne[:, 0], embeddings_tsne[:, 1], s=point_size, alpha=alpha)
        plt.title('t-SNE Results')
        # plt.colorbar(scatter, ticks=unique_labels)
        plt.show()
    elif visualize_method == 'pca_3d':
        pca = PCA(n_components=3)
        embeddings_reduced = pca.fit_transform(embeddings)
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        if labels is not None:
            scatter = ax.scatter(embeddings_reduced[:, 0], embeddings_reduced[:, 1], embeddings_reduced[:, 2], c=colors, s=point_size, alpha=alpha)
        else:
            scatter = ax.scatter(embeddings_reduced[:, 0], embeddings_reduced[:, 1], embeddings_reduced[:, 2], color='blue', s=point_size, alpha=alpha)
        # plt.colorbar(scatter, ticks=unique_labels)
        plt.show()