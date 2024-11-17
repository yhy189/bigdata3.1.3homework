import pandas as pd
from models import Paper, NodeFeat, Citation, db  # 导入您的模型类
def clear_database():
    """清空旧数据"""
    db.session.query(Citation).delete()
    db.session.query(NodeFeat).delete()
    db.session.query(Paper).delete()
    db.session.commit()
    print("已清空旧数据")

def import_papers(papers_df):
    print("开始导入paper，预计所有导入需要10分钟")
    for _, row in papers_df.iterrows():
        paper =  Paper(
                            title=row['title'],
                            abstract=row['abstract'],
                            category=row['category'],
                            year=row['year'],
                            frequency=row.get('frequency', 0)  # 如果 CSV 文件中没有 frequency 字段，使用默认值 0
                        )

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
    clear_database()
    # 读取数据
    papers_df = pd.read_csv(r'data/papers.csv')
    node_feat_df = pd.read_csv(r'data/feats.csv')
    citations_df = pd.read_csv(r'data/edge.csv')

    # 调用具体的导入函数
    import_papers(papers_df)
    import_node_feats(node_feat_df)
    import_citations(citations_df)

    # print("所有数据已成功导入！")

if __name__ == '__main__':
    import_data()
# import pandas as pd
# from models import Paper, NodeFeat, Citation, db
#
#
# def clear_database():
#     """清空旧数据"""
#     db.session.query(Citation).delete()
#     db.session.query(NodeFeat).delete()
#     db.session.query(Paper).delete()
#     db.session.commit()
#     print("已清空旧数据")
#
#
# def import_papers(file_path, batch_size=10000):
#     """导入论文信息，忽略格式错误的行"""
#     print("开始批量导入论文")
#     for chunk in pd.read_csv(file_path, chunksize=batch_size, error_bad_lines=False, quoting=3, encoding='utf-8'):
#         papers = [
#             Paper(
#                 title=row['title'],
#                 abstract=row['abstract'],
#                 category=row['category'],
#                 year=row['year'],
#                 frequency=row.get('frequency', 0)  # 如果 CSV 文件中没有 frequency 字段，使用默认值 0
#             )
#             for _, row in chunk.iterrows()
#         ]
#         db.session.bulk_save_objects(papers)
#         db.session.commit()
#     print("成功导入论文")
#
#
# def import_node_feats(file_path, batch_size=10000):
#     """导入节点特征"""
#     print("开始批量导入节点特征")
#     for chunk in pd.read_csv(file_path, chunksize=batch_size):
#         node_feats = [
#             NodeFeat(**{f'feature_{i}': row.get(f'feature_{i}', 0.0) for i in range(1, 129)})
#             for _, row in chunk.iterrows()
#         ]
#         db.session.bulk_save_objects(node_feats)
#         db.session.commit()
#     print("成功导入节点特征")
#
#
# def import_citations(file_path, batch_size=10000):
#     """导入引用关系"""
#     print("开始批量导入引用关系")
#     for chunk in pd.read_csv(file_path, chunksize=batch_size):
#         citations = [
#             Citation(
#                 citing_paper_id=row['citing_paper_id'],
#                 cited_paper_id=row['cited_paper_id']
#             )
#             for _, row in chunk.iterrows()
#         ]
#         db.session.bulk_save_objects(citations)
#         db.session.commit()
#     print("成功导入引用关系")
#
#
# def import_data():
#     """主导入函数"""
#     clear_database()
#
#     # 文件路径
#     papers_path = 'data/papers.csv'
#     node_feats_path = 'data/feats.csv'
#     citations_path = 'data/edge.csv'
#
#     # 调用批量导入函数
#     import_papers(papers_path)
#     import_node_feats(node_feats_path)
#     import_citations(citations_path)
#
#     print("所有数据导入完成！")
#
#
# if __name__ == '__main__':
#     import_data()
