import numpy as np
import pandas as pd
import logging
import time
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, accuracy_score
from lightgbm import LGBMClassifier
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv, global_mean_pool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from linkedpaper_app.models import Paper, NodeFeat, Citation

# 数据库连接配置
DATABASE_URI = 'mysql+pymysql://root:123456@localhost/selected_papers'  # 替换为你的数据库 URI
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 计时器启动
start_time = time.time()


# 数据加载模块
def load_data():
    logging.info("开始加载数据...")
    papers = session.query(Paper).all()
    papers_df = pd.DataFrame([{
        'id': paper.id,
        'title': paper.title,
        'abstract': paper.abstract,
        'category': paper.category,
        'year': paper.year
    } for paper in papers])

    node_feats = session.query(NodeFeat).all()
    features = pd.DataFrame([{
        'id': feat.id,
        **{f'feature_{i}': getattr(feat, f'feature_{i}') for i in range(1, 129)}
    } for feat in node_feats])

    citations = session.query(Citation).all()
    citation_df = pd.DataFrame([{
        'citing_paper_id': cite.citing_paper_id,
        'cited_paper_id': cite.cited_paper_id
    } for cite in citations])

    logging.info("数据加载完成，总用时: {:.2f} 分钟".format((time.time() - start_time) / 60))
    return papers_df, features, citation_df


# 数据预处理模块
def preprocess_data(papers_df, features):
    logging.info("开始数据预处理...")
    data = papers_df.merge(features, on='id')
    train_data = data[data['year'] <= 2017]
    val_data = data[data['year'] == 2018]
    test_data = data[data['year'] >= 2019]
    logging.info(f"训练集大小: {len(train_data)}, 验证集大小: {len(val_data)}, 测试集大小: {len(test_data)}")
    logging.info("数据预处理完成，总用时: {:.2f} 分钟".format((time.time() - start_time) / 60))
    return train_data, val_data, test_data


# 图神经网络模块
class GNNModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(GNNModel, self).__init__()
        self.conv1 = SAGEConv(input_dim, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x, edge_index, batch=None):
        x = self.conv1(x, edge_index).relu()
        x = self.conv2(x, edge_index).relu()

        # 如果是节点分类任务，不使用 global_mean_pool
        if batch is not None:
            x = global_mean_pool(x, batch)
        return self.fc(x)


# 图构建模块
def build_graph(papers_df, features, citation_df):
    logging.info("构建图数据...")

    data = papers_df.merge(features, on='id')
    feature_matrix = data[[f'feature_{i}' for i in range(1, 129)]].values
    labels = LabelEncoder().fit_transform(data['category'])

    # 构造边索引
    edge_index = citation_df[['citing_paper_id', 'cited_paper_id']].values.T

    # 确保所有边的索引都在有效范围内
    max_node_id = len(data)  # 节点的数量是数据的行数
    edge_index = edge_index[:, (edge_index[0] < max_node_id) & (edge_index[1] < max_node_id)]

    # 创建图数据
    graph = Data(
        x=torch.tensor(feature_matrix, dtype=torch.float),
        edge_index=torch.tensor(edge_index, dtype=torch.long),
        y=torch.tensor(labels, dtype=torch.long)
    )

    logging.info("图数据构建完成")
    return graph, data

def train_gnn(graph, output_dim=40):
    logging.info("开始训练 GNN...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = GNNModel(input_dim=128, hidden_dim=64, output_dim=output_dim).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss()

    graph = graph.to(device)

    # 修复标签
    graph.y = graph.y - 1  # 如果标签从1开始，则减去1
    graph.y = torch.clamp(graph.y, min=0)  # 确保标签不为负数

    # 确保标签最大值不超过output_dim-1
    graph.y = torch.clamp(graph.y, max=output_dim - 1)  # 确保标签不超过最大类别数 - 1

    graph.y = graph.y.long()  # 确保标签是long类型

    for epoch in range(50):
        model.train()
        optimizer.zero_grad()
        out = model(graph.x, graph.edge_index, batch=None)

        # 确保输出与标签大小一致
        assert out.size(0) == graph.y.size(0), f"Output size {out.size(0)} does not match target size {graph.y.size(0)}"

        loss = criterion(out, graph.y)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 10 == 0:
            logging.info(f"Epoch {epoch + 1}, Loss: {loss.item():.4f}")

    # 提取嵌入特征
    model.eval()
    with torch.no_grad():
        embeddings = model(graph.x, graph.edge_index, batch=None)
    logging.info("GNN 嵌入提取完成")
    return embeddings.cpu().numpy()


# 集成模型训练模块
def train_with_ensemble(train_data, val_data, gnn_embeddings):
    logging.info("开始训练集成模型...")
    X_train = np.hstack([
        train_data[[f'feature_{i}' for i in range(1, 129)]].values,
        gnn_embeddings[train_data.index]
    ])
    y_train = train_data['category'].values

    X_val = np.hstack([
        val_data[[f'feature_{i}' for i in range(1, 129)]].values,
        gnn_embeddings[val_data.index]
    ])
    y_val = val_data['category'].values

    smote = SMOTE(random_state=42)
    X_train, y_train = smote.fit_resample(X_train, y_train)

    lgbm = LGBMClassifier(n_estimators=1000, learning_rate=0.03, random_state=42)
    stack_clf = StackingClassifier(
        estimators=[('lgbm', lgbm)],
        final_estimator=LogisticRegression(),
        cv=3
    )
    stack_clf.fit(X_train, y_train)
    y_pred = stack_clf.predict(X_val)
    accuracy = accuracy_score(y_val, y_pred)
    logging.info("验证集准确率: {:.4f}".format(accuracy))
    logging.info("分类报告:\n" + classification_report(y_val, y_pred))
    return stack_clf


# 测试集预测模块
def predict_test(model, test_data, gnn_embeddings):
    logging.info("开始预测测试集...")

    # 将 GNN 嵌入特征与原始特征拼接
    X_test = np.hstack([
        test_data[[f'feature_{i}' for i in range(1, 129)]].values,
        gnn_embeddings[test_data.index]
    ])

    # 预测测试集类别
    test_data['predicted_category'] = model.predict(X_test)

    logging.info("测试集预测完成，总用时: {:.2f} 分钟".format((time.time() - start_time) / 60))
    return test_data[['id', 'predicted_category']]


# 主函数
def main():
    logging.info("程序启动...")
    papers_df, features, citation_df = load_data()
    train_data, val_data, test_data = preprocess_data(papers_df, features)
    graph, data = build_graph(papers_df, features, citation_df)

    # 训练 GNN 模型
    gnn_embeddings = train_gnn(graph)

    # 训练集成模型
    model = train_with_ensemble(train_data, val_data, gnn_embeddings)

    # 测试集预测
    predictions = predict_test(model, test_data, gnn_embeddings)
    logging.info("分类任务完成，总用时: {:.2f} 分钟".format((time.time() - start_time) / 60))
    print("样例测试集预测结果:\n", predictions.head())


if __name__ == "__main__":
    main()
