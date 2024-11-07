import pandas as pd
from models import Paper, NodeFeat, Citation, db  # 导入您的模型类

def import_papers(papers_df):
    print("开始导入paper，预计所有导入需要10分钟")
    for _, row in papers_df.iterrows():
        paper = Paper(title=row['title'], abstract=row['abstract'], category=row['category'], year=row['year'])
        db.session.add(paper)
    db.session.commit()  # 提交操作
    print("成功导入paper")

def import_node_feats(node_feat_df):
    print("开始导入feat")
    for _, row in node_feat_df.iterrows():
        features = {f'feature_{i}': row[f'feature_{i}'] for i in range(1, 129)}  # 假设您有 feature_1 到 feature_128 列
        node_feat = NodeFeat(**features)
        db.session.add(node_feat)
    db.session.commit()  # 提交操作
    print("成功导入feat")

def import_citations(citations_df):
    print("开始导入edge")
    for _, row in citations_df.iterrows():
        citation = Citation(citing_paper_id=row['citing_paper_id'], cited_paper_id=row['cited_paper_id'])
        db.session.add(citation)
    db.session.commit()  # 提交操作
    print("成功导入edge")

def import_data():
    # 读取数据
    papers_df = pd.read_csv(r'data/papers.csv')
    node_feat_df = pd.read_csv(r'data/feats.csv')
    citations_df = pd.read_csv(r'data/edge.csv')

    # 调用具体的导入函数
    # import_papers(papers_df)
    import_node_feats(node_feat_df)
    import_citations(citations_df)

    # print("所有数据已成功导入！")

if __name__ == '__main__':
    import_data()