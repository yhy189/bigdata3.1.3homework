from flask import Blueprint, request, jsonify, render_template
import pandas as pd

# 创建蓝图
paper_routes = Blueprint('paper_routes', __name__)

# 加载论文数据
papers_df = pd.read_csv('data/papers.csv')

# 论文检索页面
@paper_routes.route('/search', methods=['GET'])
def search():
    # 获取查询参数
    keyword = request.args.get('keyword', '').strip()

    # 如果没有关键词，返回空的论文列表
    if keyword:
        filtered_papers = papers_df[papers_df['title'].str.contains(keyword, case=False, na=False)]
    else:
        filtered_papers = pd.DataFrame()  # 如果没有关键词，则返回一个空的 DataFrame

    # 将筛选后的论文数据转换为字典列表，供前端模板使用
    papers = filtered_papers.to_dict(orient='records')

    # 渲染模板并传递 `papers` 数据
    return render_template('search_results.html', papers=papers)

# 论文搜索建议
@paper_routes.route('/search_suggestions', methods=['GET'])
def search_suggestions():
    keyword = request.args.get('keyword', '').lower()

    # 如果没有输入关键词，返回空建议
    if len(keyword) == 0:
        return jsonify([])

    # 筛选匹配标题的论文
    filtered_papers = papers_df[papers_df['title'].str.contains(keyword, case=False, na=False)]

    # 返回匹配的论文列表
    suggestions = [{"id": row['id'], "title": row['title']} for _, row in filtered_papers.iterrows()]
    return jsonify(suggestions)
