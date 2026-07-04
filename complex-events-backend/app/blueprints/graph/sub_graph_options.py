import os
import time

import numpy as np
from flask import request, current_app
from scipy.sparse import csgraph, csr_matrix
from scipy.sparse.linalg import eigsh  # 用于稀疏对称矩阵的特征分解
from sklearn.decomposition import PCA
from app.models import Result
from app.services.database_service import get_sub_graph_collection
from . import graph_bp

from scipy.sparse import csgraph, diags


def laplacian_embedding(adj_matrix, k=5, normalized=True):
    """
    基于图拉普拉斯的节点或图级嵌入（增强版，处理孤立节点）

    Parameters:
    -----------
    adj_matrix : scipy.sparse matrix
        邻接矩阵（建议为 csr_matrix）
    k : int
        嵌入维度（取前 k 个非零特征向量）
    normalized : bool
        是否使用归一化拉普拉斯
    """
    n = adj_matrix.shape[0]

    # 限制 k 值不超过 n-1
    if k >= n:
        k = max(1, n - 1)

    # 检查孤立节点
    degrees = np.array(adj_matrix.sum(axis=1)).flatten()
    isolated_nodes = np.where(degrees == 0)[0]

    # 初始化 embeddings
    embeddings = np.zeros((n, k))

    try:
        if len(isolated_nodes) > 0:
            # 有孤立节点：加正则化
            lap = csgraph.laplacian(adj_matrix, normed=normalized)
            eps = 1e-10
            regularized_lap = lap + diags([eps], [0], shape=lap.shape)

            if n <= 10:
                evals, evecs = np.linalg.eigh(regularized_lap.toarray())
                embeddings = evecs[:, 1:k + 1] if k < n else evecs[:, 1:]
            else:
                evals, evecs = eigsh(regularized_lap, k=k + 1, which='SM')
                embeddings = evecs[:, 1:k + 1]
        else:
            # 无孤立节点
            lap = csgraph.laplacian(adj_matrix, normed=normalized)
            if n <= 10:
                evals, evecs = np.linalg.eigh(lap.toarray())
                embeddings = evecs[:, 1:k + 1] if k < n else evecs[:, 1:]
            else:
                evals, evecs = eigsh(lap, k=k + 1, which='SM')
                embeddings = evecs[:, 1:k + 1]

        # 补齐维度（当 k 实际可用维度不足时）
        if embeddings.shape[1] < k:
            pad = np.zeros((n, k - embeddings.shape[1]))
            embeddings = np.hstack([embeddings, pad])

        # 归一化（按行）
        if normalized and embeddings.size > 0:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1
            embeddings = embeddings / norms

    except Exception as e:
        # 降级：全零嵌入
        embeddings = np.zeros((n, k))

    return embeddings


@graph_bp.route('/save', methods=['POST'])
def save_graph_data():
    # 解析请求json
    data = request.get_json()
    name = data.get('name')
    # [{id:node_id1,group:node_type1，...},{id:node_id2,group:node_type2},...]
    node_data = data.get('nodes')
    # [{from_node_id1,to_node_id1},...]
    edge_data = data.get('edges')
    if not node_data or not edge_data:
        return Result.fail(message='数据格式错误')

    # 创建节点ID到索引的映射
    node_to_index = {node['id']: idx for idx, node in enumerate(node_data)}
    n_nodes = len(node_data)

    # 构建稀疏矩阵的行列索引和数据
    row_indices = []
    col_indices = []
    values = []

    for edge in edge_data:
        from_node = edge.get('from')
        to_node = edge.get('to')

        if from_node in node_to_index and to_node in node_to_index:
            row_indices.append(node_to_index[from_node])
            col_indices.append(node_to_index[to_node])
            values.append(1)  # 可根据需要设置权重值

    # 创建稀疏矩阵
    sparse_matrix = csr_matrix((values, (row_indices, col_indices)),
                               shape=(n_nodes, n_nodes))
    embeddings = laplacian_embedding(sparse_matrix)
    graph_embedding = np.mean(embeddings, axis=0)
    embeddings_list = embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings
    # 生成一个独一无二的文件名

    file_name = f'graph_data_node{len(node_data)}_edge{len(edge_data)}_time{int(time.time())}.npz'
    file_path = os.path.join(current_app.config.get('SUB_GRAPH_PATH'), file_name)
    # 保存为NPZ格式
    np.savez_compressed(file_path,
                        adjacency_matrix=sparse_matrix.data,
                        indices=sparse_matrix.indices,
                        indptr=sparse_matrix.indptr,
                        shape=sparse_matrix.shape,
                        embeddings=embeddings_list,
                        graph_embedding=graph_embedding,
                        nodes_data=np.array(node_data))

    get_sub_graph_collection().insert_one(
        {
            'name': name if name else file_name,
            'save_name': file_name,
        }
    )

    return Result.success(message='图数据保存成功')


@graph_bp.route('/list', methods=['GET'])
def list_sub_graphs():
    # 返回所有名称
    sub_graph_docs = get_sub_graph_collection().find()
    result = []
    for doc in sub_graph_docs:
        result.append(doc.get('name'))
    return Result.success(message='获取成功', data=result)


def load_sub_graph_file(save_name):
    # 读取保存的数据
    loaded_data = np.load(os.path.join(current_app.config.get('SUB_GRAPH_PATH'), save_name),
                          allow_pickle=True)
    return loaded_data


@graph_bp.route('/load', methods=['GET'])
def get_sub_graph():
    #  要读取的名称
    name = request.args.get('name')
    if name is None:
        return Result.fail(message='请选择要读取的图数据')

    all_sub_graphs = get_sub_graph_collection().find()
    sub_graph_save_name = ''
    all_sub_graph_embedding = []
    for doc in all_sub_graphs:
        all_sub_graph_embedding.append(
            {
                'name': doc.get('name'),
                'embeddings': load_sub_graph_file(
                    doc.get('save_name')
                ).get('graph_embedding').tolist()
            }
        )
        if doc.get('name') == name:
            sub_graph_save_name = doc.get('save_name')
    # 在你的循环代码之后添加
    if len(all_sub_graph_embedding) > 1:
        # 提取所有图嵌入向量
        graph_embeddings = [item['embeddings'] for item in all_sub_graph_embedding]

        # PCA降维到2维
        pca = PCA(n_components=2)
        reduced_embeddings = pca.fit_transform(graph_embeddings)

        # 将降维结果添加到原数据中
        for i, item in enumerate(all_sub_graph_embedding):
            del item['embeddings']
            item['reduced_embedding'] = reduced_embeddings[i].tolist()

    loaded_data = load_sub_graph_file(sub_graph_save_name)

    sparse_matrix_data = loaded_data['adjacency_matrix']
    indices = loaded_data['indices']
    indptr = loaded_data['indptr']
    shape = tuple(loaded_data['shape'])
    nodes_data = list(loaded_data['nodes_data'])

    # 重建稀疏矩阵
    reconstructed_matrix = csr_matrix((sparse_matrix_data, indices, indptr), shape=shape)
    # 将稀疏矩阵转换为COO格式便于前端处理
    coo_matrix = reconstructed_matrix.tocoo()
    return Result.success(message='获取成功', data={
        'adjacency_matrix': {
            'data': coo_matrix.data.tolist(),
            'row': coo_matrix.row.tolist(),
            'col': coo_matrix.col.tolist(),
            'shape': coo_matrix.shape
        },
        'nodes_data': nodes_data,
        'all_sub_graph_embedding': all_sub_graph_embedding,
    })
